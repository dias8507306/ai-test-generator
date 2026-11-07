import http.server
import socketserver
import json
import os
import random
import requests
from urllib.parse import parse_qs

PORT = 8000

# ========== НАСТРОЙКИ ИИ ==========
# ВЫБЕРИ ОДИН ИЗ ВАРИАНТОВ:

#ВАРИАНТ 1: OpenAI (самый качественный)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")  # platform.openai.com, set in env / .env
API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-3.5-turbo"

# ВАРИАНТ 2: DeepSeek (бесплатный альтернатива)
#DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")  # platform.deepseek.com
#API_URL = "https://api.deepseek.com/v1/chat/completions"
#MODEL = "deepseek-chat"

# ВАРИАНТ 3: Gemini (Google) - тоже хороший
# GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")  # aistudio.google.com
# API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

class AI_Test_Generator(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        if self.path == '/api/generate_ai':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            try:
                # Генерация теста с помощью ИИ
                tasks = self.generate_with_ai(data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "tasks": tasks,
                    "ai_used": True,
                    "bloom_distribution": self.calculate_bloom_distribution(tasks),
                    "message": "Тест сгенерирован с помощью ИИ"
                }).encode())
                
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                # Fallback на локальную генерацию
                tasks = self.generate_local_fallback(data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "tasks": tasks,
                    "ai_used": False,
                    "bloom_distribution": self.calculate_bloom_distribution(tasks),
                    "message": "ИИ недоступен, использована локальная генерация"
                }).encode())
    
    def generate_with_ai(self, data):
        """Генерация теста с помощью реального ИИ API"""
        topic = data.get("topic", "").strip()
        subject = data.get("subject", "informatics")
        grade = data.get("grade", "5-7")
        difficulty = data.get("difficulty", "intermediate")
        student_level = data.get("student_level", "average")
        count = int(data.get("count", 5))
        
        print(f"\n🤖 ИИ ГЕНЕРАЦИЯ ТЕСТА:")
        print(f"📚 Тема: {topic}")
        print(f"🎓 Предмет: {subject}, Класс: {grade}")
        print(f"⚡ Сложность: {difficulty}, Уровень ученика: {student_level}")
        print(f"📊 Вопросов: {count}")
        
        # Определяем уровни Bloom
        bloom_levels = self.get_bloom_levels_for_difficulty(difficulty)
        
        # Создаем промпт для ИИ
        prompt = self.create_ai_prompt(topic, subject, grade, count, bloom_levels)
        
        # Отправляем запрос к ИИ
        response = self.call_ai_api(prompt)
        
        # Парсим ответ ИИ
        tasks = self.parse_ai_response(response, topic, subject, bloom_levels)
        
        return tasks
    
    def create_ai_prompt(self, topic, subject, grade, count, bloom_levels):
        """Создает промпт для ИИ"""
        
        bloom_descriptions = {
            "L1": "Знание (вспоминание фактов, терминов, определений)",
            "L2": "Понимание (объяснение, интерпретация, перефразирование)",
            "L3": "Применение (использование знаний в новых ситуациях)",
            "L4": "Анализ (разбиение на части, выявление взаимосвязей)",
            "L5": "Синтез (создание нового, комбинирование идей)",
            "L6": "Оценка (суждение, аргументация, защита позиции)"
        }
        
        # Выбираем описания для нужных уровней
        selected_blooms = [bloom_descriptions[lvl] for lvl in bloom_levels if lvl in bloom_descriptions]
        
        prompt = f"""Ты опытный учитель {subject}. Создай тест из {count} вопросов для {grade} класса по теме: "{topic}".

ТРЕБОВАНИЯ:
1. Используй уровни Bloom таксономии: {', '.join(selected_blooms)}
2. Каждый вопрос должен иметь 4 варианта ответа
3. Правильный ответ должен быть в РАЗНЫХ позициях (иногда A, иногда B, C или D)
4. Варианты должны быть реалистичными и содержательными
5. Формат: а) текст, б) текст, в) текст, г) текст

ФОРМАТ ОТВЕТА (строго JSON):
{{
  "questions": [
    {{
      "id": 1,
      "question": "Полный текст вопроса?",
      "options": [
        "а) Вариант A",
        "б) Вариант B", 
        "в) Вариант C",
        "г) Вариант D"
      ],
      "correct_letter": "A",  // или "B", "C", "D" - ВСЕГДА РАЗНЫЕ!
      "bloom_level": "L1",
      "explanation": "Подробное объяснение правильного ответа"
    }}
  ]
}}

ПРИМЕР ВОПРОСА (тема "Фотосинтез", уровень L3):
{{
  "id": 1,
  "question": "Как растения используют солнечный свет в процессе фотосинтеза?",
  "options": [
    "а) Преобразуют его в тепловую энергию",
    "б) Используют для превращения воды и углекислого газа в глюкозу",
    "в) Отражают его для защиты от перегрева",
    "г) Накапливают в специальных клетках"
  ],
  "correct_letter": "B",
  "bloom_level": "L3",
  "explanation": "В процессе фотосинтеза растения используют солнечную энергию для преобразования воды и CO2 в глюкозу и кислород."
}}

Создай РАЗНООБРАЗНЫЕ вопросы по теме "{topic}" ({subject}) для {grade} класса.
Сделай так, чтобы правильные ответы были в разных позициях (не все под буквой A)!"""
        
        return prompt
    
    def call_ai_api(self, prompt):
        """Отправляет запрос к ИИ API"""
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "system", 
                    "content": "Ты опытный педагог. Твоя задача - создавать качественные тесты. Отвечай ТОЛЬКО в JSON формате без лишнего текста."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.8,  # Больше разнообразия
            "max_tokens": 3000
        }
        
        try:
            print("🔄 Отправляю запрос к ИИ...")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                print("✅ ИИ ответил успешно!")
                return response.json()
            else:
                print(f"❌ Ошибка ИИ API: {response.status_code}")
                print(f"Ответ: {response.text}")
                raise Exception(f"API ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ ИИ недоступен: {e}")
            raise
    
    def parse_ai_response(self, ai_response, topic, subject, bloom_levels):
        """Парсит ответ от ИИ"""
        try:
            content = ai_response["choices"][0]["message"]["content"]
            
            # Ищем JSON в ответе
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                tasks = []
                for i, q in enumerate(data.get("questions", [])):
                    
                    # Проверяем наличие всех необходимых полей
                    if all(k in q for k in ['question', 'options', 'correct_letter']):
                        
                        # Форматируем варианты ответов
                        options = []
                        for opt in q['options'][:4]:  # Берем максимум 4 варианта
                            if opt.strip():
                                options.append(opt)
                        
                        # Добираем до 4 вариантов если нужно
                        while len(options) < 4:
                            options.append(f"{chr(1072 + len(options))}) Дополнительный вариант")
                        
                        bloom_level = q.get('bloom_level', random.choice(bloom_levels))
                        bloom_info = self.get_bloom_info(bloom_level)
                        
                        task = {
                            "id": i + 1,
                            "question": q['question'],
                            "type": "test",
                            "options": options,
                            "correctAnswer": q['correct_letter'].upper(),
                            "correctAnswerText": next((opt for opt in options if opt.startswith(f"{q['correct_letter'].lower()})")), options[0]),
                            "explanation": q.get('explanation', f"Правильный ответ: {q['correct_letter']}"),
                            "descriptor": f"Ученик демонстрирует {bloom_info['name'].lower()} по теме '{topic}'",
                            "criteria": bloom_info['criteria'],
                            "level": bloom_info['name'],
                            "bloom_level": bloom_level,
                            "subject": subject,
                            "topic": topic
                        }
                        
                        tasks.append(task)
                
                print(f"🎉 Сгенерировано {len(tasks)} вопросов от ИИ")
                return tasks
            else:
                print("❌ ИИ не вернул JSON")
                raise Exception("Невалидный ответ от ИИ")
                
        except Exception as e:
            print(f"❌ Ошибка парсинга ответа ИИ: {e}")
            raise
    
    def generate_local_fallback(self, data):
        """Локальная генерация если ИИ недоступен"""
        topic = data.get("topic", "").strip()
        subject = data.get("subject", "informatics")
        count = int(data.get("count", 5))
        
        print(f"🔄 Использую локальную генерацию для темы: {topic}")
        
        tasks = []
        for i in range(count):
            # Случайный уровень Bloom
            bloom_levels = ["L1", "L2", "L3", "L4"]
            bloom_level = random.choice(bloom_levels)
            bloom_info = self.get_bloom_info(bloom_level)
            
            # Случайная позиция правильного ответа (A, B, C, D)
            correct_letter = random.choice(['A', 'B', 'C', 'D'])
            correct_index = ord(correct_letter) - 65  # A=0, B=1, C=2, D=3
            
            # Генерируем варианты
            options = []
            letters = ['а', 'б', 'в', 'г']
            
            for j in range(4):
                if j == correct_index:
                    options.append(f"{letters[j]}) Правильный ответ по теме '{topic}'")
                else:
                    options.append(f"{letters[j]}) Неправильный вариант {j+1}")
            
            tasks.append({
                "id": i + 1,
                "question": f"Вопрос {i+1} по теме '{topic}':",
                "type": "test",
                "options": options,
                "correctAnswer": correct_letter,
                "correctAnswerText": options[correct_index],
                "explanation": f"Правильный ответ: {correct_letter}. {topic} - важная тема в {subject}.",
                "descriptor": f"Ученик демонстрирует {bloom_info['name'].lower()} по теме '{topic}'",
                "criteria": bloom_info['criteria'],
                "level": bloom_info['name'],
                "bloom_level": bloom_level,
                "subject": subject,
                "topic": topic
            })
        
        return tasks
    
    def get_bloom_levels_for_difficulty(self, difficulty):
        if difficulty == "beginner":
            return ["L1", "L2"]
        elif difficulty == "advanced":
            return ["L4", "L5", "L6"]
        else:
            return ["L2", "L3", "L4"]
    
    def get_bloom_info(self, level):
        bloom_info = {
            "L1": {"name": "Знание", "criteria": "1 балл за правильное определение"},
            "L2": {"name": "Понимание", "criteria": "2 балла за полное объяснение"},
            "L3": {"name": "Применение", "criteria": "3 балла за правильное применение"},
            "L4": {"name": "Анализ", "criteria": "4 балла за глубокий анализ"},
            "L5": {"name": "Синтез", "criteria": "5 баллов за творческий синтез"},
            "L6": {"name": "Оценка", "criteria": "6 баллов за критическую оценку"}
        }
        return bloom_info.get(level, {"name": "Средний", "criteria": "1 балл"})
    
    def calculate_bloom_distribution(self, tasks):
        distribution = {}
        for task in tasks:
            level = task.get("bloom_level", "L3")
            distribution[level] = distribution.get(level, 0) + 1
        return distribution

# ========== ЗАПУСК СЕРВЕРА ==========
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🚀 РЕАЛЬНЫЙ ИИ ТЕСТ ГЕНЕРАТОР")
print("=" * 70)
print(f"🌐 Сервер запущен: http://localhost:{PORT}")
print(f"🤖 Модель ИИ: {MODEL}")
print("🎯 Особенности:")
print("  • Реальная генерация ИИ по ЛЮБОЙ теме")
print("  • Правильные ответы в разных местах (A, B, C, D)")
print("  • Адаптация под предмет и класс")
print("  • Уровни Bloom таксономии")
print("=" * 70)

if OPENAI_API_KEY and OPENAI_API_KEY != "sk-твой-ключ-openai-тут":
    print("✅ OpenAI API подключен")
else:
    print("⚠️  ВНИМАНИЕ: Установи OpenAI API ключ!")
    print("   Получи на https://platform.openai.com/api-keys")

print("🚀 Сервер готов! Открой http://localhost:8000")
print("🛑 Нажми Ctrl+C для остановки")
print("=" * 70)

try:
    with socketserver.TCPServer(("", PORT), AI_Test_Generator) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n🛑 Сервер остановлен")
except Exception as e:
    print(f"❌ Ошибка: {e}")