"""
ГЕНЕРАТОР ТЕСТОВЫХ ВОПРОСОВ С ЛОКАЛЬНЫМ ИИ
Не требует API ключей и интернета после установки
"""

import requests
import json
import time
import os

class LocalTestGenerator:
    def __init__(self, model_name: str = "llama3.2"):
        """
        Использует локальную модель через Ollama
        """
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/generate"
        
        # Проверяем, запущен ли Ollama
        self.check_ollama()
        
        # Уровни сложности
        self.levels = {
            "1-4": "простые вопросы, конкретные примеры",
            "5-7": "базовые понятия с объяснениями", 
            "8-9": "вопросы на понимание и анализ",
            "10-11": "сложные задачи, требующие решения"
        }
    
    def check_ollama(self):
        """Проверка, что Ollama запущен"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                print("✅ Ollama запущен, модели доступны")
                return True
        except:
            print("""
❌ ОШИБКА: Ollama не запущен!

ШАГИ ДЛЯ ИСПРАВЛЕНИЯ:
1. Нажмите Пуск → Найти "Ollama" → Запустить
2. Или в командной строке напишите: ollama run llama3.2
3. Подождите, пока загрузится модель
4. Запустите программу снова
            """)
            return False
    
    def generate_with_ollama(self, prompt: str) -> str:
        """Генерация текста через локальную модель"""
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 500
            }
        }
        
        try:
            response = requests.post(self.api_url, json=data, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                print(f"Ошибка Ollama: {response.status_code}")
                return ""
        except Exception as e:
            print(f"Ошибка подключения к Ollama: {e}")
            return ""
    
    def generate_question(self, subject: str, topic: str, grade: str) -> dict:
        """Создание одного вопроса"""
        
        # Определяем уровень
        grade_num = int(''.join(filter(str.isdigit, grade)) or '5')
        if grade_num <= 4:
            level = "1-4"
        elif grade_num <= 7:
            level = "5-7"
        elif grade_num <= 9:
            level = "8-9"
        else:
            level = "10-11"
        
        prompt = f"""
        Ты - учитель. Создай один тестовый вопрос для школьника.
        
        ПРЕДМЕТ: {subject}
        ТЕМА: {topic}
        КЛАСС: {grade} (уровень: {self.levels[level]})
        
        ФОРМАТ ОТВЕТА ТОЛЬКО В JSON:
        {{
            "question": "текст вопроса",
            "options": ["вариант А", "вариант Б", "вариант В", "вариант Г"],
            "correct": "номер правильного варианта (1-4)",
            "explanation": "краткое объяснение"
        }}
        
        Вопрос должен соответствовать уровню {grade} класса.
        Верни ТОЛЬКО JSON объект, без других слов.
        """
        
        print("🤖 Локальный ИИ генерирует вопрос...")
        response = self.generate_with_ollama(prompt)
        
        if response:
            try:
                # Ищем JSON в ответе
                start = response.find('{')
                end = response.rfind('}') + 1
                
                if start != -1 and end != 0:
                    json_str = response[start:end]
                    question_data = json.loads(json_str)
                    
                    # Добавляем информацию об уровне
                    question_data["grade"] = grade
                    question_data["level"] = level
                    
                    return question_data
                else:
                    # Если не нашли JSON, создаем структурированный вопрос
                    return self.create_fallback_question(subject, topic, grade, response)
                    
            except json.JSONDecodeError:
                print("⚠️ ИИ вернул не JSON, использую стандартный вопрос")
                return self.create_fallback_question(subject, topic, grade, response)
        
        return None
    
    def create_fallback_question(self, subject, topic, grade, ai_response):
        """Создание вопроса, если ИИ не вернул JSON"""
        return {
            "question": f"По предмету {subject} на тему '{topic}': {ai_response[:100]}...",
            "options": ["Вариант А", "Вариант Б", "Вариант В", "Вариант Г"],
            "correct": "1",
            "explanation": "Ответ сгенерирован ИИ",
            "grade": grade,
            "source": "локальная модель ИИ"
        }
    
    def generate_test(self, subject, topic, grade, num_questions=3):
        """Создание полного теста"""
        
        print(f"\n{'='*60}")
        print(f"🎓 СОЗДАНИЕ ТЕСТА (локальный ИИ)")
        print(f"{'='*60}")
        print(f"📚 Предмет: {subject}")
        print(f"📖 Тема: {topic}")
        print(f"🏫 Класс: {grade}")
        print(f"❓ Вопросов: {num_questions}")
        print(f"{'='*60}")
        
        questions = []
        
        for i in range(num_questions):
            print(f"\n📝 Вопрос {i+1}/{num_questions}...")
            question = self.generate_question(subject, topic, grade)
            
            if question:
                question["number"] = i + 1
                questions.append(question)
                
                # Выводим вопрос
                print(f"✅ Создан: {question['question'][:80]}...")
                
                # Пауза между запросами
                time.sleep(1)
            else:
                print(f"⚠️ Не удалось создать вопрос {i+1}")
        
        # Формируем тест
        test_data = {
            "test_info": {
                "subject": subject,
                "topic": topic,
                "grade": grade,
                "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model": self.model_name
            },
            "questions": questions
        }
        
        return test_data
    
    def save_test(self, test_data):
        """Сохранение теста"""
        filename = f"тест_{test_data['test_info']['subject']}_{test_data['test_info']['grade']}кл.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"ТЕСТ: {test_data['test_info']['subject']}\n")
            f.write(f"Тема: {test_data['test_info']['topic']}\n")
            f.write(f"Класс: {test_data['test_info']['grade']}\n")
            f.write("="*50 + "\n\n")
            
            for q in test_data["questions"]:
                f.write(f"{q['number']}. {q['question']}\n\n")
                
                if "options" in q:
                    f.write("Варианты ответов:\n")
                    for j, opt in enumerate(q["options"], 1):
                        f.write(f"  {j}) {opt}\n")
                
                f.write(f"\n✅ Правильный ответ: {q.get('correct', 'не указан')}\n")
                
                if "explanation" in q:
                    f.write(f"💡 Объяснение: {q['explanation']}\n")
                
                f.write("-"*50 + "\n\n")
        
        print(f"\n💾 Тест сохранен: {filename}")
        print(f"📂 Путь: {os.path.abspath(filename)}")

def main():
    """Основная функция"""
    
    print("🎓 ГЕНЕРАТОР ТЕСТОВ С ЛОКАЛЬНЫМ ИИ")
    print("="*60)
    print("🌟 Преимущества:")
    print("• Не требует API ключей")
    print("• Работает без интернета")
    print("• Бесплатно и без ограничений")
    print("="*60)
    
    # Запрос данных
    print("\n📝 ВВЕДИТЕ ДАННЫЕ:")
    subject = input("Предмет: ").strip() or "Математика"
    topic = input("Тема: ").strip() or "Дроби"
    grade = input("Класс (1-11): ").strip() or "7"
    
    try:
        num = int(input("Количество вопросов (1-10): ").strip() or "3")
        num = max(1, min(num, 10))
    except:
        num = 3
    
    # Создаем генератор
    generator = LocalTestGenerator()
    
    # Проверяем, что Ollama работает
    if not generator.check_ollama():
        input("Нажмите Enter после запуска Ollama...")
        if not generator.check_ollama():
            print("❌ Не удалось подключиться к Ollama")
            return
    
    # Генерируем тест
    test = generator.generate_test(subject, topic, grade, num)
    
    if test["questions"]:
        # Показываем результат
        print(f"\n{'='*60}")
        print("✅ ТЕСТ СОЗДАН!")
        print(f"{'='*60}")
        
        for q in test["questions"]:
            print(f"\n{q['number']}. {q['question']}")
            
            if "options" in q:
                print("   Варианты:")
                for j, opt in enumerate(q["options"], 1):
                    print(f"   {j}) {opt}")
            
            print(f"   ✅ Ответ: {q.get('correct', 'не указан')}")
            
            if "explanation" in q:
                print(f"   💡 {q['explanation']}")
        
        # Сохраняем
        save = input("\n💾 Сохранить в файл? (да/нет): ").lower()
        if save in ['да', 'д', 'yes', 'y']:
            generator.save_test(test)
    
    print(f"\n🎉 Готово! Тест создан локальным ИИ.")

if __name__ == "__main__":
    main()