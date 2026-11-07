"""
EDUGEN PRO - ФИНАЛ ВЕРСИЯСЫ (ТОЛЫҚ ЖАНАРТЫЛҒАН: ИСТОРИЯ, BLOOM, ДЕСКРИПТОРЛАР, ЖҮКТЕУ PDF/DOCX)

Өзгерістер:
1. 'letter' айнымалысының UnboundLocalError қатесін болдырмау үшін PDF функциясы дұрысталды.
2. Барлық қажетті HTML шаблондары енгізілді.
"""
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, send_file, abort
import requests
import json
import time
import re
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# --- PDF/DOCX импорттары ---
from reportlab.lib.pagesizes import letter # <--- Міндетті түрде импорттау!
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from io import BytesIO
from docx import Document
from docx.shared import Pt

app = Flask(__name__)
# Құпия кілтті өзгертуді ұмытпаңыз!
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-me')

# --- ҚАРІПТЕРДІ ТІРКЕУ (PDF ҮШІН) ---
try:
    # Ықтимал Arial файлдарының аттары
    # Егер .ttf файлдары болмаса, 'DejaVuSans.ttf' қолдану қажет
    pdfmetrics.registerFont(TTFont('ArialUnicode', 'Arial.ttf'))
    pdfmetrics.registerFont(TTFont('ArialBold', 'Arial_Bold.ttf'))
    FONT_NORMAL = 'ArialUnicode'
    FONT_BOLD = 'ArialBold'
except:
    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
        FONT_NORMAL = 'DejaVuSans'
        FONT_BOLD = 'DejaVuSans-Bold'
    except:
        FONT_NORMAL = 'Helvetica'
        FONT_BOLD = 'Helvetica-Bold'
        print("❌ Қате: Арнайы қаріптер жоқ. Әдепкі Helvetica қолданылуда.")

# --- ГЛОБАЛЬДЫ АЙНЫМАЛЫЛАР ЖӘНЕ СӨЗДІК ---
DICTIONARY = {
    'ru': {
        'title': 'AI Тест Генератор',
        'subtitle': 'Профессиональный генератор тестов с использованием Phi-3 Mini',
        'auth_logout': 'Выйти',
        'auth_login': 'Вход',
        'login_title': 'Вход в систему',
        'register_title': 'Регистрация',
        'label_email': 'Email',
        'label_password': 'Пароль',
        'label_name': 'Имя',
        'btn_login': 'Войти',
        'btn_register': 'Зарегистрироваться',
        'link_no_account': 'Нет аккаунта? Регистрация',
        'link_has_account': 'Уже есть аккаунт? Войти',
        'label_subject': '📚 Предмет',
        'label_grade': '🎓 Класс',
        'label_topic': '💡 Тема урока (Будьте конкретны!)',
        'placeholder_topic': 'Например: Квадратные уравнения или Законы Ньютона',
        'label_difficulty': '📊 Сложность',
        'label_count': '🔢 Кол-во вопросов',
        'opt_beginner': 'Начальный',
        'opt_intermediate': 'Средний',
        'opt_advanced': 'Продвинутый (Олимпиадный)',
        'btn_generate': 'СГЕНЕРИРОВАТЬ ТЕСТ (PHI-3 AI)',
        'auth_required_title': '🔒 Требуется авторизация',
        'auth_required_text': 'Войдите, чтобы использовать ИИ-генератор',
        'loading_text': 'Phi-3 думает... Это может занять до 180 секунд...',
        'task_question': 'Вопрос',
        'task_explanation': '💡 Объяснение:',
        'alert_topic_empty': 'Пожалуйста, введите тему урока!',
        'error_title': '❌ Ошибка',
        'subjects': {
            'mathematics': 'Математика', 'physics': 'Физика', 'informatics': 'Информатика',
            'biology': 'Биология', 'history': 'История', 'english': 'Английский язык'
        },
        'btn_save_task_new': '💾 Сохранить в историю',
        'link_my_tests': 'Мои Тесты',
        'my_tests_title': 'Мои Сохраненные Тесты',
        'no_tests_yet': 'Вы пока не сохранили ни одного теста.',
        'saved_at': 'Сохранено:',
        'view_test': 'Посмотреть тест',
        'go_back_to_generator': '← Вернуться к генератору',
        'metadata_subject': 'Предмет',
        'metadata_grade': 'Класс',
        'metadata_topic': 'Тема',
        'metadata_difficulty': 'Сложность',
        'metadata_task_type': 'Тип задания',
        'descriptor': 'Дескриптор'
    },
    'kk': {
        'title': 'ЖИ Тест Генераторы',
        'subtitle': 'Phi-3 Mini негізіндегі кәсіби тест генераторы',
        'auth_logout': 'Шығу',
        'auth_login': 'Кіру',
        'login_title': 'Жүйеге кіру',
        'register_title': 'Тіркелу',
        'label_email': 'Email',
        'label_password': 'Құпия сөз',
        'label_name': 'Аты',
        'btn_login': 'Кіру',
        'btn_register': 'Тіркелу',
        'link_no_account': 'Аккаунтыңыз жоқ па? Тіркелу',
        'link_has_account': 'Аккаунтыңыз бар ма? Кіру',
        'label_subject': '📚 Пән',
        'label_grade': '🎓 Сынып',
        'label_topic': '💡 Сабақ тақырыбы (Нақты айтыңыз!)',
        'placeholder_topic': 'Мысалы: Квадрат теңдеулер немесе Ньютон заңдары',
        'label_difficulty': '📊 Қиындық деңгейі',
        'label_count': '🔢 Сұрақ саны',
        'opt_beginner': 'Бастауыш',
        'opt_intermediate': 'Орташа',
        'opt_advanced': 'Күрделі (Олимпиадалық)',
        'btn_generate': 'ТЕСТТІ ГЕНЕРАЦИЯЛАУ (PHI-3 AI)',
        'auth_required_title': '🔒 Авторизация қажет',
        'auth_required_text': 'ЖИ-генераторды пайдалану үшін кіріңіз',
        'loading_text': 'Phi-3 ойлануда... Бұл 180 секундқа дейін созылуы мүмкін...',
        'task_question': 'Сұрақ',
        'task_explanation': '💡 Түсіндіру:',
        'alert_topic_empty': 'Сабақ тақырыбын енгізіңіз!',
        'error_title': '❌ Қате',
        'subjects': {
            'mathematics': 'Математика', 'physics': 'Физика', 'informatics': 'Информатика',
            'biology': 'Биология', 'history': 'Тарих', 'english': 'Ағылшын тілі'
        },
        'btn_save_task_new': '💾 Тарихқа сақтау',
        'link_my_tests': 'Менің Тесттерім',
        'my_tests_title': 'Менің Сақталған Тесттерім',
        'no_tests_yet': 'Сіз әлі бірде-бір тест сақтамадыңыз.',
        'saved_at': 'Сақталған уақыты:',
        'view_test': 'Тестті қарау',
        'go_back_to_generator': '← Генераторға оралу',
        'metadata_subject': 'Пән',
        'metadata_grade': 'Сынып',
        'metadata_topic': 'Тақырып',
        'metadata_difficulty': 'Қиындық деңгейі',
        'metadata_task_type': 'Тапсырма түрі',
        'descriptor': 'Дескриптор'
    },
    'en': {
        'title': 'AI Test Generator',
        'subtitle': 'Professional test generator using Phi-3 Mini',
        'auth_logout': 'Logout',
        'auth_login': 'Login',
        'login_title': 'System Login',
        'register_title': 'Registration',
        'label_email': 'Email',
        'label_password': 'Password',
        'label_name': 'Name',
        'btn_login': 'Login',
        'btn_register': 'Register',
        'link_no_account': 'No account? Register',
        'link_has_account': 'Already have an account? Login',
        'label_subject': '📚 Subject',
        'label_grade': '🎓 Grade',
        'label_topic': '💡 Lesson Topic (Be specific!)',
        'placeholder_topic': 'Example: Quadratic Equations or Newton\'s Laws',
        'label_difficulty': '📊 Difficulty',
        'label_count': '🔢 Number of Questions',
        'opt_beginner': 'Beginner',
        'opt_intermediate': 'Intermediate',
        'opt_advanced': 'Advanced (Olympiad)',
        'btn_generate': 'GENERATE TEST (PHI-3 AI)',
        'auth_required_title': '🔒 Authorization Required',
        'auth_required_text': 'Log in to use the AI generator',
        'loading_text': 'Phi-3 is thinking... This may take up to 180 seconds...',
        'task_question': 'Question',
        'task_explanation': '💡 Explanation:',
        'alert_topic_empty': 'Please enter a lesson topic!',
        'error_title': '❌ Error',
        'subjects': {
            'mathematics': 'Mathematics', 'physics': 'Physics', 'informatics': 'Informatics',
            'biology': 'Biology', 'history': 'History', 'english': 'English Language'
        },
        'btn_save_task_new': '💾 Save to History',
        'link_my_tests': 'My Tests',
        'my_tests_title': 'My Saved Tests',
        'no_tests_yet': 'You have not saved any tests yet.',
        'saved_at': 'Saved at:',
        'view_test': 'View Test',
        'go_back_to_generator': '← Back to Generator',
        'metadata_subject': 'Subject',
        'metadata_grade': 'Grade',
        'metadata_topic': 'Topic',
        'metadata_difficulty': 'Difficulty',
        'metadata_task_type': 'Task Type',
        'descriptor': 'Descriptor'
    }
}


class Phi3Generator:
    def __init__(self):
        # Ollama URL
        self.ollama_url = "http://localhost:11434/api/generate" 
        self.model = "phi3:mini"
        
        self.users = {}
        self.load_users()
        self.check_connection()
    
    def check_connection(self):
        """Проверка Ollama қосылуын тексеру"""
        try:
            requests.get("http://localhost:11434/api/tags", timeout=1) 
            print("✅ Phi-3 Mini дайын (Ready).")
            return True
        except:
            print("❌ Ollama табылған жоқ. Оның іске қосылғанын тексеріңіз (localhost:11434).")
            return False

    def ask_phi3(self, prompt, language='ru', timeout=180):
        """Балама сұраныс: Тілге байланысты параметрлерді қолдану және JSON форматын талап ету"""
        
        temperature = 0.2 
        num_predict = 8192 
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False, 
            "format": "json", 
            "options": {
                "temperature": temperature, 
                "num_predict": num_predict, 
                "top_p": 0.9,
                "repeat_penalty": 1.1 
            }
        }
        try:
            print(f"⏳ Phi-3-ке сұраныс жіберілуде ({language.upper()}, Temp: {temperature}, JSON формат)...")
            response = requests.post(self.ollama_url, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                print(f"❌ Ollama қатесі (Status {response.status_code}): {response.text[:100]}")
                return None
                
        except requests.exceptions.Timeout:
            print("❌ Қате: Сұраныс таймаутқа ұшырады.")
            return None
        except Exception as e:
            print(f"❌ Жалпы қате: {e}") 
            return None 

    def create_prompt(self, subject, topic, grade, difficulty, count, language): 
        """Динамикалық тілдік промпт жасау және Bloom таксономиясын қосу"""
        
        texts = DICTIONARY.get(language, DICTIONARY['ru'])
        subject_name = texts['subjects'].get(subject.lower(), subject.capitalize())
        
        # Bloom Таксономиясының анықтамасы
        bloom_levels = [
            "L1 – Білу (атау, тізімдеу, сипаттау)",
            "L2 – Түсіну (түсіндіру, қорыту, мысал келтіру)",
            "L3 – Қолдану (есептеу, қолдану, шешу)",
            "L4 – Талдау (салыстыру, талдау, айырмашылығын табу)",
            "L5 – Жинақтау (құрастыру, жобалау, ұсыну)",
            "L6 – Бағалау (дәлелдеу, баға беру, сынау)"
        ]
        
        # Тілге байланысты нұсқаулықтар
        if language == 'en':
            lang_inst = "Generate questions, options, and explanations STRICTLY in ENGLISH. Ensure each task includes a 'bloomLevel' (L1-L6) and a specific action 'descriptor' (e.g., 'calculates the force')."
            example_q = "What is the capital of Kazakhstan?"
            example_e = "The capital of Kazakhstan is Astana."
            lang_options = ["Option A", "Option B", "Option C", "Option D"]
            example_desc = "Defines the term."
        elif language == 'kk':
            lang_inst = "Сұрақтар, жауаптар және түсіндірмелерді ҚАТАҢ ҚАЗАҚ тілінде жасаңыз. Әр тапсырмаға 'bloomLevel' (L1-L6) және нақты әрекеттік 'descriptor' (мысалы: 'күшті есептейді') қосуды қамтамасыз етіңіз."
            example_q = "Қазақстанның астанасы қай қала?"
            example_e = "Қазақстанның астанасы – Астана қаласы."
            lang_options = ["Жауап А", "Жауап B", "Жауап C", "Жауап D"]
            example_desc = "Мерзімді анықтайды."
        else: # ru
            lang_inst = "Генерируй вопросы, ответы и объяснения СТРОГО на РУССКОМ языке. Убедись, что каждая задача включает 'bloomLevel' (L1-L6) и конкретный 'descriptor' (например: 'вычисляет силу')."
            example_q = "Какой закон описывает движение планет?"
            example_e = "Закон Кеплера описывает движение планет."
            lang_options = ["Ответ 1", "Ответ 2", "Ответ 3", "Ответ 4"]
            example_desc = "Определяет понятие."

        return f"""
        *СТРОГО ВЕРНИ ТОЛЬКО JSON МАССИВ*. Не добавляй комментарии или лишний текст вне JSON блока.
        {lang_inst}
        
        **Bloom Таксономиясы Деңгейлері:** {'; '.join(bloom_levels)}
        
        Создай {count} тестовых заданий по "{subject_name}" на тему "{topic}" ({difficulty}, {grade} класс).
        
        Формат должен быть ТОЛЬКО JSON массива, используя ЛАТИНСКИЕ буквы (A, B, C, D) для correctAnswer. **Обязательно включи поля "bloomLevel" и "descriptor":**
        [
          {{
            "question": "{example_q}",
            "options": ["{lang_options[0]}", "{lang_options[1]}", "{lang_options[2]}", "{lang_options[3]}"],
            "correctAnswer": "B", 
            "explanation": "{example_e}",
            "level": "{difficulty}",
            "bloomLevel": "L1", 
            "descriptor": "{example_desc}"
          }}
        ]
        """
    
    def parse_response(self, text):
        """Парсинг: Енді LLM JSON форматында қайтаруы тиіс деп есептейміз."""
        if not text: return None
        try:
            text = text.strip()

            # [] ішіндегі JSON блогын іздейміз
            match = re.search(r'\[.*\]', text, re.DOTALL)
            
            if match:
                json_str = match.group()
            else:
                json_str = text
            
            return json.loads(json_str)
                
        except json.JSONDecodeError as e:
            try:
                # ASCII емес және басқа да ұсақ таңбаларды жою
                json_str_cleaned = re.sub(r'[^\x00-\x7F]+', '', json_str) 
                return json.loads(json_str_cleaned)
            except:
                print(f"❌ JSON парсинг қатесі: {e}. AI-дан алынған мәтін: {text[:200]}...")
                return None
        except Exception as e:
            print(f"❌ Жалпы парсинг қатесі: {e}")
            return None

    def generate(self, subject, topic, grade, difficulty, count, language='ru'): 
        """Генерациялау функциясы"""
        prompt = self.create_prompt(subject, topic, grade, difficulty, count, language)
        
        response = self.ask_phi3(prompt, language) 
        
        error_lang = DICTIONARY.get(language, DICTIONARY['ru'])
        
        if response is None:
            return [{"question": f"{error_lang['error_title']}: Ollama-дан жауап алынбады немесе сұраныс сәтсіз аяқталды. Журналдарды тексеріңіз.", "options": [], "correctAnswer": "", "explanation": "", "level": "Error"}]
        
        tasks = self.parse_response(response)
        
        if not tasks or not isinstance(tasks, list):
            return [{"question": f"{error_lang['error_title']}: ЖИ жарамды JSON жасай алмады немесе парсинг қатесі. Толық қате журналы консольде.", "options": [], "correctAnswer": "", "explanation": "", "level": "Error"}]
        
        for t in tasks:
            t['level'] = difficulty
        
        return tasks[:int(count)]

    # --- ПАЙДАЛАНУШЫ БАСҚАРУ ЖӘНЕ ТАПСЫРМА БАНКІ ---
    def load_users(self):
        try:
            # users.json файлы болмаған жағдайда қате туындамас үшін
            if os.path.exists("users.json"):
                with open("users.json", "r", encoding='utf-8') as f: self.users = json.load(f)
            else:
                self.users = {}
        except: self.users = {}
        
        for email in self.users:
            if 'saved_tasks' not in self.users[email]:
                self.users[email]['saved_tasks'] = []

    def save_users(self):
        with open("users.json", "w", encoding='utf-8') as f: json.dump(self.users, f, indent=2, ensure_ascii=False)

    def register(self, name, email, password):
        if email in self.users: return False, "Email бос емес"
        self.users[email] = {
            "name": name,
            "email": email,
            "password": generate_password_hash(password),
            "created_at": str(datetime.now()),
            "saved_tasks": []
        }
        self.save_users()
        return True, self.users[email]

    def login(self, email, password):
        user = self.users.get(email)
        if user and check_password_hash(user['password'], password):
            user_data = user.copy()
            user_data['password'] = 'HIDDEN' 
            return True, user_data
        return False, "Қате логин немесе құпия сөз"

    def save_task_to_user(self, user_email, task_data, metadata):
        """Тестті пайдаланушы тарихына сақтау"""
        if user_email in self.users:
            test_record = {
                "id": str(int(time.time())),
                "timestamp": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "metadata": metadata,
                "tasks": task_data
            }
            # Ең жаңа тесттер жоғарыда болуы үшін
            self.users[user_email]['saved_tasks'].insert(0, test_record)
            self.save_users()
            return True
        return False

generator = Phi3Generator()

# --- PDF ГЕНЕРАЦИЯ ФУНКЦИЯСЫ (Дұрысталған) ---
def create_pdf_from_tasks(test_data, texts, language):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter) # 'letter' reportlab импортынан дұрыс келеді
    width, height = letter
    y = height - 50
    line_height = 20
    
    # Қаріпті тексеру
    font_name = FONT_NORMAL
    font_bold = FONT_BOLD
    if not pdfmetrics.isRegisteredFont(font_name):
        font_name = 'Helvetica'
        font_bold = 'Helvetica-Bold'
        
    c.setFont(font_bold, 18)
    c.drawString(50, y, f"{texts['title']} - {test_data['metadata']['topic']}")
    y -= 30

    c.setFont(font_name, 10)
    meta = test_data['metadata']
    c.drawString(50, y, f"{texts['metadata_subject']}: {meta['subject']} | {texts['metadata_grade']}: {meta['grade']} | {texts['metadata_difficulty']}: {meta['difficulty']}")
    y -= 20
    c.drawString(50, y, f"Bloom таксономиясы бар тапсырмалар ({meta['task_type']})")
    y -= 30

    for index, task in enumerate(test_data['tasks']):
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont(font_bold, 14)
            c.drawString(50, y, f"{texts['metadata_topic']}: {meta['topic']} (жалғасы)")
            y -= 30

        # Сұрақ
        c.setFont(font_bold, 12)
        c.drawString(50, y, f"{index+1}. {task['question']}")
        y -= line_height

        # Дескриптор және Bloom
        c.setFont(font_name, 9)
        bloom_desc = f"Bloom: {task.get('bloomLevel', 'N/A')} | {texts.get('descriptor', 'Дескриптор')}: {task.get('descriptor', 'N/A')}"
        c.drawString(70, y, bloom_desc)
        y -= (line_height / 2)

        # Жауап нұсқалары
        c.setFont(font_name, 10)
        # letter айнымалысын инициализациялау (Мәселені шешу!)
        letter = ''
        
        for idx, option in enumerate(task['options']):
            letter = chr(65 + idx)
            prefix = f"{letter}) "
            
            # Егер дұрыс жауап болса, жасылмен белгілеу
            if letter == task.get('correctAnswer'):
                c.setFillColor(colors.green)
                prefix = f"✅ {letter}) "
            else:
                c.setFillColor(colors.black)
            
            c.drawString(70, y - 5, prefix + option[:70] + ('...' if len(option) > 70 else ''))
            y -= 15

        # Түсіндіру
        c.setFont(font_name, 9)
        c.setFillColor(colors.blue)
        c.drawString(70, y - 5, f"    {texts['task_explanation']} {task['explanation'][:100]}...")
        c.setFillColor(colors.black)
        y -= 30 # Келесі сұраққа дейінгі аралық

    c.save()
    buffer.seek(0)
    return buffer

# --- DOCX ГЕНЕРАЦИЯ ФУНКЦИЯСЫ ---
def create_docx_from_tasks(test_data, texts):
    document = Document()
    
    # Қаріпті орнату (Әдепкі Times New Roman DOCX үшін)
    style = document.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)

    # Тақырып
    meta = test_data['metadata']
    document.add_heading(f"{texts['title']}: {meta['topic']}", 0)
    
    meta_p = document.add_paragraph()
    meta_p.add_run(f"{texts['metadata_subject']}: {meta['subject']} | {texts['metadata_grade']}: {meta['grade']} | {texts['metadata_difficulty']}: {meta['difficulty']}").bold = True
    meta_p.add_run(f"\n{texts['saved_at']} {test_data['timestamp']}")
    document.add_paragraph("\n")

    for index, task in enumerate(test_data['tasks']):
        # Сұрақ
        q_p = document.add_paragraph()
        q_p.add_run(f"{index+1}. {task['question']}").bold = True
        
        # Дескриптор және Bloom
        desc_p = document.add_paragraph()
        desc_p.add_run(f"    [Bloom: {task.get('bloomLevel', 'N/A')} | {texts.get('descriptor', 'Дескриптор')}: {task.get('descriptor', 'N/A')}]").italic = True
        desc_p.style.font.size = Pt(10)

        # Жауап нұсқалары
        for idx, option in enumerate(task['options']):
            letter = chr(65 + idx)
            document.add_paragraph(f"    {letter}) {option}", style='ListBullet')
        
        # Түсіндіру
        exp_p = document.add_paragraph()
        exp_p.add_run(f"{texts['task_explanation']} ").bold = True
        exp_p.add_run(task['explanation'])
        
        # Аралық
        document.add_paragraph("\n")

    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

# --- HTML ШАБЛОНДАРЫ (Толық) ---

# Басты генератор бетінің шаблоны
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EduGen Pro | {{ texts.title }}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #3b82f6; --primary-dark: #2563eb; --secondary: #8b5cf6;
            --success: #10b981; --danger: #ef4444; --warning: #f59e0b;
            --dark: #1f2937; --light: #f9fafb; --gray: #6b7280;
            --radius: 12px; --shadow: 0 10px 25px rgba(0,0,0,0.1);
            --transition: all 0.3s ease;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
            min-height: 10vh; color: var(--dark); line-height: 1.6;
        }

        .header {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white; padding: 60px 40px; border-radius: 0 0 var(--radius) var(--radius);
            position: relative; overflow: hidden; text-align: center;
        }

        .header h1 { font-size: 2.5rem; font-weight: 800; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1rem; }

        .container { max-width: 1000px; margin: -40px auto 40px; padding: 0 20px; position: relative; z-index: 10; }

        .card {
            background: white; border-radius: var(--radius); padding: 40px;
            box-shadow: var(--shadow); margin-bottom: 30px; transition: var(--transition);
        }
        
        .list-card {
            background: white; border-radius: var(--radius); padding: 25px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; transition: var(--transition);
            display: flex; justify-content: space-between; align-items: center;
        }
        .list-card:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(0,0,0,0.1); }


        .form-group { margin-bottom: 20px; }
        .form-label { display: block; margin-bottom: 8px; font-weight: 600; }
        
        .form-control, .form-select {
            width: 100%; padding: 12px 15px; border: 2px solid #e5e7eb;
            border-radius: 10px; font-size: 16px; transition: var(--transition);
        }
        
        .form-control:focus, .form-select:focus {
            outline: none; border-color: var(--primary);
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
        }

        .btn {
            display: block; width: 100%; padding: 15px; border: none;
            border-radius: 10px; font-size: 16px; font-weight: 700;
            cursor: pointer; transition: var(--transition); text-align: center; color: white;
            text-decoration: none;
        }
        
        .btn-inline { 
            display: inline-block; width: auto; padding: 10px 20px; 
            font-size: 0.9rem;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
        }
        
        .btn-secondary {
            background: var(--success);
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
        }

        .btn-tertiary {
            background: #6b7280;
            box-shadow: 0 4px 15px rgba(107, 114, 128, 0.4);
        }

        .btn:hover:not(:disabled) { transform: translateY(-2px); }
        .btn:disabled { opacity: 0.7; cursor: not-allowed; }

        #results-area { margin-top: 30px; }
        
        .task-card {
            background: #fff; border-radius: 12px; padding: 25px; margin-bottom: 20px;
            border-left: 6px solid var(--primary); box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            animation: slideIn 0.4s ease-out;
        }

        .task-question { font-size: 1.2rem; font-weight: 600; margin-bottom: 15px; }
        
        .task-options li {
            list-style: none; padding: 10px 15px; background: #f3f4f6;
            margin-bottom: 8px; border-radius: 8px; border: 1px solid transparent;
        }

        .task-options li.correct {
            background: #d1fae5; border-color: #10b981; color: #065f46; font-weight: 600;
        }

        .task-explanation {
            margin-top: 15px; padding: 15px; background: #eff6ff;
            border-radius: 8px; font-size: 0.95rem; color: #1e40af;
        }
        
        .loading { text-align: center; font-size: 1.2rem; color: var(--gray); padding: 40px; display: none; }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .auth-panel { display: flex; justify-content: flex-end; align-items: center; margin-bottom: 10px; }
        .auth-btn {
            background: rgba(255,255,255,0.2); color: white; padding: 8px 20px;
            border-radius: 20px; text-decoration: none; font-weight: 600;
            border: 1px solid rgba(255,255,255,0.4); margin-left: 10px; cursor: pointer;
        }
        .auth-btn:hover { background: white; color: var(--primary); }

        .multi-lang-panel {
            position: absolute; top: 20px; left: 20px; display: flex;
            background: rgba(255,255,255,0.1); border-radius: 20px;
            padding: 5px; border: 1px solid rgba(255,255,255,0.3);
        }
        .lang-btn {
            background: transparent; color: white; padding: 5px 15px;
            border: none; border-radius: 15px; font-size: 0.9rem;
            font-weight: 500; cursor: pointer; transition: var(--transition);
        }
        .lang-btn.active {
            background: white; color: var(--primary); font-weight: 700;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .lang-btn:hover:not(.active) { background: rgba(255,255,255,0.2); }
    </style>
</head>
<body>

    <div class="header">
        <div class="multi-lang-panel">
            <span style="display:flex; align-items:center; margin-right:10px; font-weight:600; font-size:1rem; opacity:0.8;">
                <i class="fas fa-language"></i> Көптілді режим:
            </span>
            <button class="lang-btn" data-lang="kk">Қазақша</button>
            <button class="lang-btn" data-lang="ru">Орысша</button>
            <button class="lang-btn" data-lang="en">Ағылшынша</button>
        </div>

        <div class="auth-panel">
            {% if user %}
                <span>👤 {{ user.name }}</span>
                <button onclick="window.location.href='/'" class="auth-btn" style="margin-left: 10px;">
                    <i class="fas fa-magic"></i> Генератор
                </button>
                <button onclick="window.location.href='/my_tests'" class="auth-btn" style="margin-left: 10px;">
                    <i class="fas fa-list-alt"></i> {{ texts.link_my_tests }}
                </button>
                <button onclick="logout()" class="auth-btn">
                    <i class="fas fa-sign-out-alt"></i> {{ texts.auth_logout }}
                </button>
            {% else %}
                <button onclick="showLogin()" class="auth-btn">
                    <i class="fas fa-sign-in-alt"></i> {{ texts.auth_login }}
                </button>
            {% endif %}
        </div>
        <h1><a href="/" style="color:white; text-decoration:none;"><i class="fas fa-brain"></i> EDUGEN PRO</a></h1>
        <p>{{ texts.subtitle }}</p>
    </div>

    <div class="container">
        
        <div id="login-form" class="card" style="display: none; max-width: 400px; margin: 0 auto;">
            <h2 style="margin-bottom: 20px; text-align: center;">{{ texts.login_title }}</h2>
            <div class="form-group">
                <label class="form-label">{{ texts.label_email }}</label>
                <input type="email" id="email" class="form-control" placeholder="admin@example.com">
            </div>
            <div class="form-group">
                <label class="form-label">{{ texts.label_password }}</label>
                <input type="password" id="password" class="form-control" placeholder="123456">
            </div>
            <button onclick="login()" class="btn btn-primary">{{ texts.btn_login }}</button>
            <p style="text-align: center; margin-top: 15px; cursor: pointer; color: var(--primary);" onclick="showRegister()">{{ texts.link_no_account }}</p>
        </div>

        <div id="register-form" class="card" style="display: none; max-width: 400px; margin: 0 auto;">
            <h2 style="margin-bottom: 20px; text-align: center;">{{ texts.register_title }}</h2>
            <div class="form-group">
                <label class="form-label">{{ texts.label_name }}</label>
                <input type="text" id="reg-name" class="form-control">
            </div>
            <div class="form-group">
                <label class="form-label">{{ texts.label_email }}</label>
                <input type="email" id="reg-email" class="form-control">
            </div>
            <div class="form-group">
                <label class="form-label">{{ texts.label_password }}</label>
                <input type="password" id="reg-password" class="form-control">
            </div>
            <button onclick="register()" class="btn btn-primary">{{ texts.btn_register }}</button>
            <p style="text-align: center; margin-top: 15px; cursor: pointer; color: var(--primary);" onclick="showLogin()">{{ texts.link_has_account }}</p>
        </div>

        <div id="generator-panel" class="card" {% if not user %}style="filter: blur(4px); pointer-events: none;"{% endif %}>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div class="form-group">
                    <label class="form-label">{{ texts.label_subject }}</label>
                    <select id="subject" class="form-select">
                        {% for key, value in texts.subjects.items() %}
                            <option value="{{ key }}">{{ value }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">{{ texts.label_grade }}</label>
                    <select id="grade" class="form-select">
                        <option value="5">5 {{ texts.label_grade.split(' ')[1] }}</option>
                        <option value="7">7 {{ texts.label_grade.split(' ')[1] }}</option>
                        <option value="9" selected>9 {{ texts.label_grade.split(' ')[1] }}</option>
                        <option value="11">11 {{ texts.label_grade.split(' ')[1] }}</option>
                    </select>
                </div>
            </div>

            <div class="form-group">
                <label class="form-label">{{ texts.label_topic }}</label>
                <input type="text" id="topic" class="form-control" placeholder="{{ texts.placeholder_topic }}">
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                <div class="form-group">
                    <label class="form-label">📝 Тапсырма түрі</label>
                    <select id="task_type" class="form-select">
                        <option value="test" selected>Тест</option>
                        <option value="kb">ҚБ (Формативті бағалау)</option>
                        <option value="zb">ЖБ (Жиынтық)</option>
                        <option value="open_question">Ашық сұрақ</option>
                        <option value="descriptor">Дескрипторлық тапсырма</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">{{ texts.label_difficulty }}</label>
                    <select id="difficulty" class="form-select">
                        <option value="beginner">{{ texts.opt_beginner }}</option>
                        <option value="intermediate" selected>{{ texts.opt_intermediate }}</option>
                        <option value="advanced">{{ texts.opt_advanced }}</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">{{ texts.label_count }}</label>
                    <select id="count" class="form-select">
                        <option value="3">3 {{ texts.label_count.split(' ')[1] }}</option>
                        <option value="5" selected>5 {{ texts.label_count.split(' ')[1] }}</option>
                        <option value="10">10 {{ texts.label_count.split(' ')[1] }}</option>
                    </select>
                </div>
            </div>

            <button onclick="generateTests()" class="btn btn-primary" id="gen-btn">
                <i class="fas fa-magic"></i> {{ texts.btn_generate }}
            </button>
        </div>

        <div id="auth-overlay" style="text-align: center; margin-top: -200px; position: relative; z-index: 20; {% if user %}display:none;{% endif %}">
            <div style="background: white; padding: 20px; display: inline-block; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
                <h3>{{ texts.auth_required_title }}</h3>
                <p>{{ texts.auth_required_text }}</p>
                <button onclick="showLogin()" class="btn btn-primary" style="margin-top: 10px;">{{ texts.btn_login }}</button>
            </div>
        </div>

        <div id="loading" class="loading">
            <i class="fas fa-spinner fa-spin fa-3x" style="color: var(--primary);"></i>
            <p style="margin-top: 15px;">{{ texts.loading_text }}</p>
        </div>

        <div id="results-area">
            <div id="save-button-container" style="display: none; margin-bottom: 20px; display: flex; gap: 10px;">
                <button onclick="saveTasks()" class="btn btn-secondary btn-inline" id="save-btn" style="flex-grow: 1;">
                    {{ texts.btn_save_task_new }}
                </button>
                <a href="/download/pdf/current" class="btn btn-primary btn-inline" style="background: #ef4444; width: auto;">
                    <i class="fas fa-file-pdf"></i> PDF
                </a>
                <a href="/download/docx/current" class="btn btn-primary btn-inline" style="background: #2563eb; width: auto;">
                    <i class="fas fa-file-word"></i> Word
                </a>
            </div>
        </div>

    </div>

    <script>
        // Глобальные переменные для сохранения заданий
        let lastGeneratedTasks = []; 
        let lastGenerationMetadata = {};

        // --- MULTI-LANG LOGIC ---
        const langBtns = document.querySelectorAll('.lang-btn');
        const defaultLang = 'ru'; 
        let currentLang = localStorage.getItem('appLang') || defaultLang;

        function setLang(lang) {
            currentLang = lang;
            localStorage.setItem('appLang', lang);
            window.location.href = `/?lang=${lang}`; 
        }

        langBtns.forEach(btn => {
            if (btn.dataset.lang === currentLang) {
                btn.classList.add('active');
            }
            btn.addEventListener('click', () => {
                setLang(btn.dataset.lang);
            });
        });
        
        // --- AUTH LOGIC ---
        function hideAllForms() {
            document.getElementById('generator-panel').style.display = 'block';
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('register-form').style.display = 'none';
            
            const authOverlay = document.getElementById('auth-overlay');
            if (authOverlay) {
                authOverlay.style.display = 'none';
            }
        }

        function showLogin() {
            hideAllForms();
            document.getElementById('generator-panel').style.display = 'none';
            document.getElementById('login-form').style.display = 'block';
        }

        function showRegister() {
            hideAllForms();
            document.getElementById('generator-panel').style.display = 'none';
            document.getElementById('register-form').style.display = 'block';
        }

        async function login() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            const res = await fetch('/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, password})
            });
            
            const data = await res.json();
            if (data.success) {
                location.reload();
            } else {
                alert(data.message);
            }
        }

        async function logout() {
            await fetch('/logout', {method: 'POST'});
            window.location.href = '/';
        }

        async function register() {
            const name = document.getElementById('reg-name').value;
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;
            
            const res = await fetch('/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, email, password})
            });
            
            const data = await res.json();
            if (data.success) {
                location.reload();
            } else {
                alert(data.message);
            }
        }

        // --- GENERATION LOGIC ---
        async function generateTests() {
            const btn = document.getElementById('gen-btn');
            const loading = document.getElementById('loading');
            const results = document.getElementById('results-area');
            const topic = document.getElementById('topic').value;

            if (!topic) { 
                alert("{{ texts.alert_topic_empty }}"); 
                return; 
            }

            btn.disabled = true;
            results.innerHTML = document.getElementById('save-button-container').outerHTML;
            document.getElementById('save-button-container').style.display = 'none';
            loading.style.display = 'block';

            const taskType = document.getElementById('task_type').value; 
            
            const payload = {
                subject: document.getElementById('subject').value,
                topic: topic,
                grade: document.getElementById('grade').value,
                difficulty: document.getElementById('difficulty').value,
                task_count: document.getElementById('count').value,
                language: currentLang,
                task_type: taskType 
            };
            
            // Сохраняем метаданные для истории
            const selectedSubject = document.getElementById('subject').value;
            const subjectText = document.querySelector(`#subject option[value="${selectedSubject}"]`).textContent;

            const selectedDifficulty = document.getElementById('difficulty').value;
            const difficultyText = document.querySelector(`#difficulty option[value="${selectedDifficulty}"]`).textContent;

            const selectedTaskType = document.getElementById('task_type').value;
            const taskTypeText = document.querySelector(`#task_type option[value="${selectedTaskType}"]`).textContent;
            
            lastGenerationMetadata = {
                subject: subjectText,
                topic: topic,
                grade: document.getElementById('grade').value,
                difficulty: difficultyText,
                task_type: taskTypeText,
            };


            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });

                const data = await response.json();
                loading.style.display = 'none';
                btn.disabled = false;

                if (data.success) {
                    lastGeneratedTasks = data.tasks; 
                    renderTasks(data.tasks);
                    document.getElementById('save-button-container').style.display = 'flex'; // Display as flex
                } else {
                    const saveContainer = document.getElementById('save-button-container').outerHTML;
                    results.innerHTML = saveContainer + `<div class="card" style="border-left: 5px solid red;"><h3>{{ texts.error_title }}</h3><p>${data.message}</p></div>`;
                    document.getElementById('save-button-container').style.display = 'none';
                    lastGeneratedTasks = [];
                }

            } catch (e) {
                loading.style.display = 'none';
                btn.disabled = false;
                alert("Сервермен байланыс қатесі");
                document.getElementById('save-button-container').style.display = 'none';
                lastGeneratedTasks = [];
            }
        }

        function renderTasks(tasks) {
            const container = document.getElementById('results-area');
            let html = '';

            tasks.forEach((task, index) => {
                let optionsHtml = '';
                task.options.forEach((opt, i) => {
                    const letter = String.fromCharCode(65 + i); 
                    const isCorrect = letter === task.correctAnswer ? 'correct' : '';
                    optionsHtml += `<li class="${isCorrect}"><strong>${letter})</strong> ${opt}</li>`;
                });

                // Жаңа өрістерді қосу
                const bloomLevel = task.bloomLevel || 'N/A';
                const descriptor = task.descriptor || 'N/A';

                html += `
                <div class="task-card">
                    <div style="display:flex; justify-content:space-between; align-items: flex-start;">
                        <span style="background:#dbeafe; color:#1e40af; padding:5px 10px; border-radius:15px; font-size:0.8rem;">{{ texts.task_question }} ${index+1}</span>
                        <div style="text-align: right;">
                            <span style="background:#fee2e2; color:#ef4444; padding:3px 8px; border-radius:10px; font-size:0.75rem; font-weight:600; display: inline-block; margin-bottom: 5px;">
                                Bloom: ${bloomLevel}
                            </span>
                            <span style="color:#6b7280; font-size:0.8rem; display: block;">${task.level}</span>
                        </div>
                    </div>
                    
                    <div style="margin-top: 10px; padding: 10px; border: 1px dashed #ccc; border-radius: 8px; background: #fcfcfc;">
                        <strong style="color: var(--secondary);"><i class="fas fa-magic"></i> {{ texts.descriptor }}:</strong> ${descriptor}
                    </div>

                    <div class="task-question" style="margin-top:15px;">${task.question}</div>
                    <ul class="task-options">${optionsHtml}</ul>
                    <div class="task-explanation">
                        <strong>{{ texts.task_explanation }}</strong> ${task.explanation}
                    </div>
                </div>`;
            });
            
            const saveContainer = document.getElementById('save-button-container').outerHTML;
            container.innerHTML = saveContainer + html;
            document.getElementById('save-button-container').style.display = 'flex'; // Display as flex
        }

        // --- СОХРАНЕНИЕ ЗАДАНИЙ В ИСТОРИЮ (ТИХОЕ) ---
        async function saveTasks() {
            if (lastGeneratedTasks.length === 0) {
                alert("Сақтауға тапсырмалар жоқ.");
                return;
            }

            const saveBtn = document.getElementById('save-btn');
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ...';

            try {
                const response = await fetch('/save_task', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        tasks: lastGeneratedTasks,
                        metadata: lastGenerationMetadata
                    })
                });

                const data = await response.json();
                saveBtn.disabled = false;
                
                if (data.success) {
                    saveBtn.innerHTML = '<i class="fas fa-check"></i> Сохранено!';
                    // Скрываем кнопку и очищаем буфер через 2 секунды
                    setTimeout(() => {
                         saveBtn.innerHTML = '{{ texts.btn_save_task_new }}';
                         document.getElementById('save-button-container').style.display = 'none'; 
                         lastGeneratedTasks = [];
                    }, 2000); 
                } else {
                    saveBtn.innerHTML = '❌ Қате';
                    setTimeout(() => {
                         saveBtn.innerHTML = '{{ texts.btn_save_task_new }}';
                    }, 2000); 
                    console.error('Ошибка сохранения:', data.message);
                }

            } catch (e) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '❌ Қате';
                setTimeout(() => {
                         saveBtn.innerHTML = '{{ texts.btn_save_task_new }}';
                    }, 2000);
            }
        }
    </script>
</body>
</html>
'''

# Шаблон для страницы "Мои Тесты"
MY_TESTS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EduGen Pro | {{ texts.my_tests_title }}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #3b82f6; --primary-dark: #2563eb; --secondary: #8b5cf6;
            --success: #10b981; --danger: #ef4444; --warning: #f59e0b;
            --dark: #1f2937; --light: #f9fafb; --gray: #6b7280;
            --radius: 12px; --shadow: 0 10px 25px rgba(0,0,0,0.1);
            --transition: all 0.3s ease;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
            min-height: 10vh; color: var(--dark); line-height: 1.6;
        }

        .header {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white; padding: 60px 40px; border-radius: 0 0 var(--radius) var(--radius);
            position: relative; overflow: hidden; text-align: center;
        }

        .header h1 { font-size: 2.5rem; font-weight: 800; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1rem; }

        .container { max-width: 1000px; margin: -40px auto 40px; padding: 0 20px; position: relative; z-index: 10; }

        .card {
            background: white; border-radius: var(--radius); padding: 40px;
            box-shadow: var(--shadow); margin-bottom: 30px; transition: var(--transition);
        }
        
        .list-card {
            background: white; border-radius: var(--radius); padding: 25px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; transition: var(--transition);
            display: flex; justify-content: space-between; align-items: center;
            border-left: 5px solid var(--primary);
        }
        .list-card:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(0,0,0,0.1); }
        .list-card .details { flex-grow: 1; }
        .list-card .details h4 { margin: 0 0 5px 0; font-size: 1.1rem; font-weight: 600; }
        .list-card .details p { margin: 0; font-size: 0.9rem; color: var(--gray); }
        .list-card .actions { margin-left: 20px; }

        .btn {
            display: block; width: 100%; padding: 15px; border: none;
            border-radius: 10px; font-size: 16px; font-weight: 700;
            cursor: pointer; transition: var(--transition); text-align: center; color: white;
            text-decoration: none;
        }
        
        .btn-inline { 
            display: inline-block; width: auto; padding: 10px 20px; 
            font-size: 0.9rem;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
        }
        
        .btn-secondary {
            background: var(--success);
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
        }
        
        .btn-tertiary {
            background: #6b7280;
            box-shadow: 0 4px 15px rgba(107, 114, 128, 0.4);
        }

        .btn:hover:not(:disabled) { transform: translateY(-2px); }
        .btn:disabled { opacity: 0.7; cursor: not-allowed; }

        .auth-panel { display: flex; justify-content: flex-end; align-items: center; margin-bottom: 10px; }
        .auth-btn {
            background: rgba(255,255,255,0.2); color: white; padding: 8px 20px;
            border-radius: 20px; text-decoration: none; font-weight: 600;
            border: 1px solid rgba(255,255,255,0.4); margin-left: 10px; cursor: pointer;
        }
        .auth-btn:hover { background: white; color: var(--primary); }

        .multi-lang-panel {
            position: absolute; top: 20px; left: 20px; display: flex;
            background: rgba(255,255,255,0.1); border-radius: 20px;
            padding: 5px; border: 1px solid rgba(255,255,255,0.3);
        }
        .lang-btn {
            background: transparent; color: white; padding: 5px 15px;
            border: none; border-radius: 15px; font-size: 0.9rem;
            font-weight: 500; cursor: pointer; transition: var(--transition);
        }
        .lang-btn.active {
            background: white; color: var(--primary); font-weight: 700;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .lang-btn:hover:not(.active) { background: rgba(255,255,255,0.2); }
    </style>
</head>
<body>

    <div class="header">
        <div class="multi-lang-panel">
            <span style="display:flex; align-items:center; margin-right:10px; font-weight:600; font-size:1rem; opacity:0.8;">
                <i class="fas fa-language"></i> Көптілді режим:
            </span>
            <button class="lang-btn" data-lang="kk">Қазақша</button>
            <button class="lang-btn" data-lang="ru">Орысша</button>
            <button class="lang-btn" data-lang="en">Ағылшынша</button>
        </div>

        <div class="auth-panel">
            {% if user %}
                <span>👤 {{ user.name }}</span>
                <a href="/" class="auth-btn" style="margin-left: 10px;">
                    <i class="fas fa-magic"></i> Генератор
                </a>
                <a href="/my_tests" class="auth-btn" style="margin-left: 10px; background: white; color: var(--primary);">
                    <i class="fas fa-list-alt"></i> {{ texts.link_my_tests }}
                </a>
                <button onclick="logout()" class="auth-btn">
                    <i class="fas fa-sign-out-alt"></i> {{ texts.auth_logout }}
                </button>
            {% else %}
                <button onclick="showLogin()" class="auth-btn">
                    <i class="fas fa-sign-in-alt"></i> {{ texts.auth_login }}
                </button>
            {% endif %}
        </div>
        <h1><a href="/" style="color:white; text-decoration:none;"><i class="fas fa-brain"></i> EDUGEN PRO</a></h1>
        <p>{{ texts.subtitle }}</p>
    </div>

    <div class="container">
        
        <h2 style="margin-bottom: 20px; font-weight: 700;">{{ texts.my_tests_title }}</h2>

        {% if not tests %}
            <div class="card" style="text-align: center; color: var(--gray);">
                <i class="fas fa-box-open fa-3x" style="margin-bottom: 15px;"></i>
                <p>{{ texts.no_tests_yet }}</p>
            </div>
        {% else %}
            {% for test in tests %}
                <div class="list-card">
                    <div class="details">
                        <h4>{{ test.metadata.topic }} ({{ test.metadata.task_type }})</h4>
                        <p>
                            <i class="fas fa-book"></i> {{ test.metadata.subject }} | 
                            <i class="fas fa-graduation-cap"></i> {{ test.metadata.grade }} | 
                            <i class="fas fa-tachometer-alt"></i> {{ test.metadata.difficulty }}
                        </p>
                        <p style="margin-top: 5px;">
                            <span style="font-weight: 600;">{{ texts.saved_at }}</span> 
                            {{ test.timestamp }}
                        </p>
                    </div>
                    <div class="actions">
                        <a href="/view_test/{{ test.id }}" class="btn btn-primary btn-inline">
                            {{ texts.view_test }}
                        </a>
                    </div>
                </div>
            {% endfor %}
        {% endif %}

    </div>
    
    <script>
        // Инициализация языка для lang-btn
        const langBtns = document.querySelectorAll('.lang-btn');
        const currentLang = '{{ lang }}';
        langBtns.forEach(btn => {
            if (btn.dataset.lang === currentLang) {
                btn.classList.add('active');
            }
            btn.addEventListener('click', () => {
                // Перенаправление на главную страницу с новым языком, чтобы обновить тексты
                window.location.href = `/?lang=${btn.dataset.lang}`;
            });
        });
        
        function logout() {
            fetch('/logout', {method: 'POST'}).then(() => {
                window.location.href = '/';
            });
        }
    </script>
</body>
</html>
'''

# Шаблон для просмотра одного теста (С Bloom және Дескрипторлармен)
VIEW_TEST_TEMPLATE = '''
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EduGen Pro | {{ test.metadata.topic }}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #3b82f6; --primary-dark: #2563eb; --secondary: #8b5cf6;
            --success: #10b981; --danger: #ef4444; --warning: #f59e0b;
            --dark: #1f2937; --light: #f9fafb; --gray: #6b7280;
            --radius: 12px; --shadow: 0 10px 25px rgba(0,0,0,0.1);
            --transition: all 0.3s ease;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
            min-height: 10vh; color: var(--dark); line-height: 1.6;
        }

        .header {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white; padding: 60px 40px; border-radius: 0 0 var(--radius) var(--radius);
            position: relative; overflow: hidden; text-align: center;
        }

        .header h1 { font-size: 2.5rem; font-weight: 800; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1rem; }

        .container { max-width: 1000px; margin: -40px auto 40px; padding: 0 20px; position: relative; z-index: 10; }

        .card {
            background: white; border-radius: var(--radius); padding: 40px;
            box-shadow: var(--shadow); margin-bottom: 30px; transition: var(--transition);
        }
        
        .list-card {
            background: white; border-radius: var(--radius); padding: 25px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; transition: var(--transition);
            display: flex; justify-content: space-between; align-items: center;
        }
        .list-card:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(0,0,0,0.1); }

        .btn {
            display: block; width: 100%; padding: 15px; border: none;
            border-radius: 10px; font-size: 16px; font-weight: 700;
            cursor: pointer; transition: var(--transition); text-align: center; color: white;
            text-decoration: none;
        }
        
        .btn-inline { 
            display: inline-block; width: auto; padding: 10px 20px; 
            font-size: 0.9rem;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
        }
        
        .btn-secondary {
            background: var(--success);
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
        }

        .btn-tertiary {
            background: #6b7280;
            box-shadow: 0 4px 15px rgba(107, 114, 128, 0.4);
        }

        .btn:hover:not(:disabled) { transform: translateY(-2px); }
        .btn:disabled { opacity: 0.7; cursor: not-allowed; }

        .task-card {
            background: #fff; border-radius: 12px; padding: 25px; margin-bottom: 20px;
            border-left: 6px solid var(--primary); box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            animation: slideIn 0.4s ease-out;
        }

        .task-question { font-size: 1.2rem; font-weight: 600; margin-bottom: 15px; }
        
        .task-options li {
            list-style: none; padding: 10px 15px; background: #f3f4f6;
            margin-bottom: 8px; border-radius: 8px; border: 1px solid transparent;
        }

        .task-options li.correct {
            background: #d1fae5; border-color: #10b981; color: #065f46; font-weight: 600;
        }

        .task-explanation {
            margin-top: 15px; padding: 15px; background: #eff6ff;
            border-radius: 8px; font-size: 0.95rem; color: #1e40af;
        }
        
        .auth-panel { display: flex; justify-content: flex-end; align-items: center; margin-bottom: 10px; }
        .auth-btn {
            background: rgba(255,255,255,0.2); color: white; padding: 8px 20px;
            border-radius: 20px; text-decoration: none; font-weight: 600;
            border: 1px solid rgba(255,255,255,0.4); margin-left: 10px; cursor: pointer;
        }
        .auth-btn:hover { background: white; color: var(--primary); }
        
        .metadata-box {
            background: #fff; border-radius: var(--radius); padding: 20px; 
            box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 30px; 
            border: 1px solid #e5e7eb;
        }
        .metadata-box p { margin-bottom: 5px; font-size: 0.95rem; }
        .metadata-box p strong { font-weight: 700; color: var(--dark); margin-right: 5px; }
    </style>
</head>
<body>

    <div class="header">
        <div class="auth-panel">
            <a href="/my_tests" class="auth-btn">
                <i class="fas fa-list-alt"></i> {{ texts.link_my_tests }}
            </a>
            <a href="/" class="auth-btn" style="margin-left: 10px;">
                <i class="fas fa-magic"></i> Генератор
            </a>
            <button onclick="logout()" class="auth-btn">
                <i class="fas fa-sign-out-alt"></i> {{ texts.auth_logout }}
            </button>
        </div>
        <h1><a href="/" style="color:white; text-decoration:none;"><i class="fas fa-brain"></i> EDUGEN PRO</a></h1>
        <p>{{ test.metadata.topic }}</p>
    </div>

    <div class="container">
        
        <div style="margin-bottom: 20px; display: flex; gap: 10px; align-items: center;">
            <a href="/my_tests" class="btn btn-tertiary btn-inline">
                {{ texts.go_back_to_generator }}
            </a>
            <a href="/download/pdf/{{ test.id }}" class="btn btn-primary btn-inline" style="background: #ef4444; width: auto;">
                <i class="fas fa-file-pdf"></i> PDF
            </a>
            <a href="/download/docx/{{ test.id }}" class="btn btn-primary btn-inline" style="background: #2563eb; width: auto;">
                <i class="fas fa-file-word"></i> Word
            </a>
        </div>

        <div class="metadata-box">
            <h3 style="margin-bottom: 15px; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">
                {{ texts.my_tests_title }} - {{ test.metadata.topic }}
            </h3>
            <p><strong>{{ texts.metadata_subject }}:</strong> {{ test.metadata.subject }}</p>
            <p><strong>{{ texts.metadata_grade }}:</strong> {{ test.metadata.grade }}</p>
            <p><strong>{{ texts.metadata_difficulty }}:</strong> {{ test.metadata.difficulty }}</p>
            <p><strong>{{ texts.metadata_task_type }}:</strong> {{ test.metadata.task_type }}</p>
            <p style="margin-top: 10px;"><strong>{{ texts.saved_at }}</strong> {{ test.timestamp }}</p>
        </div>

        {% for task in test.tasks %}
            <div class="task-card">
                <div style="display:flex; justify-content:space-between; align-items: flex-start;">
                    <span style="background:#dbeafe; color:#1e40af; padding:5px 10px; border-radius:15px; font-size:0.8rem;">{{ texts.task_question }} {{ loop.index }}</span>
                    <div style="text-align: right;">
                        <span style="background:#fee2e2; color:#ef4444; padding:3px 8px; border-radius:10px; font-size:0.75rem; font-weight:600; display: inline-block; margin-bottom: 5px;">
                            Bloom: {{ task.bloomLevel | default('N/A') }}
                        </span>
                        <span style="color:#6b7280; font-size:0.8rem; display: block;">{{ task.level }}</span>
                    </div>
                </div>
                
                <div style="margin-top: 10px; padding: 10px; border: 1px dashed #ccc; border-radius: 8px; background: #fcfcfc;">
                    <strong style="color: var(--secondary);"><i class="fas fa-magic"></i> {{ texts.descriptor }}:</strong> {{ task.descriptor | default('N/A') }}
                </div>
                
                <div class="task-question" style="margin-top:15px;">{{ task.question }}</div>
                <ul class="task-options">
                    {% for opt in task.options %}
                        {% set letter = loop.index | chr_to_upper_case %}
                        {% set is_correct = 'correct' if letter == task.correctAnswer else '' %}
                        <li class="{{ is_correct }}"><strong>{{ letter }})</strong> {{ opt }}</li>
                    {% endfor %}
                </ul>
                <div class="task-explanation">
                    <strong>{{ texts.task_explanation }}</strong> {{ task.explanation }}
                </div>
            </div>
        {% endfor %}

    </div>
    
    <script>
        function logout() {
            fetch('/logout', {method: 'POST'}).then(() => {
                window.location.href = '/';
            });
        }
    </script>
</body>
</html>
'''

# --- FLASK МАРШРУТТАРЫ ---

def chr_to_upper_case(index):
    return chr(64 + index)

app.jinja_env.filters['chr_to_upper_case'] = chr_to_upper_case

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def index():
    user_lang = request.args.get('lang')
    if not user_lang:
        user_lang = session.get('language', 'ru')
    
    session['language'] = user_lang
    texts = DICTIONARY.get(user_lang, DICTIONARY['ru'])
    
    return render_template_string(HTML_TEMPLATE, user=session.get('user'), lang=user_lang, texts=texts)

@app.route('/login', methods=['POST'])
def login_route():
    data = request.json
    success, res = generator.login(data['email'], data['password'])
    if success:
        session['user'] = res
        return jsonify({"success": True, "name": res.get("name")})
    return jsonify({"success": False, "message": res})

@app.route('/register', methods=['POST'])
def register_route():
    data = request.json
    success, res = generator.register(data['name'], data['email'], data['password'])
    if success:
        session['user'] = res
        return jsonify({"success": True, "name": res.get("name")})
    return jsonify({"success": False, "message": res})

@app.route('/logout', methods=['POST'])
def logout_route():
    session.clear()
    return jsonify({"success": True})


@app.route('/generate', methods=['POST'])
def generate_route():
    if 'user' not in session: return jsonify({"success": False, "message": "Авторизация қажет"}), 401
    
    data = request.json
    
    tasks = generator.generate(
        data.get('subject'), 
        data.get('topic'), 
        data.get('grade'), 
        data.get('difficulty'), 
        data.get('task_count', 5),
        data.get('language', 'ru') 
    )
    
    if tasks and tasks[0].get('level') == 'Error':
        return jsonify({"success": False, "message": tasks[0]['question']})
    
    # Сәтті болған жағдайда, соңғы генерацияны сессияға сақтау (Жүктеу үшін)
    if tasks and not tasks[0].get('level') == 'Error':
        
        # subject мәнін таңбалы мәннен сөздікке түрлендіру
        subject_key = data.get('subject')
        subject_display = DICTIONARY.get(data.get('language', 'ru'), DICTIONARY['ru'])['subjects'].get(subject_key)
        if not subject_display:
            subject_display = subject_key.capitalize() # Егер сөздікте табылмаса

        session['last_generated_tasks'] = tasks
        session['last_generation_metadata'] = {
            'subject': subject_display,
            'topic': data.get('topic'),
            'grade': data.get('grade'),
            'difficulty': data.get('difficulty'),
            'task_type': data.get('task_type', 'test')
        }
        
    return jsonify({"success": True, "tasks": tasks})


@app.route('/save_task', methods=['POST'])
def save_task_route():
    """Тапсырманы пайдаланушы тарихына үнсіз сақтау"""
    if 'user' not in session: 
        return jsonify({"success": False, "message": "Авторизация қажет."}), 401
    
    data = request.json
    user_email = session['user']['email']
    tasks = data.get('tasks')
    metadata = data.get('metadata')
    
    if not tasks or not metadata:
        return jsonify({"success": False, "message": "Жарамсыз деректер: тапсырмалар немесе метадеректер жоқ."}), 400
        
    if generator.save_task_to_user(user_email, tasks, metadata):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Пайдаланушы табылмады немесе сақтау қатесі."}), 500

@app.route('/my_tests')
def my_tests_route():
    """Пайдаланушының сақталған тесттерін көрсетеді"""
    user = session.get('user')
    user_lang = session.get('language', 'ru')
    texts = DICTIONARY.get(user_lang, DICTIONARY['ru'])

    if not user:
        return redirect(url_for('index', lang=user_lang))
        
    user_data = generator.users.get(user['email'])
    saved_tests = user_data.get('saved_tasks', []) if user_data else []
    
    return render_template_string(
        MY_TESTS_TEMPLATE,
        user=user, 
        tests=saved_tests, 
        lang=user_lang, 
        texts=texts
    )

@app.route('/view_test/<test_id>')
def view_test_route(test_id):
    """Бір сақталған тестті толық көрсетеді"""
    user = session.get('user')
    user_lang = session.get('language', 'ru')
    texts = DICTIONARY.get(user_lang, DICTIONARY['ru'])

    if not user:
        return redirect(url_for('index', lang=user_lang))

    user_data = generator.users.get(user['email'])
    saved_tests = user_data.get('saved_tasks', []) if user_data else []
    
    test_to_view = next((test for test in saved_tests if test['id'] == test_id), None)
    
    if not test_to_view:
        return f"Тест табылмады (ID: {test_id})", 404
        
    return render_template_string(
        VIEW_TEST_TEMPLATE,
        user=user, 
        test=test_to_view, 
        lang=user_lang, 
        texts=texts
    )

# --- ЖҮКТЕУ ФУНКЦИЯЛАРЫ ---
def get_test_data(test_id=None):
    """Жүктеу үшін тест деректерін алу (Тарихтан немесе соңғы генерациядан)"""
    user = session.get('user')
    if not user: return None
    
    if test_id == 'current':
        # Соңғы генерацияны сессиядан алу
        tasks = session.get('last_generated_tasks')
        metadata = session.get('last_generation_metadata')
        if tasks and metadata:
            return {
                "id": "current",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "metadata": metadata,
                "tasks": tasks
            }
        return None
    
    if test_id:
        # Тарихтан алу
        user_data = generator.users.get(user['email'])
        saved_tests = user_data.get('saved_tasks', [])
        test = next((t for t in saved_tests if t['id'] == test_id), None)
        return test
        
    return None

@app.route('/download/<format>/<test_id>')
def download_test(format, test_id):
    if 'user' not in session: abort(401)
    user_lang = session.get('language', 'ru')
    texts = DICTIONARY.get(user_lang, DICTIONARY['ru'])

    test_data = get_test_data(test_id)
    
    if not test_data or not test_data['tasks']:
        abort(404, description="Test data not found or empty.")

    # Файл атын тақырып негізінде тазалау
    # Қазақ/Орыс әріптерін де ескеру
    filename_base = re.sub(r'[^a-zA-Z0-9А-Яа-яӨөҰұҚқЕеГгҺһІіҢң]', '_', test_data['metadata']['topic'])[:30]

    if format == 'pdf':
        buffer = create_pdf_from_tasks(test_data, texts, user_lang)
        filename = f"{filename_base}_test.pdf"
        mimetype = 'application/pdf'
    elif format == 'docx':
        buffer = create_docx_from_tasks(test_data, texts)
        filename = f"{filename_base}_test.docx"
        mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    else:
        abort(400, description="Invalid format specified.")

    return send_file(
        buffer,
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    # Әдепкі әкімші аккаунтының бар екеніне көз жеткізу
    if 'admin@example.com' not in generator.users:
        generator.register("Admin", "admin@example.com", "123456")
        print("👤 Әдепкі аккаунт жасалды: admin@example.com / 123456")

    print(f"\n🚀 EduGen Pro іске қосылды: [http://127.0.0.1:5000](http://127.0.0.1:5000)")
    app.run(debug=True, threaded=False, host='0.0.0.0')