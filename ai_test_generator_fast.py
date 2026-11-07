import http.server
import socketserver
import json
import os
import random
import requests
from urllib.parse import parse_qs
import time

PORT = 8000

# ========== НАСТРОЙКИ ==========
# РЕЖИМ 1: БЫСТРЫЙ (без ИИ) - РАБОТАЕТ ВСЕГДА
# РЕЖИМ 2: ИИ (нужен API ключ)

USE_AI = False  # Поставьте True если настроили API ключ
AI_PROVIDER = "deepseek"  # "openai", "deepseek", "gemini"

# Глобальные переменные для быстрого доступа
bloom_info_cache = {
    "L1": {"name": "Знание", "criteria": "1 балл за правильное определение"},
    "L2": {"name": "Понимание", "criteria": "2 балла за полное объяснение"},
    "L3": {"name": "Применение", "criteria": "3 балла за правильное применение"},
    "L4": {"name": "Анализ", "criteria": "4 балла за глубокий анализ"},
    "L5": {"name": "Синтез", "criteria": "5 баллов за творческий синтез"},
    "L6": {"name": "Оценка", "criteria": "6 баллов за критическую оценку"}
}

class Fast_Test_Generator(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "mode": "fast" if not USE_AI else "ai",
                "timestamp": time.time()
            }).encode())
            return
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        if self.path == '/api/generate_ai':
            start_time = time.time()
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            try:
                # СУПЕР БЫСТРАЯ ГЕНЕРАЦИЯ
                tasks = self.generate_ultra_fast(data)
                elapsed = time.time() - start_time
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    "success": True,
                    "tasks": tasks,
                    "ai_used": False,
                    "bloom_distribution": self.calculate_bloom_distribution(tasks),
                    "generation_time": f"{elapsed:.2f} сек",
                    "message": f"✅ Тест из {len(tasks)} вопросов сгенерирован за {elapsed:.2f} секунд!"
                }
                
                self.wfile.write(json.dumps(response).encode())
                print(f"⚡ Запрос обработан за {elapsed:.2f} секунд")
                
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ Ошибка: {e}")
                
                # Экстренный фоллбэк
                tasks = self.emergency_fallback(data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.wfile.write(json.dumps({
                    "success": True,
                    "tasks": tasks,
                    "ai_used": False,
                    "generation_time": f"{elapsed:.2f} сек",
                    "message": "⚠️ Использован аварийный режим генерации"
                }).encode())
    
    def generate_ultra_fast(self, data):
        """УЛЬТРА-БЫСТРАЯ генерация теста"""
        topic = data.get("topic", "").strip() or "Общая тема"
        subject = data.get("subject", "informatics")
        grade = data.get("grade", "5-7")
        difficulty = data.get("difficulty", "intermediate")
        count = int(data.get("count", 5))
        
        print(f"⚡ Быстрая генерация: {topic} ({count} вопросов)")
        
        # Шаблоны вопросов
        question_templates = [
            "Что такое {topic} в контексте {subject}?",
            "Основная характеристика {topic}?",
            "Для чего используется {topic} в {grade} классе?",
            "Какое утверждение о {topic} верно?",
            "Пример применения {topic} на практике?",
            "Отличительная особенность {topic}?",
            "С чем связано понятие {topic}?",
            "Что НЕ относится к {topic}?",
            "Последовательность действий при работе с {topic}?",
            "Основная функция {topic}?"
        ]
        
        # Шаблоны ответов
        correct_options = [
            "Правильное определение термина",
            "Верная характеристика явления",
            "Корректное применение на практике",
            "Общепринятая точка зрения",
            "Научно доказанный факт"
        ]
        
        incorrect_options = [
            "Распространенное заблуждение",
            "Неточная формулировка",
            "Устаревшая информация",
            "Ошибочное предположение",
            "Нерелевантный факт"
        ]
        
        tasks = []
        bloom_levels = ["L1", "L2", "L3"]
        
        for i in range(count):
            # Выбираем шаблон вопроса
            template_idx = i % len(question_templates)
            question = question_templates[template_idx].format(
                topic=topic, subject=subject, grade=grade
            )
            
            # Выбираем уровень Bloom
            bloom_level = bloom_levels[i % len(bloom_levels)]
            bloom = bloom_info_cache[bloom_level]
            
            # Генерируем 4 варианта ответа
            letters = ['а', 'б', 'в', 'г']
            correct_letter = random.choice(['A', 'B', 'C', 'D'])
            correct_index = ord(correct_letter) - 65
            
            options = []
            for j in range(4):
                if j == correct_index:
                    correct_text = random.choice(correct_options)
                    options.append(f"{letters[j]}) {correct_text}")
                else:
                    incorrect_text = random.choice(incorrect_options)
                    options.append(f"{letters[j]}) {incorrect_text}")
            
            tasks.append({
                "id": i + 1,
                "question": question,
                "type": "test",
                "options": options,
                "correctAnswer": correct_letter,
                "correctAnswerText": options[correct_index],
                "explanation": f"✅ Ответ {correct_letter} правильный, так как соответствует определению или характеристике {topic}.",
                "descriptor": f"Ученик демонстрирует {bloom['name'].lower()} по теме '{topic}'",
                "criteria": bloom['criteria'],
                "level": bloom['name'],
                "bloom_level": bloom_level,
                "subject": subject,
                "topic": topic
            })
        
        return tasks
    
    def emergency_fallback(self, data):
        """Аварийная генерация при критической ошибке"""
        topic = data.get("topic", "тема")
        count = min(int(data.get("count", 5)), 10)
        
        tasks = []
        for i in range(count):
            tasks.append({
                "id": i + 1,
                "question": f"Вопрос {i+1}: Что вы знаете о '{topic}'?",
                "type": "test",
                "options": [
                    "а) Это важная тема для изучения",
                    "б) Это сложная концепция",
                    "в) Это базовое понятие",
                    "г) Это практический навык"
                ],
                "correctAnswer": "A",
                "correctAnswerText": "а) Это важная тема для изучения",
                "explanation": "Все варианты могут быть верными в разных контекстах",
                "descriptor": "Базовое понимание темы",
                "criteria": "1 балл за любой ответ",
                "level": "Начальный",
                "bloom_level": "L1",
                "subject": data.get("subject", "general"),
                "topic": topic
            })
        
        return tasks
    
    def calculate_bloom_distribution(self, tasks):
        distribution = {}
        for task in tasks:
            level = task.get("bloom_level", "L1")
            distribution[level] = distribution.get(level, 0) + 1
        return distribution

# ========== ЗАПУСК СЕРВЕРА ==========
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("⚡ МГНОВЕННЫЙ ГЕНЕРАТОР ТЕСТОВ")
print("=" * 60)
print(f"🌐 Сервер запущен: http://localhost:{PORT}")
print(f"🚀 Режим: {'ИИ (требуется ключ)' if USE_AI else 'БЫСТРЫЙ (без ИИ)'}")
print("🎯 Генерация тестов за < 0.5 секунды!")
print("=" * 60)
print("✅ Готов к работе!")
print("📁 index.html должен быть в той же папке")
print("🛑 Ctrl+C для остановки")
print("=" * 60)

try:
    with socketserver.TCPServer(("", PORT), Fast_Test_Generator) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n🛑 Сервер остановлен")
except Exception as e:
    print(f"❌ Ошибка сервера: {e}")