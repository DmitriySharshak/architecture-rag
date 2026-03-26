import os
import json
import logging
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImprovedRAGBot:
    """Улучшенный RAG-бот с корректной работой Few-shot и CoT"""
    
    def __init__(self,
                 chroma_db_path: str = "../chroma_db",
                 embedding_model_name: str = "all-MiniLM-L6-v2",
                 collection_name: str = "knowledge_base",
                 use_local_llm: bool = True,
                 llm_model: str = "llama3.2:1b"):
        
        logger.info("Инициализация улучшенного RAG-бота...")
        
        # Загрузка модели эмбеддингов
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        # Загрузка ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.chroma_client.get_collection(collection_name)
        
        # Настройки
        self.use_local_llm = use_local_llm
        self.llm_model = llm_model
        self.n_results = 5
        self.similarity_threshold = 0.3
        
        logger.info(f"✅ Загружено {self.collection.count()} векторов")
    
    def search(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Поиск в базе знаний"""
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Фильтрация и форматирование
        filtered_docs = []
        filtered_metadatas = []
        filtered_distances = []
        
        for doc, metadata, distance in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            similarity = 1 - distance
            if similarity >= self.similarity_threshold:
                filtered_docs.append(doc)
                filtered_metadatas.append(metadata)
                filtered_distances.append(distance)
        
        return {
            'documents': filtered_docs,
            'metadatas': filtered_metadatas,
            'distances': filtered_distances
        }
    
    def format_context(self, search_results: Dict[str, Any]) -> str:
        """Форматирование контекста для промпта"""
        if not search_results['documents']:
            return "Нет релевантной информации."
        
        context_parts = []
        for i, (doc, metadata, distance) in enumerate(zip(
            search_results['documents'],
            search_results['metadatas'],
            search_results['distances']
        ), 1):
            similarity = 1 - distance
            title = metadata.get('title', metadata.get('file_name', 'Unknown'))
            context_parts.append(
                f"=== Документ {i}: {title} (релевантность: {similarity:.1%}) ===\n"
                f"{doc}\n"
            )
        
        return "\n".join(context_parts)
    
    def get_few_shot_examples(self) -> str:
        """Получение примеров для Few-shot из реальной базы"""
        return """Пример 1:
Вопрос: Кто такой Kaelen Vex?
Ответ: Kaelen Vex - легендарный герой, который начинал как фермер на планете Dusthal. Он обучался у Masters Eldrin Thorne и Zephyr Nox, чтобы стать Aether Sentinel. Kaelen Vex использовал Phantom Blade - сначала синий, а затем сконструировал свой собственный зеленый клинок. Он известен тем, что уничтожил Void Core и помог своему отцу Xarn Velgor искупить свою вину.

Пример 2:
Вопрос: Что такое Void Core?
Ответ: Void Core - это боевая станция размером с луну, построенная Imperium of Eternal Dominion. Она была вооружена суперлазером, способным уничтожать целые планеты. Главное слабое место Void Core - тепловой выхлопной порт, ведущий к главному реактору. Именно в этот порт Kaelen Vex выпустил протонные торпеды, что привело к уничтожению станции.
"""
    
    def create_prompt(self, query: str, context: str) -> str:
        """Создание промпта с Few-shot и CoT"""
        prompt = f"""Ты - русскоязычный ассистент. ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ.
        #prompt = fТы - ассистент компании QuantumForge Software, отвечающий на вопросы на основе базы знаний.

ВАЖНЫЕ ПРАВИЛА:
1. Используй ТОЛЬКО информацию из предоставленного контекста
2. Отвечай ТОЛЬКО на русском языке
3. Если информация отсутствует в контексте - честно скажи "Информация не найдена"
4. Всегда указывай источник информации (название документа)

{self.get_few_shot_examples()}

Теперь ответь на следующий вопрос, используя Chain-of-Thought (цепочку рассуждений):

КОНТЕКСТ ИЗ БАЗЫ ЗНАНИЙ:
{context}

ВОПРОС: {query}

ОТВЕТ (сначала напиши свою цепочку рассуждений в формате "Шаг 1: ... Шаг 2: ...", затем дай финальный ответ):"""
        
        return prompt
    
    def answer(self, query: str) -> Dict[str, Any]:
        """Основной метод для ответа на вопрос"""
        start_time = time.time()
        
        # Поиск
        logger.info(f"Поиск: {query}")
        search_results = self.search(query)
        
        # Если ничего не найдено
        if not search_results['documents']:
            return {
                "query": query,
                "answer": "Извините, я не нашел информации по вашему вопросу в базе знаний.",
                "sources": [],
                "time": time.time() - start_time
            }
        
        # Форматирование контекста
        context = self.format_context(search_results)
        
        # Создание промпта
        prompt = self.create_prompt(query, context)
        
        # Генерация ответа через LLM
        if self.use_local_llm:
            answer = self.call_ollama(prompt)
        else:
            answer = self.generate_fallback_answer(query, search_results)
        
        # Подготовка источников
        sources = []
        for metadata, distance in zip(search_results['metadatas'][:3], search_results['distances'][:3]):
            sources.append({
                "title": metadata.get('title', 'Unknown'),
                "similarity": 1 - distance
            })
        
        return {
            "query": query,
            "answer": answer,
            "sources": sources,
            "time": time.time() - start_time
        }
    
    def call_ollama(self, prompt: str) -> str:
        """Вызов Ollama API"""
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Низкая температура для более точных ответов
                        "num_predict": 500,
                        "top_k": 40,
                        "top_p": 0.9
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "Не удалось сгенерировать ответ")
            else:
                return f"Ошибка LLM: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Ошибка Ollama: {e}")
            return f"Ошибка генерации: {str(e)}"
    
    def generate_fallback_answer(self, query: str, search_results: Dict[str, Any]) -> str:
        """Запасной вариант ответа без LLM"""
        answer = f"По запросу '{query}' найдены следующие документы:\n\n"
        for i, (doc, metadata) in enumerate(zip(search_results['documents'][:3], search_results['metadatas'][:3]), 1):
            title = metadata.get('title', 'Unknown')
            answer += f"{i}. {title}\n   {doc[:200]}...\n\n"
        return answer


class ConsoleInterface:
    """Консольный интерфейс"""
    
    def __init__(self):
        self.bot = ImprovedRAGBot()
    
    def run(self):
        print("\n" + "="*60)
        print("🤖 УЛУЧШЕННЫЙ RAG-БОТ QUANTUMFORGE SOFTWARE 🤖")
        print("="*60)
        print("\nТехники промптинга:")
        print("  ✅ Few-shot (примеры из базы знаний)")
        print("  ✅ Chain-of-Thought (цепочка рассуждений)")
        print("\nКоманды:")
        print("  /help - справка")
        print("  /exit - выход")
        print("="*60)
        
        while True:
            try:
                query = input("\n👤 Вы: ").strip()
                
                if not query:
                    continue
                
                if query.lower() == "/exit":
                    print("\n👋 До свидания!")
                    break
                
                if query.lower() == "/help":
                    self.show_help()
                    continue
                
                print("\n🤔 Думаю...")
                result = self.bot.answer(query)
                
                print("\n🤖 Бот:")
                print("-"*60)
                print(result['answer'])
                print("-"*60)
                
                if result['sources']:
                    print("\n📚 Источники:")
                    for source in result['sources']:
                        print(f"  • {source['title']} (схожесть: {source['similarity']:.1%})")
                
                print(f"\n⏱️ Время: {result['time']:.1f} сек")
                
            except KeyboardInterrupt:
                print("\n\n👋 До свидания!")
                break
            except Exception as e:
                print(f"\n❌ Ошибка: {e}")
    
    def show_help(self):
        print("\n📖 СПРАВКА:")
        print("Примеры вопросов:")
        print("  • Кто такой Kaelen Vex?")
        print("  • Что такое Void Core?")
        print("  • Расскажи о планете Dusthal")
        print("  • Что такое Phantom Blade?")
        print("  • Кто такие Aether Sentinels?")


if __name__ == "__main__":
    interface = ConsoleInterface()
    interface.run()