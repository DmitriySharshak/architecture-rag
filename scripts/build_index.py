import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VectorIndexBuilder:
    """Класс для создания векторного индекса базы знаний"""
    
    def __init__(self, 
                 knowledge_base_path: str = "../knowledge_base",
                 chroma_db_path: str = "../chroma_db",
                 embedding_model_name: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 500,
                 chunk_overlap: int = 100):
        
        self.knowledge_base_path = Path(knowledge_base_path)
        self.chroma_db_path = Path(chroma_db_path)
        
        # Инициализация модели эмбеддингов
        logger.info(f"Загрузка модели эмбеддингов: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        logger.info(f"Размер эмбеддингов: {self.embedding_dim}")
        
        # Инициализация сплиттера для текста
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Инициализация ChromaDB клиента
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Создание или получение коллекции
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"ChromaDB коллекция создана: knowledge_base")
        
    def load_documents(self) -> List[Dict[str, Any]]:
        """Загрузка документов из папки knowledge_base"""
        documents = []
        
        # Загружаем словарь замен для метаданных
        terms_map_path = self.knowledge_base_path / "terms_map.json"
        if terms_map_path.exists():
            with open(terms_map_path, 'r', encoding='utf-8') as f:
                terms_map = json.load(f)
        else:
            terms_map = {}
        
        # Чтение всех текстовых файлов
        for file_path in self.knowledge_base_path.glob("*.txt"):
            if file_path.name == "terms_map.json":
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Извлекаем заголовок из первого абзаца
                lines = content.strip().split('\n')
                title = lines[0].replace('#', '').strip() if lines else file_path.stem
                
                documents.append({
                    "id": file_path.stem,
                    "title": title,
                    "content": content,
                    "file_name": file_path.name,
                    "file_path": str(file_path)
                })
                
                logger.info(f"Загружен документ: {file_path.name}")
                
            except Exception as e:
                logger.error(f"Ошибка загрузки {file_path}: {e}")
        
        logger.info(f"Всего загружено документов: {len(documents)}")
        return documents
    
    def split_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Разбивка документов на чанки"""
        chunks = []
        
        for doc in documents:
            # Разбиваем текст на чанки
            split_texts = self.text_splitter.split_text(doc["content"])
            
            for i, chunk_text in enumerate(split_texts):
                chunk_id = f"{doc['id']}_chunk_{i}"
                
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "source_doc_id": doc["id"],
                        "title": doc["title"],
                        "file_name": doc["file_name"],
                        "file_path": doc["file_path"],
                        "chunk_index": i,
                        "total_chunks": len(split_texts)
                    }
                })
            
            logger.info(f"Документ '{doc['title']}' разбит на {len(split_texts)} чанков")
        
        logger.info(f"Всего создано чанков: {len(chunks)}")
        return chunks
    
    def generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[List[float]]:
        """Генерация эмбеддингов для всех чанков"""
        texts = [chunk["text"] for chunk in chunks]
        
        logger.info(f"Начало генерации эмбеддингов для {len(texts)} текстов...")
        start_time = time.time()
        
        # Генерация эмбеддингов батчами для эффективности
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = self.embedding_model.encode(batch_texts, show_progress_bar=False)
            all_embeddings.extend(batch_embeddings.tolist())
            
            if (i + batch_size) % 100 == 0:
                logger.info(f"Обработано {i + len(batch_texts)} из {len(texts)} чанков")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Генерация эмбеддингов завершена за {elapsed_time:.2f} секунд")
        
        return all_embeddings
    
    def create_index(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Создание индекса в ChromaDB"""
        logger.info("Создание индекса в ChromaDB...")
        start_time = time.time()
        
        # Подготовка данных для вставки
        ids = [chunk["id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Добавление данных в коллекцию
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Индекс создан за {elapsed_time:.2f} секунд")
        logger.info(f"Всего векторов в индексе: {self.collection.count()}")
    
    def save_statistics(self, chunks_count: int, embedding_time: float, index_time: float):
        """Сохранение статистики создания индекса"""
        stats = {
            "total_chunks": chunks_count,
            "embedding_model": self.embedding_model.model_card_data.model_name,
            "embedding_dimension": self.embedding_dim,
            "chunk_size": 500,
            "chunk_overlap": 100,
            "embedding_generation_time_seconds": embedding_time,
            "index_creation_time_seconds": index_time,
            "total_time_seconds": embedding_time + index_time,
            "vector_db": "ChromaDB",
            "documents_count": len(list(self.knowledge_base_path.glob("*.txt"))) - 1  # исключая terms_map
        }
        
        stats_path = self.chroma_db_path / "index_stats.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Статистика сохранена в {stats_path}")
    
    def build(self):
        """Основной метод для построения индекса"""
        logger.info("="*50)
        logger.info("Начало построения векторного индекса")
        logger.info("="*50)
        
        # Шаг 1: Загрузка документов
        documents = self.load_documents()
        
        # Шаг 2: Разбивка на чанки
        chunks = self.split_documents(documents)
        
        # Шаг 3: Генерация эмбеддингов
        embedding_start = time.time()
        embeddings = self.generate_embeddings(chunks)
        embedding_time = time.time() - embedding_start
        
        # Шаг 4: Создание индекса
        index_start = time.time()
        self.create_index(chunks, embeddings)
        index_time = time.time() - index_start
        
        # Шаг 5: Сохранение статистики
        self.save_statistics(len(chunks), embedding_time, index_time)
        
        logger.info("="*50)
        logger.info("Построение индекса успешно завершено!")
        logger.info(f"Всего чанков: {len(chunks)}")
        logger.info(f"Размер эмбеддингов: {self.embedding_dim}")
        logger.info(f"Время генерации эмбеддингов: {embedding_time:.2f} сек")
        logger.info(f"Время создания индекса: {index_time:.2f} сек")
        logger.info("="*50)
        
        return self.collection

def test_query(collection, query_text: str, n_results: int = 3):
    """Тестовый запрос к индексу"""
    from sentence_transformers import SentenceTransformer
    
    # Загружаем ту же модель для генерации эмбеддинга запроса
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Генерируем эмбеддинг запроса
    query_embedding = model.encode([query_text])[0].tolist()
    
    # Поиск в коллекции
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    return results

if __name__ == "__main__":
    # Создание индекса
    builder = VectorIndexBuilder(
        knowledge_base_path="../knowledge_base",
        chroma_db_path="../chroma_db",
        chunk_size=500,
        chunk_overlap=100
    )
    
    collection = builder.build()
    
    # Тестирование с несколькими запросами
    print("\n" + "="*50)
    print("ТЕСТИРОВАНИЕ ПОИСКА")
    print("="*50)
    
    test_queries = [
        "Кто такой Kaelen Vex?",
        "Расскажи о планете Dusthal",
    ]
    
    for query in test_queries:
        print(f"\nЗапрос: {query}")
        print("-" * 50)
        
        results = test_query(collection, query, n_results=2)
        
        if results['documents'][0]:
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0], 
                results['metadatas'][0],
                results['distances'][0]
            )):
                print(f"\nРезультат {i+1} (расстояние: {distance:.4f}):")
                print(f"Источник: {metadata['title']}")
                print(f"Фрагмент: {doc[:200]}...")
        else:
            print("Ничего не найдено")