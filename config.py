import os

# Загрузка токена из переменных окружения Render
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "ВАШ_ТОКЕН_БОТА_ДЛЯ_ТЕСТОВ")

# Доступные классы
GRADES = [3, 6]

# Доступные предметы
SUBJECTS = ["математика", "русский", "биология", "история"]

# Состояния пользователя
STATE_START = "start"
STATE_GRADE_SELECTED = "grade_selected"
STATE_SUBJECT_SELECTED = "subject_selected"
STATE_ANSWERING = "answering"
STATE_RETRY = "retry"

# Максимум попыток на один вопрос
MAX_ATTEMPTS = 2

# Для Render - создаем папку для данных
if not os.path.exists("users_data"):
    os.makedirs("users_data")