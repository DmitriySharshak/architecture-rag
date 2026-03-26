## Шаг 1. Подготовка данных
Перейти в каталог scripts и запустить скрипт
```
python init.py
```
## Шаг 2. Создание векторного индекса
Выполнить следующие команды 
активировать пространство
```
.venv\Scripts\activate.bat

```

Установить необходимые библиотеки и проверить установку
```
pip install chromadb sentence-transformers langchain-text-splitters
python -c "import chromadb; print(chromadb.__version__)"
python build_index.py
```

Перейти в каталог scripts и запустить скрипт создания векторного индекса
```
python build_index.py
```

Результаты выполнения:
|   |     |
| --| ----| 
|Модель|all-MiniLM-L6-v2|
|База знаний|knowledge_base|
|Всего чанков|35|
|Размер эмбеддингов|384|
|Время генерации эмбеддингов|0.37 сек|
|Время создания индекса|0.06 сек|

Примеры запросов
Запрос 1: "Кто такой Kaelen Vex и какое оружие он использовал?"
Kaelen Vex was a farm boy who became a legendary hero. He discovered his connection to the Force through
training with Aether Lord Eldrin Thorne and later with Aether Lord...

Запрос 2: Расскажи о планете Dusthal
Dusthal is a desert planet orbiting binary stars. Covered in vast sand dunes and rocky wastes, it was home to
moisture farmers, criminals, and slaves. The planet's two suns ma...



