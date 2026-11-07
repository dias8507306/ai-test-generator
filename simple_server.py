import http.server
import socketserver
import json
import os
import random
from urllib.parse import parse_qs

PORT = 8000

# База знаний для разных предметов и тем
KNOWLEDGE_BASE = {
    "informatics": {
        "алгоритмы": [
            {
                "bloom_level": "L1",
                "question": "Алгоритм — это:",
                "correct": "Конечная последовательность шагов для решения задачи",
                "wrong": ["Программа на языке Python", "Код, который всегда работает быстро", "Математическая формула", "Графический интерфейс", "Тип данных", "Системная команда"]
            },
            {
                "bloom_level": "L2", 
                "question": "В чем заключается основное отличие алгоритма от программы?",
                "correct": "Алгоритм - это план решения, программа - его реализация",
                "wrong": ["Алгоритм написан на русском, программа - на английском", "Алгоритм для компьютера, программа - для человека", "Программа сложнее алгоритма", "Это одно и то же", "Алгоритм быстрее выполняется", "Программа не имеет структуры"]
            },
            {
                "bloom_level": "L3",
                "question": "Какой алгоритм сортировки имеет сложность O(n²)?",
                "correct": "Сортировка пузырьком",
                "wrong": ["Быстрая сортировка", "Сортировка слиянием", "Сортировка подсчетом", "Пирамидальная сортировка", "Сортировка выбором", "Сортировка вставками"]
            },
            {
                "bloom_level": "L4",
                "question": "Проанализируйте эффективность алгоритма быстрой сортировки:",
                "correct": "В среднем O(n log n), в худшем O(n²), требует дополнительную память",
                "wrong": ["Всегда O(n log n), не требует памяти", "Всегда O(n²), быстрый на практике", "O(1) по памяти, медленный", "Лучший для отсортированных данных", "Не использует рекурсию", "Работает только с числами"]
            }
        ],
        "программирование": [
            {
                "bloom_level": "L1",
                "question": "Что такое переменная в программировании?",
                "correct": "Именованная область памяти для хранения данных",
                "wrong": ["Математическое уравнение", "Функция без параметров", "Тип цикла", "Способ вывода текста", "Оператор условия", "Библиотека"]
            },
            {
                "bloom_level": "L2",
                "question": "Объясните принцип работы цикла for:",
                "correct": "Выполняет блок кода заданное количество раз",
                "wrong": ["Выполняется бесконечно", "Работает только с массивами", "Используется для условий", "Выполняется один раз всегда", "Только для ввода данных", "Для создания функций"]
            }
        ]
    },
    "mathematics": {
        "дроби": [
            {
                "bloom_level": "L1",
                "question": "Что такое дробь?",
                "correct": "Число, представляющее часть целого",
                "wrong": ["Целое число", "Отрицательное число", "Десятичная запись", "Корень уравнения", "Степень числа", "Логарифм"]
            },
            {
                "bloom_level": "L3",
                "question": "Как сложить дроби 1/4 и 1/2?",
                "correct": "3/4",
                "wrong": ["1/6", "2/6", "1/8", "2/4", "1/3", "3/8"]
            }
        ],
        "геометрия": [
            {
                "bloom_level": "L1",
                "question": "Что такое прямоугольный треугольник?",
                "correct": "Треугольник с одним углом 90 градусов",
                "wrong": ["Треугольник с равными сторонами", "Треугольник без прямых углов", "Треугольник с тупым углом", "Треугольник в круге", "Треугольник с двумя прямыми углами", "Треугольник в квадрате"]
            }
        ]
    },
    "physics": {
        "механика": [
            {
                "bloom_level": "L1",
                "question": "Что такое сила?",
                "correct": "Векторная величина, мера взаимодействия тел",
                "wrong": ["Скалярная величина", "Единица расстояния", "Вид энергии", "Температурный показатель", "Единица времени", "Математическая константа"]
            }
        ]
    }
}

# Уровни Bloom с описаниями
BLOOM_LEVELS = {
    "L1": {"name": "Знание", "criteria": "1 балл за правильное определение"},
    "L2": {"name": "Понимание", "criteria": "2 балла за полное объяснение"},
    "L3": {"name": "Применение", "criteria": "3 балла за правильное применение"},
    "L4": {"name": "Анализ", "criteria": "4 балла за глубокий анализ"},
    "L5": {"name": "Синтез", "criteria": "5 баллов за творческий синтез"},
    "L6": {"name": "Оценка", "criteria": "6 баллов за критическую оценку"}
}

class TestGeneratorHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        if self.path == '/api/generate_ai':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Генерация теста
            tasks = self.generate_test(data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "tasks": tasks,
                "ai_used": False,
                "bloom_distribution": self.calculate_bloom_distribution(tasks),
                "message": "Тест успешно сгенерирован"
            }).encode())
    
    def generate_test(self, data):
        """Генерация теста с разными вопросами и правильными ответами"""
        topic = data.get("topic", "").lower().strip()
        subject = data.get("subject", "informatics")
        grade = data.get("grade", "5-7")
        difficulty = data.get("difficulty", "intermediate")
        count = int(data.get("count", 5))
        
        print(f"\n🔧 Генерация теста:")
        print(f"📚 Тема: {topic}")
        print(f"🎓 Предмет: {subject}")
        print(f"📊 Количество вопросов: {count}")
        
        # Определяем уровни Bloom для сложности
        bloom_levels = self.get_bloom_levels_for_difficulty(difficulty)
        
        # Получаем вопросы из базы знаний
        questions_pool = self.get_questions_pool(subject, topic, bloom_levels)
        
        # Если мало вопросов в базе, добавляем сгенерированные
        if len(questions_pool) < count:
            questions_pool.extend(self.generate_additional_questions(topic, subject, count - len(questions_pool), bloom_levels))
        
        # Выбираем случайные вопросы
        selected_questions = random.sample(questions_pool, min(count, len(questions_pool)))
        
        # Создаем задачи
        tasks = []
        for i, q_data in enumerate(selected_questions):
            task = self.create_task(q_data, i + 1, topic, subject)
            tasks.append(task)
        
        return tasks
    
    def get_questions_pool(self, subject, topic, bloom_levels):
        """Получаем вопросы из базы знаний"""
        pool = []
        
        # Ищем по точному совпадению темы
        if subject in KNOWLEDGE_BASE and topic in KNOWLEDGE_BASE[subject]:
            for question in KNOWLEDGE_BASE[subject][topic]:
                if question["bloom_level"] in bloom_levels:
                    pool.append(question)
        
        # Если мало вопросов, ищем по частичному совпадению
        if len(pool) < 5:
            if subject in KNOWLEDGE_BASE:
                for subject_topic, questions in KNOWLEDGE_BASE[subject].items():
                    if subject_topic in topic or topic in subject_topic:
                        for question in questions:
                            if question["bloom_level"] in bloom_levels:
                                pool.append(question)
        
        return pool
    
    def generate_additional_questions(self, topic, subject, count, bloom_levels):
        """Генерируем дополнительные вопросы если их мало в базе"""
        questions = []
        
        question_templates = {
            "L1": [
                f"Что такое '{topic}'?",
                f"Основное определение '{topic}' это:",
                f"Ключевая характеристика '{topic}' это:"
            ],
            "L2": [
                f"Объясните принцип работы '{topic}':",
                f"В чем суть '{topic}'?",
                f"Как работает '{topic}'?"
            ],
            "L3": [
                f"Как применить '{topic}' на практике?",
                f"Пример использования '{topic}':",
                f"Где применяется '{topic}'?"
            ],
            "L4": [
                f"Проанализируйте преимущества и недостатки '{topic}':",
                f"Сравните '{topic}' с аналогичными подходами:",
                f"Каковы ограничения '{topic}'?"
            ]
        }
        
        correct_answers = {
            "L1": [
                f"Это основной элемент {subject}",
                f"Фундаментальное понятие в области {subject}",
                f"Базовый принцип {subject}"
            ],
            "L2": [
                f"Работает на основе определенных правил",
                f"Основан на принципах {subject}",
                f"Имеет четкий алгоритм работы"
            ],
            "L3": [
                f"Используется для решения практических задач",
                f"Применяется в различных областях",
                f"Эффективен для конкретных ситуаций"
            ],
            "L4": [
                f"Имеет свои преимущества и ограничения",
                f"Эффективен в определенных условиях",
                f"Требует анализа перед применением"
            ]
        }
        
        wrong_answers = [
            "Не имеет практического применения",
            "Работает только в теории",
            "Устаревший подход",
            "Слишком сложен для понимания",
            "Требует специального оборудования",
            "Не документирован",
            "Работает только онлайн",
            "Нужны специальные разрешения",
            "Дорог в реализации",
            "Медленный по сравнению с аналогами"
        ]
        
        for i in range(count):
            bloom_level = random.choice(bloom_levels)
            
            if bloom_level in question_templates:
                question = random.choice(question_templates[bloom_level])
                correct = random.choice(correct_answers.get(bloom_level, ["Правильный ответ"]))
                
                # Выбираем 3 случайных неправильных ответа
                wrong_sample = random.sample(wrong_answers, 3)
                
                questions.append({
                    "bloom_level": bloom_level,
                    "question": question,
                    "correct": correct,
                    "wrong": wrong_sample
                })
        
        return questions
    
    def create_task(self, q_data, number, topic, subject):
        """Создает задачу с РАЗНЫМ расположением правильного ответа"""
        # Собираем все варианты ответов
        all_options = [q_data["correct"]] + q_data["wrong"][:3]  # Берем 3 неправильных
        
        # Случайно перемешиваем варианты
        random.shuffle(all_options)
        
        # Находим индекс правильного ответа после перемешивания
        correct_index = all_options.index(q_data["correct"])
        
        # Преобразуем в формат а), б), в), г)
        formatted_options = []
        letters = ["а", "б", "в", "г"]
        for i, option in enumerate(all_options[:4]):  # Берем только первые 4
            formatted_options.append(f"{letters[i]}) {option}")
        
        # Английская буква для правильного ответа
        correct_letter = chr(65 + correct_index)  # A, B, C, D
        
        # Дескриптор и критерии
        bloom_info = BLOOM_LEVELS.get(q_data["bloom_level"], {"name": "Средний", "criteria": "1 балл"})
        
        return {
            "id": number,
            "question": q_data["question"],
            "type": "test",
            "options": formatted_options,
            "correctAnswer": correct_letter,
            "correctAnswerText": formatted_options[correct_index],
            "explanation": f"Правильный ответ: {formatted_options[correct_index]}. Это уровень {q_data['bloom_level']} ({bloom_info['name']}) по Bloom таксономии.",
            "descriptor": f"Ученик демонстрирует {bloom_info['name'].lower()} по теме '{topic}'",
            "criteria": bloom_info["criteria"],
            "level": bloom_info["name"],
            "bloom_level": q_data["bloom_level"],
            "subject": subject,
            "topic": topic
        }
    
    def get_bloom_levels_for_difficulty(self, difficulty):
        """Возвращает уровни Bloom для сложности"""
        if difficulty == "beginner":
            return ["L1", "L2"]
        elif difficulty == "advanced":
            return ["L4", "L5", "L6"]
        else:  # intermediate
            return ["L2", "L3", "L4"]
    
    def calculate_bloom_distribution(self, tasks):
        """Рассчитывает распределение по уровням Bloom"""
        distribution = {}
        for task in tasks:
            level = task.get("bloom_level", "L3")
            distribution[level] = distribution.get(level, 0) + 1
        return distribution

# Запуск сервера
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🤖 УМНЫЙ ТЕСТ ГЕНЕРАТОР")
print("=" * 60)
print(f"🌐 Сервер запущен: http://localhost:{PORT}")
print("📚 База знаний: Информатика, Математика, Физика")
print("🎯 Особенности:")
print("  • Разные вопросы каждый раз")
print("  • Правильные ответы в случайных местах (A, B, C, D)")
print("  • Уровни Bloom таксономии")
print("  • Качественные варианты ответов")
print("=" * 60)
print("🚀 Сервер готов к работе!")
print("🛑 Нажми Ctrl+C для остановки")
print("=" * 60)

try:
    with socketserver.TCPServer(("", PORT), TestGeneratorHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n🛑 Сервер остановлен")
except Exception as e:
    print(f"❌ Ошибка: {e}")