// Переключение темы
const themeToggle = document.getElementById('themeToggle');
if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
        const icon = themeToggle.querySelector('i');
        if (document.body.classList.contains('dark-theme')) {
            icon.className = 'fas fa-sun';
            localStorage.setItem('theme', 'dark');
        } else {
            icon.className = 'fas fa-moon';
            localStorage.setItem('theme', 'light');
        }
    });
    
    // Загрузить тему
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-theme');
        themeToggle.querySelector('i').className = 'fas fa-sun';
    }
}

// Фильтрация проектов
const filterButtons = document.querySelectorAll('.filter-btn');
const projectCards = document.querySelectorAll('.project-card');

if (filterButtons.length > 0) {
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Удалить активный класс у всех кнопок
            filterButtons.forEach(btn => btn.classList.remove('active'));
            // Добавить активный класс текущей кнопке
            button.classList.add('active');
            
            const filter = button.getAttribute('data-filter');
            
            // Показать/скрыть проекты
            projectCards.forEach(card => {
                if (filter === 'all' || card.getAttribute('data-category').includes(filter)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });
}

// Модальное окно для проектов
const viewButtons = document.querySelectorAll('.view-details');
const modal = document.getElementById('projectModal');
const closeModal = document.querySelector('.close-modal');

if (modal) {
    // Открыть модальное окно
    viewButtons.forEach(button => {
        button.addEventListener('click', () => {
            const projectCard = button.closest('.project-card');
            const title = projectCard.querySelector('h3').textContent;
            const description = projectCard.querySelector('p').textContent;
            
            document.getElementById('modalTitle').textContent = title;
            document.getElementById('modalContent').innerHTML = `
                <p>${description}</p>
                <h3>Технологии:</h3>
                <div class="tech-list">
                    ${projectCard.querySelector('.tech-tags').innerHTML}
                </div>
                <h3>Особенности:</h3>
                <div class="features-list">
                    ${projectCard.querySelector('.project-features').innerHTML}
                </div>
            `;
            
            modal.style.display = 'block';
        });
    });
    
    // Закрыть модальное окно
    if (closeModal) {
        closeModal.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    // Закрыть при клике вне окна
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Обработка формы
const messageForm = document.getElementById('messageForm');
if (messageForm) {
    messageForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitBtn = document.getElementById('submitBtn');
        const formStatus = document.getElementById('formStatus');
        
        // Получить данные формы
        const formData = new FormData(messageForm);
        const data = {
            name: formData.get('name'),
            email: formData.get('email'),
            subject: formData.get('subject'),
            message: formData.get('message')
        };
        
        // Показать загрузку
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Отправка...';
        submitBtn.disabled = true;
        formStatus.innerHTML = '';
        
        try {
            // Отправить на Java сервер
            const response = await fetch('/api/send-message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                formStatus.innerHTML = `
                    <div class="success-message">
                        <i class="fas fa-check-circle"></i> ${result.message}
                    </div>
                `;
                messageForm.reset();
                
                // Обновить счетчик сообщений
                updateMessagesCount();
            } else {
                throw new Error(result.message || 'Ошибка отправки');
            }
        } catch (error) {
            formStatus.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i> ${error.message}
                </div>
            `;
        } finally {
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Отправить сообщение';
            submitBtn.disabled = false;
        }
    });
}

// FAQ аккордеон
const faqQuestions = document.querySelectorAll('.faq-question');
faqQuestions.forEach(question => {
    question.addEventListener('click', () => {
        const answer = question.nextElementSibling;
        const icon = question.querySelector('i');
        
        // Закрыть другие ответы
        document.querySelectorAll('.faq-answer').forEach(otherAnswer => {
            if (otherAnswer !== answer && otherAnswer.style.maxHeight) {
                otherAnswer.style.maxHeight = null;
                otherAnswer.previousElementSibling.querySelector('i').className = 'fas fa-chevron-down';
            }
        });
        
        // Переключить текущий ответ
        if (answer.style.maxHeight) {
            answer.style.maxHeight = null;
            icon.className = 'fas fa-chevron-down';
        } else {
            answer.style.maxHeight = answer.scrollHeight + 'px';
            icon.className = 'fas fa-chevron-up';
        }
    });
});

// Обновить счетчик сообщений
async function updateMessagesCount() {
    try {
        const response = await fetch('/api/messages');
        const data = await response.json();
        
        const messagesCount = document.getElementById('messagesCount');
        if (messagesCount) {
            messagesCount.textContent = data.messages;
        }
    } catch (error) {
        console.error('Не удалось обновить счетчик:', error);
    }
}

// Загрузить счетчик при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    updateMessagesCount();
    
    // Анимация при скролле
    const animateOnScroll = () => {
        const elements = document.querySelectorAll('.skill, .project-card, .stat-card');
        
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementTop < windowHeight - 100) {
                element.classList.add('animate');
            }
        });
    };
    
    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll(); // Запустить сразу
});

// Таймер для счетчика проектов
const projectsCount = document.getElementById('projectsCount');
if (projectsCount) {
    let count = 0;
    const target = 8;
    const increment = target / 50;
    
    const timer = setInterval(() => {
        count += increment;
        projectsCount.textContent = Math.floor(count) + '+';
        
        if (count >= target) {
            clearInterval(timer);
            projectsCount.textContent = target + '+';
        }
    }, 30);
}