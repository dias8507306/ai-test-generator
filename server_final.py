import http.server
import socketserver
import json
import os
from urllib.parse import parse_qs
import requests
import logging

# ==================== КОНФИГУРАЦИЯ ====================
logging.getLogger().setLevel(logging.ERROR)
PORT = 8000

# ⚠️ ⚠️ ⚠️ ВСТАВЬ СВОЙ OPENAI API КЛЮЧ ЗДЕСЬ ⚠️ ⚠️ ⚠️
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")  # set in env / .env (see .env.example)
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-3.5-turbo"  # или "gpt-4", "gpt-4-turbo-preview"

# Создаем папку для данных
if not os.path.exists('data'):
    os.makedirs('data')

USERS_FILE = 'data/users.json'
TASKS_FILE = 'data/tasks.json'

# Инициализация файлов
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({"users": []}, f)

if not os.path.exists(TASKS_FILE):
    with open(TASKS_FILE, 'w') as f:
        json.dump({"tasks": []}, f)

# ==================== ОСНОВНОЙ КЛАСС ====================
class AIHandler(http.server.SimpleHTTPRequestHandler):
    
    # Убираем метод log_message для чистоты логов
    
    # ==================== ОБРАБОТЧИКИ ====================
    def do_GET(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        if self.path == '/':
            self.path = '/index.html'
        elif self.path.startswith('/api/'):
            self.handle_api()
            return
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        if self.path.startswith('/api/'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                self.handle_api_post(data)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_api(self):
        if self.path == '/api/users':
            self.send_users()
        elif self.path == '/api/tasks':
            self.send_tasks()
        else:
            self.send_error(404, "API endpoint not found")
    
    def handle_api_post(self, data):
        if self.path == '/api/register':
            self.register_user(data)
        elif self.path == '/api/login':
            self.login_user(data)
        elif self.path == '/api/save_task':
            self.save_task(data)
        elif self.path == '/api/generate_ai':
            self.generate_with_openai_ai(data)  # РЕАЛЬНЫЙ ИИ через OpenAI
        elif self.path == '/api/analyze_errors':
            self.analyze_errors(data)
        elif self.path == '/api/generate':
            self.generate_local_tasks(data)  # Локальная генерация
        else:
            self.send_error(404, "API endpoint not found")
    
    # ==================== OPENAI AI ====================
    def generate_with_openai_ai(self, data):
        """Реальная генерация с OpenAI AI"""
        try:
            topic = data.get("topic", "").strip()
            subject = data.get("subject", "informatics")
            grade = data.get("grade", "5-7")
            task_type = data.get("type", "test")
            difficulty = data.get("difficulty", "intermediate")
            student_level = data.get("student_level", "average")
            count = int(data.get("count", 5))
            
            if not topic:
                self.send_error(400, "Тема не может быть пустой")
                return
            
            print(f"\n{'='*50}")
            print(f"🧠 OPENAI AI: Генерация теста")
            print(f"📚 Тема: {topic}")
            print(f"🎓 Класс: {grade}, Сложность: {difficulty}")
            print(f"📊 Вопросов: {count}, Уровень ученика: {student_level}")
            print(f"{'='*50}")
            
            # Определяем уровни Bloom в зависимости от сложности
            bloom_levels = self.get_bloom_levels_for_difficulty(difficulty)
            bloom_names = self.get_bloom_names()
            
            # Создаем промпт для OpenAI в НУЖНОМ формате
            prompt = self.create_openai_prompt_proper_format(topic, subject, grade, count, bloom_levels, task_type)
            
            # Отправляем запрос к OpenAI
            try:
                if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-tvoi-openai-api-key-тут":
                    print("⚠️  ВНИМАНИЕ: Установи OpenAI API ключ в коде!")
                    print("   Получи ключ на https://platform.openai.com/api-keys")
                    raise Exception("OpenAI API ключ не установлен")
                
                headers = {
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": OPENAI_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": """Ты опытный педагог и эксперт по созданию образовательных тестов. 
Создавай тесты с использованием Bloom Таксономии. Всегда отвечай в JSON формате.

ВАЖНЫЕ ПРАВИЛА ФОРМАТА:
1. Каждый вопрос должен быть сформулирован как полноценное предложение
2. Варианты ответов должны начинаться с маленькой буквы (а), б), в), г))
3. Только один вариант правильный
4. Правильный вариант должен быть реалистичным и содержательным
5. Неправильные варианты должны быть правдоподобными, но неверными
6. Правильный ответ должен быть под буквой 'а' (первый вариант)
"""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"}
                }
                
                print("🔄 Отправка запроса к OpenAI API...")
                response = requests.post(
                    OPENAI_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    ai_data = response.json()
                    ai_content = ai_data["choices"][0]["message"]["content"]
                    print("✅ Получен ответ от OpenAI API")
                    
                    # Парсим JSON ответ
                    try:
                        result = json.loads(ai_content)
                        tasks = result.get("tasks", [])
                        
                        # Форматируем задачи для нашего приложения
                        formatted_tasks = []
                        for i, task in enumerate(tasks[:count]):
                            # Проверяем обязательные поля
                            if all(k in task for k in ['question', 'options', 'correct_index']):
                                bloom_level = task.get('bloom_level', 'L3')
                                
                                # ОБРАБОТКА ОПЦИЙ - ФОРМАТ а), б), в), г)
                                options = []
                                for j, opt in enumerate(task['options']):
                                    # Добавляем букву к варианту, если её нет
                                    letter = chr(1072 + j)  # русская 'а'
                                    if not opt.strip().startswith(f'{letter})'):
                                        options.append(f"{letter}) {opt}")
                                    else:
                                        options.append(opt)
                                
                                formatted_tasks.append({
                                    "id": i + 1,
                                    "question": task['question'],
                                    "type": task_type,
                                    "options": options[:4],  # Берем максимум 4 варианта
                                    "correctAnswer": chr(65 + task['correct_index']),  # A, B, C, D
                                    "correctAnswerText": options[task['correct_index']] if task['correct_index'] < len(options) else options[0],
                                    "explanation": task.get('explanation', ''),
                                    "descriptor": task.get('descriptor', f"Ученик демонстрирует знания по теме '{topic}'"),
                                    "criteria": task.get('criteria', "1 балл за правильный ответ"),
                                    "level": bloom_names.get(bloom_level, "Средний"),
                                    "bloom_level": bloom_level,
                                    "subject": subject,
                                    "topic": topic
                                })
                        
                        if formatted_tasks:
                            # Сохраняем
                            self.save_ai_tasks(topic, formatted_tasks)
                            
                            # Рассчитываем распределение Bloom
                            bloom_distribution = {}
                            for task in formatted_tasks:
                                level = task.get("bloom_level", "L3")
                                bloom_distribution[level] = bloom_distribution.get(level, 0) + 1
                            
                            # Отправляем
                            self.send_json_response(200, {
                                "success": True,
                                "tasks": formatted_tasks,
                                "ai_used": True,
                                "model": OPENAI_MODEL,
                                "bloom_distribution": bloom_distribution,
                                "message": f"Сгенерировано с помощью OpenAI ({OPENAI_MODEL})"
                            })
                            print(f"🎉 УСПЕХ: Сгенерировано {len(formatted_tasks)} вопросов!")
                            print(f"📊 Bloom распределение: {bloom_distribution}")
                            return
                        else:
                            print("⚠️ OpenAI вернул невалидные данные")
                            print(f"Содержимое: {result}")
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ Ошибка парсинга JSON от OpenAI: {e}")
                        print(f"Сырой ответ: {ai_content[:500]}...")
                    
                else:
                    print(f"❌ Ошибка OpenAI API: {response.status_code}")
                    print(f"Ответ: {response.text}")
                
            except requests.exceptions.Timeout:
                print("⏰ Таймаут запроса к OpenAI API")
            except Exception as e:
                print(f"❌ Ошибка AI: {e}")
            
            # Если что-то пошло не так - УЛУЧШЕННАЯ локальная генерация
            print("⚠️ OpenAI не сработал, использую улучшенную локальную генерацию")
            self.generate_enhanced_local_tasks(data)
            
        except Exception as e:
            print(f"❌ Общая ошибка: {e}")
            self.generate_enhanced_local_tasks(data)
    
    def create_openai_prompt_proper_format(self, topic, subject, grade, count, bloom_levels, task_type):
        """Создает промпт для OpenAI в ПРАВИЛЬНОМ формате"""
        bloom_descriptions = {
            "L1": "Знание (вспоминание фактов)",
            "L2": "Понимание (объяснение идей)",
            "L3": "Применение (использование знаний)",
            "L4": "Анализ (разбиение информации)",
            "L5": "Синтез (создание нового)",
            "L6": "Оценка (суждение и аргументация)"
        }
        
        bloom_levels_text = ", ".join([f"{level} ({bloom_descriptions[level]})" for level in bloom_levels])
        
        prompt = f"""Создай {count} тестовых вопросов по теме "{topic}" для предмета "{subject}" ({grade} класс).

ОЧЕНЬ ВАЖНЫЕ ТРЕБОВАНИЯ ПО ФОРМАТУ:
1. Вопрос должен быть ПОЛНЫМ ПРЕДЛОЖЕНИЕМ с вопросительным знаком в конце
2. Варианты ответов должны быть в формате: а) текст, б) текст, в) текст, г) текст
3. Правильный ответ ВСЕГДА должен быть под буквой 'а' (первый вариант)
4. Неправильные варианты должны быть ПРАВДОПОДОБНЫМИ, но неверными
5. Каждый вариант должен начинаться с маленькой буквы

ТРЕБОВАНИЯ К СОДЕРЖАНИЮ:
1. Тип вопросов: {task_type}
2. Используй уровни Bloom таксономии: {bloom_levels_text}
3. Распредели вопросы равномерно по выбранным уровням
4. Только один вариант ответа правильный

ФОРМАТ ОТВЕТА (JSON):
{{
  "tasks": [
    {{
      "question": "Полный текст вопроса?",
      "options": [
        "а) Правильный ответ (реалистичный и содержательный)",
        "б) Неправильный, но правдоподобный ответ",
        "в) Еще один неправильный вариант",
        "г) Неправильный вариант, связанный с темой"
      ],
      "correct_index": 0,
      "explanation": "Подробное объяснение почему этот ответ правильный",
      "bloom_level": "L1",
      "descriptor": "Что должен уметь ученик для правильного ответа",
      "criteria": "Критерии оценки (например, '1 балл за правильный ответ')"
    }}
  ]
}}

ПРИМЕРЫ ПРАВИЛЬНОГО ФОРМАТА:

1. ПРАВИЛЬНЫЙ пример:
{{
  "question": "Алгоритм — это:",
  "options": [
    "а) Конечная последовательность шагов для решения задачи",
    "б) Программа на языке Python",
    "в) Код, который всегда работает быстро",
    "г) Математическая формула"
  ],
  "correct_index": 0,
  "explanation": "Алгоритм - это точная последовательность шагов для решения задачи.",
  "bloom_level": "L1",
  "descriptor": "Ученик определяет понятие алгоритма",
  "criteria": "1 балл за правильный ответ"
}}

2. ПРАВИЛЬНЫЙ пример:
{{
  "question": "Проанализируйте эффективность алгоритма сортировки пузырьком:",
  "options": [
    "а) Сложность O(n²), неэффективен для больших данных, прост в реализации",
    "б) Сложность O(log n), самый эффективный алгоритм",
    "в) Не требует дополнительной памяти",
    "г) Всегда работает быстрее быстрой сортировки"
  ],
  "correct_index": 0,
  "explanation": "Сортировка пузырьком имеет квадратичную сложность, что делает её неэффективной для больших данных.",
  "bloom_level": "L4",
  "descriptor": "Ученик анализирует характеристики алгоритма",
  "criteria": "3 балла за полный анализ"
}}

НЕПРАВИЛЬНЫЙ формат (так НЕ делать):
- Вопрос: "Что такое алгоритм?"
- Варианты: ["А) Это программа", "B) Это последовательность", ...]

Создай {count} разнообразных и качественных вопросов по теме "{topic}"!
Каждый вопрос должен быть уникальным и соответствовать своему уровню Bloom."""
        
        return prompt
    
    def generate_enhanced_local_tasks(self, data):
        """Улучшенная локальная генерация в ПРАВИЛЬНОМ формате"""
        print("⚠️ Использую улучшенную локальную генерацию (правильный формат)")
        
        topic = data.get("topic", "Алгоритмы")
        subject = data.get("subject", "informatics")
        grade = data.get("grade", "5-7")
        task_type = data.get("type", "test")
        difficulty = data.get("difficulty", "intermediate")
        count = int(data.get("count", 5))
        
        # Определяем уровни Bloom
        bloom_levels = self.get_bloom_levels_for_difficulty(difficulty)
        bloom_names = self.get_bloom_names()
        
        # Генерация задач в ПРАВИЛЬНОМ формате
        tasks = []
        
        for i in range(count):
            # Выбираем уровень Bloom
            bloom_level = bloom_levels[i % len(bloom_levels)] if bloom_levels else "L3"
            
            # Генерируем вопрос в зависимости от уровня Bloom
            question_data = self.generate_proper_question(topic, bloom_level, i)
            
            # Создаем дескриптор и критерии
            descriptor = self.generate_descriptor(bloom_level, topic, subject)
            criteria = self.generate_criteria(bloom_level)
            
            # Создаем задачу в ПРАВИЛЬНОМ формате
            task = {
                "id": i + 1,
                "question": question_data["question"],
                "type": task_type,
                "options": question_data["options"],
                "correctAnswer": "A",  # Всегда A, так как правильный ответ первый
                "correctAnswerText": question_data["options"][0],
                "explanation": question_data["explanation"],
                "descriptor": descriptor,
                "criteria": criteria,
                "level": bloom_names.get(bloom_level, "Средний"),
                "bloom_level": bloom_level,
                "subject": subject,
                "topic": topic
            }
            
            tasks.append(task)
        
        # Рассчитываем распределение Bloom
        bloom_distribution = {}
        for task in tasks:
            level = task.get("bloom_level", "L3")
            bloom_distribution[level] = bloom_distribution.get(level, 0) + 1
        
        # Отправляем ответ
        self.send_json_response(200, {
            "success": True,
            "tasks": tasks,
            "ai_used": False,
            "bloom_distribution": bloom_distribution,
            "message": "Сгенерировано локально в правильном формате"
        })
    
    def generate_proper_question(self, topic, bloom_level, index):
        """Генерирует вопрос в ПРАВИЛЬНОМ формате а), б), в), г)"""
        
        # База знаний для разных уровней Bloom
        questions_db = {
            "L1": {
                "questions": [
                    f"Что такое '{topic}'?",
                    f"Основное определение '{topic}' это:",
                    f"Ключевая характеристика '{topic}' это:",
                    f"Главная цель использования '{topic}' это:"
                ],
                "correct_answers": [
                    f"а) Последовательность четких шагов для решения задачи",
                    f"а) Метод систематического решения проблемы",
                    f"а) Способ организации данных или процессов",
                    f"а) Автоматизация повторяющихся операций"
                ],
                "wrong_answers": [
                    f"б) Случайный набор инструкций",
                    f"б) Язык программирования",
                    f"в) Тип данных в компьютерной памяти",
                    f"г) Математическая теорема"
                ]
            },
            "L2": {
                "questions": [
                    f"Как объяснить принцип работы '{topic}'?",
                    f"В чем заключается суть '{topic}'?",
                    f"Каков основной механизм действия '{topic}'?",
                    f"Как можно описать процесс '{topic}'?"
                ],
                "correct_answers": [
                    f"а) Последовательное выполнение шагов для достижения цели",
                    f"а) Преобразование входных данных в выходные по определенным правилам",
                    f"а) Систематическое применение правил к данным",
                    f"а) Циклическое или последовательное выполнение операций"
                ],
                "wrong_answers": [
                    f"б) Произвольное изменение информации",
                    f"б) Хранение данных в памяти",
                    f"в) Случайный выбор из вариантов",
                    f"г) Визуальное представление данных"
                ]
            },
            "L3": {
                "questions": [
                    f"Как применить '{topic}' для решения практической задачи?",
                    f"Каким образом использовать '{topic}' в реальной ситуации?",
                    f"Как решить задачу с помощью '{topic}'?",
                    f"В какой ситуации следует применять '{topic}'?"
                ],
                "correct_answers": [
                    f"а) Определить шаги и последовательно их выполнить",
                    f"а) Проанализировать задачу и выбрать подходящий метод",
                    f"а) Разбить проблему на подзадачи и решать по порядку",
                    f"а) Когда требуется системный подход к решению"
                ],
                "wrong_answers": [
                    f"б) Действовать случайным образом",
                    f"б) Использовать только интуицию",
                    f"в) Применять без понимания принципов",
                    f"г) Когда задача очень простая и очевидная"
                ]
            },
            "L4": {
                "questions": [
                    f"Проанализируйте эффективность '{topic}':",
                    f"Сравните '{topic}' с другими подходами:",
                    f"Каковы преимущества и недостатки '{topic}'?",
                    f"Как оценить результативность применения '{topic}'?"
                ],
                "correct_answers": [
                    f"а) Имеет свои сильные и слабые стороны в зависимости от контекста",
                    f"а) Эффективен в определенных условиях, но не во всех",
                    f"а) Прост в реализации, но может быть неоптимальным",
                    f"а) Зависит от размера данных и требований к скорости"
                ],
                "wrong_answers": [
                    f"б) Всегда самый лучший метод",
                    f"б) Не имеет недостатков",
                    f"в) Абсолютно неэффективен",
                    f"г) Не зависит от условий применения"
                ]
            },
            "L5": {
                "questions": [
                    f"Как можно улучшить '{topic}'?",
                    f"Предложите модификацию '{topic}' для конкретной задачи:",
                    f"Создайте новый подход на основе '{topic}':",
                    f"Как адаптировать '{topic}' под новые требования?"
                ],
                "correct_answers": [
                    f"а) Добавить оптимизацию для обработки больших данных",
                    f"а) Комбинировать с другими методами для повышения эффективности",
                    f"а) Разработать гибридный подход",
                    f"а) Внести изменения в соответствии с новыми условиями"
                ],
                "wrong_answers": [
                    f"б) Полностью отказаться от подхода",
                    f"б) Усложнить без улучшения эффективности",
                    f"в) Применить без изменений в любой ситуации",
                    f"г) Заменить на совершенно другой метод"
                ]
            },
            "L6": {
                "questions": [
                    f"Оцените значимость '{topic}' в современном мире:",
                    f"Критически проанализируйте применение '{topic}':",
                    f"Каково влияние '{topic}' на развитие технологий?",
                    f"Аргументируйте необходимость изучения '{topic}':"
                ],
                "correct_answers": [
                    f"а) Имеет фундаментальное значение для понимания процессов",
                    f"а) Критически важен для эффективного решения проблем",
                    f"а) Лежит в основе многих современных технологий",
                    f"а) Развивает системное и алгоритмическое мышление"
                ],
                "wrong_answers": [
                    f"б) Не имеет практического значения",
                    f"б) Устаревший подход, не нужный в современном мире",
                    f"в) Важен только для теоретиков",
                    f"г) Можно обойтись без понимания этого подхода"
                ]
            }
        }
        
        # Берем данные для текущего уровня Bloom
        level_data = questions_db.get(bloom_level, questions_db["L3"])
        questions = level_data["questions"]
        correct_answers = level_data["correct_answers"]
        wrong_answers = level_data["wrong_answers"]
        
        # Выбираем вопрос и ответ
        question_idx = index % len(questions)
        
        # Создаем варианты ответов в формате а), б), в), г)
        options = [
            correct_answers[question_idx % len(correct_answers)],
            f"б) {wrong_answers[(question_idx * 2) % len(wrong_answers)]}",
            f"в) {wrong_answers[(question_idx * 3 + 1) % len(wrong_answers)]}",
            f"г) {wrong_answers[(question_idx * 4 + 2) % len(wrong_answers)]}"
        ]
        
        # Убираем дублирование "а)" если уже есть
        if options[0].startswith("а) "):
            # Уже в правильном формате
            pass
        elif options[0].startswith("а)"):
            # Нет пробела после скобки
            options[0] = "а) " + options[0][3:]
        else:
            # Нет "а)" вообще
            options[0] = "а) " + options[0]
        
        return {
            "question": questions[question_idx],
            "options": options,
            "explanation": f"Это вопрос уровня {bloom_level} (Bloom таксономия) по теме '{topic}'. " +
                          f"Правильный ответ: {options[0][3:]}"
        }
    
    def get_bloom_levels_for_difficulty(self, difficulty):
        """Возвращает уровни Bloom для заданной сложности"""
        if difficulty == "beginner":
            return ["L1", "L2"]
        elif difficulty == "advanced":
            return ["L4", "L5", "L6"]
        else:  # intermediate
            return ["L2", "L3", "L4"]
    
    def get_bloom_names(self):
        """Возвращает названия уровней Bloom"""
        return {
            "L1": "Знание (начальный)",
            "L2": "Понимание (базовый)",
            "L3": "Применение (средний)",
            "L4": "Анализ (продвинутый)",
            "L5": "Синтез (высокий)",
            "L6": "Оценка (экспертный)"
        }
    
    def generate_descriptor(self, bloom_level, topic, subject):
        """Генерирует дескриптор для уровня Bloom"""
        descriptors = {
            "L1": f"Ученик называет и определяет основные понятия темы '{topic}' по предмету {subject}",
            "L2": f"Ученик объясняет и интерпретирует понятия темы '{topic}' по предмету {subject}",
            "L3": f"Ученик применяет знания темы '{topic}' для решения практических задач по {subject}",
            "L4": f"Ученик анализирует и сравнивает различные аспекты темы '{topic}' по {subject}",
            "L5": f"Ученик создает и синтезирует новые идеи на основе темы '{topic}' по {subject}",
            "L6": f"Ученик оценивает и аргументирует важность темы '{topic}' в контексте {subject}"
        }
        return descriptors.get(bloom_level, f"Ученик демонстрирует знания по теме '{topic}'")
    
    def generate_criteria(self, bloom_level):
        """Генерирует критерии оценки для уровня Bloom"""
        criteria = {
            "L1": "1 балл за правильное определение каждого понятия",
            "L2": "2 балла за полное объяснение и интерпретацию",
            "L3": "3 балла за правильное применение в новой ситуации",
            "L4": "4 балла за глубокий анализ и выявление связей",
            "L5": "5 баллов за творческий синтез и создание нового",
            "L6": "6 баллов за критическую оценку и аргументацию"
        }
        return criteria.get(bloom_level, "Критерии оценивания")
    
    def save_ai_tasks(self, topic, tasks):
        """Сохраняет AI задачи в базу"""
        try:
            with open(TASKS_FILE, 'r') as f:
                data = json.load(f)
            
            new_entry = {
                "id": len(data["tasks"]) + 1,
                "topic": topic,
                "tasks": tasks,
                "source": "openai_ai",
                "model": OPENAI_MODEL,
                "created_at": "2024-12-06"
            }
            
            data["tasks"].append(new_entry)
            
            with open(TASKS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
                
            print(f"💾 Сохранено {len(tasks)} вопросов в базу")
            
        except Exception as e:
            print(f"⚠️ Ошибка сохранения: {e}")
    
    # ==================== АНАЛИЗ ОШИБОК ====================
    def analyze_errors(self, data):
        """Анализирует ошибки ученика по Bloom таксономии"""
        try:
            answers = data.get("answers", {})
            tasks = data.get("tasks", [])
            student_level = data.get("student_level", "average")
            
            # Простой анализ
            total_answers = len(answers)
            correct_answers = sum(1 for answer in answers.values() if answer.get("correct", False))
            
            # Анализ по уровням Bloom
            analysis = {
                "total_answers": total_answers,
                "correct_answers": correct_answers,
                "percentage": (correct_answers / total_answers * 100) if total_answers > 0 else 0,
                "bloom_analysis": {},
                "recommendations": []
            }
            
            # Генерация рекомендаций
            if correct_answers / total_answers < 0.5:
                analysis["recommendations"].append("Требуется повторение базовых понятий")
                analysis["recommendations"].append("Рекомендуется начать с уровня L1 (Знание)")
            elif correct_answers / total_answers < 0.8:
                analysis["recommendations"].append("Улучшите навыки применения знаний (L3)")
                analysis["recommendations"].append("Практикуйтесь в решении практических задач")
            else:
                analysis["recommendations"].append("Отличные результаты! Можно переходить к продвинутым уровням")
            
            self.send_json_response(200, {
                "success": True,
                "analysis": analysis
            })
            
        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
            self.send_json_response(500, {
                "success": False,
                "message": f"Ошибка анализа: {str(e)}"
            })
    
    # ==================== ЛОКАЛЬНАЯ ГЕНЕРАЦИЯ (старая) ====================
    def generate_local_tasks(self, data):
        """Локальная генерация (простой fallback)"""
        print("⚠️ Использую простую локальную генерацию")
        
        topic = data.get("topic", "Алгоритмы")
        count = int(data.get("count", 5))
        
        # Простые вопросы в ПРАВИЛЬНОМ формате
        tasks = []
        for i in range(count):
            tasks.append({
                "id": i + 1,
                "question": f"Что такое '{topic}'?",
                "type": data.get("type", "test"),
                "options": [
                    f"а) Последовательность шагов для решения задачи",
                    f"б) Язык программирования",
                    f"в) Тип данных",
                    f"г) Математическая формула"
                ],
                "correctAnswer": "A",
                "correctAnswerText": "а) Последовательность шагов для решения задачи",
                "explanation": f"Правильный ответ объясняет тему '{topic}'",
                "descriptor": f"Ученик демонстрирует понимание темы '{topic}'",
                "criteria": "1 балл за правильный ответ",
                "level": "Средний",
                "bloom_level": "L3"
            })
        
        # Отправляем ответ
        self.send_json_response(200, {
            "success": True,
            "tasks": tasks,
            "ai_used": False,
            "message": "Сгенерировано локально"
        })
    
    # ==================== БАЗОВЫЕ API МЕТОДЫ ====================
    def register_user(self, data):
        try:
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
            
            for user in users["users"]:
                if user["email"] == data["email"]:
                    self.send_json_response(400, {"success": False, "message": "Пользователь уже существует"})
                    return
            
            new_user = {
                "id": len(users["users"]) + 1,
                "name": data["name"],
                "email": data["email"],
                "password": data["password"],
                "created_at": "2024-12-06"
            }
            
            users["users"].append(new_user)
            
            with open(USERS_FILE, 'w') as f:
                json.dump(users, f, indent=2)
            
            self.send_json_response(200, {
                "success": True,
                "user": {
                    "id": new_user["id"],
                    "name": new_user["name"],
                    "email": new_user["email"]
                }
            })
        except Exception as e:
            self.send_error(500, str(e))
    
    def login_user(self, data):
        try:
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
            
            for user in users["users"]:
                if user["email"] == data["email"] and user["password"] == data["password"]:
                    self.send_json_response(200, {
                        "success": True,
                        "user": {
                            "id": user["id"],
                            "name": user["name"],
                            "email": user["email"]
                        }
                    })
                    return
            
            self.send_json_response(401, {"success": False, "message": "Неверный email или пароль"})
        except Exception as e:
            self.send_error(500, str(e))
    
    def save_task(self, data):
        try:
            with open(TASKS_FILE, 'r') as f:
                tasks_data = json.load(f)
            
            new_task = {
                "id": len(tasks_data["tasks"]) + 1,
                "topic": data["topic"],
                "subject": data["subject"],
                "tasks": data["tasks"],
                "created_at": "2024-12-06"
            }
            
            tasks_data["tasks"].append(new_task)
            
            with open(TASKS_FILE, 'w') as f:
                json.dump(tasks_data, f, indent=2)
            
            self.send_json_response(200, {"success": True, "task_id": new_task["id"]})
        except Exception as e:
            self.send_error(500, str(e))
    
    def send_users(self):
        try:
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
            self.send_json_response(200, users)
        except Exception as e:
            self.send_error(500, str(e))
    
    def send_tasks(self):
        try:
            with open(TASKS_FILE, 'r') as f:
                tasks = json.load(f)
            self.send_json_response(200, tasks)
        except Exception as e:
            self.send_error(500, str(e))
    
    def send_json_response(self, status, data):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

# ==================== ЗАПУСК СЕРВЕРА ====================
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🤖 OPENAI AI ТЕСТ ГЕНЕРАТОР С BLOOM ТАКСОНОМИЕЙ")
print("=" * 60)
print(f"🌐 Сервер запущен: http://localhost:{PORT}")
print(f"📁 Папка: {os.getcwd()}")
print("=" * 60)

# Проверка API ключа
if OPENAI_API_KEY and OPENAI_API_KEY != "sk-tvoi-openai-api-key-тут":
    print(f"🧠 OpenAI API: АКТИВИРОВАН")
    print("🔑 Ключ: задан через переменную окружения OPENAI_API_KEY")
    print(f"🤖 Модель: {OPENAI_MODEL}")
else:
    print("⚠️  ВНИМАНИЕ: OpenAI API ключ не установлен!")
    print("   Получи ключ на https://platform.openai.com/api-keys")
    print("   И вставь его в переменную OPENAI_API_KEY")
print("=" * 60)

print("🚀 Сервер готов к работе!")
print("🛑 Нажми Ctrl+C для остановки")
print("=" * 60)

try:
    with socketserver.TCPServer(("", PORT), AIHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n🛑 Сервер остановлен")
except Exception as e:
    print(f"❌ Ошибка запуска: {e}")