import json
from rag_bot import RAGBot

def run_test_suite():
    """Запуск тестового набора вопросов"""
    
    bot = RAGBot(use_local_llm=True)
    
    test_questions = [
        "Кто такой Kaelen Vex?",
        "Что такое Void Core?",
        "Расскажи о планете Dusthal",
        "Какая организация противостояла Imperium?",
        "Что такое Phantom Blade и кто его использует?",
        "Кто такой Marcus Wellington?"  # Ожидаем "не знаю"
    ]
    
    results = []
    
    print("\n" + "="*80)
    print("ТЕСТИРОВАНИЕ RAG-БОТА")
    print("="*80)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\nТест {i}: {question}")
        print("-"*80)
        
        result = bot.answer_question(question)
        
        print(f"\nОтвет:\n{result['answer'][:300]}...")
        print(f"\nИсточников: {len(result['sources'])}")
        print(f"Время: {result['time_seconds']:.2f} сек")
        
        results.append({
            "test_id": i,
            "question": question,
            "has_sources": len(result['sources']) > 0,
            "time": result['time_seconds']
        })
    
    # Сохранение результатов
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*80)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("="*80)
    for result in results:
        status = "✅" if result['has_sources'] else "❌"
        print(f"{status} Тест {result['test_id']}: {result['question'][:40]}... ({result['time']:.2f} сек)")

if __name__ == "__main__":
    run_test_suite()