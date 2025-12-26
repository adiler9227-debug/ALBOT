import google.generativeai as genai
from config import GEMINI_API_KEY

# Настройка Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Используем Gemini 2.0 Flash (бесплатно 1500 запросов/день)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

async def generate_schedule(schedule_type: str, date: str = None) -> str:
    """
    Генерация расписания через Gemini
    schedule_type: 'day', 'week', 'month'
    """
    
    prompts = {
        'day': f"Создай расписание тренировок на один день ({date}). Включи время, тип тренировки, описание. Формат: красиво оформленный текст для Telegram с эмодзи.",
        'week': f"Создай расписание тренировок на неделю начиная с {date}. Для каждого дня укажи время и тип тренировки. Формат: красиво оформленный текст для Telegram с эмодзи.",
        'month': f"Создай расписание тренировок на месяц начиная с {date}. Распредели разные типы тренировок по неделям. Формат: красиво оформленный текст для Telegram с эмодзи."
    }
    
    prompt = prompts.get(schedule_type, prompts['day'])
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Ошибка генерации: {e}"

async def generate_post(topic: str = None) -> str:
    """
    Генерация поста для канала через Gemini
    """
    
    if topic:
        prompt = f"Создай мотивирующий пост для фитнес-канала на тему: {topic}. Формат: красивый текст с эмодзи для Telegram, 150-250 слов."
    else:
        prompt = "Создай мотивирующий пост для женского фитнес-клуба. Тема - здоровье, красота, спорт. Формат: красивый текст с эмодзи для Telegram, 150-250 слов."
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Ошибка генерации: {e}"

async def analyze_payment_receipt(text: str) -> dict:
    """
    Анализ чека через Gemini
    Извлекает сумму и дату
    """
    
    prompt = f"""
    Проанализируй текст чека и извлеки информацию:
    
    Текст: {text}
    
    Верни ТОЛЬКО JSON в формате:
    {{"amount": число, "date": "ГГГГ-ММ-ДД"}}
    
    Если не можешь определить - верни null для этого поля.
    """
    
    try:
        response = model.generate_content(prompt)
        # Парсим JSON из ответа
        import json
        result = json.loads(response.text.strip())
        return result
    except Exception as e:
        return {"amount": None, "date": None}
