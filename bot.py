import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import random
import os

from config import TOKEN, GRADES, SUBJECTS, STATE_START, STATE_GRADE_SELECTED, STATE_SUBJECT_SELECTED, STATE_ANSWERING, STATE_RETRY, MAX_ATTEMPTS
from questions import QUESTIONS
from utils import get_question, check_answer, update_stats, load_user_stats

bot = telebot.TeleBot(TOKEN)

# Хранение данных пользователей в памяти
user_data = {}

def get_keyboard_grade():
    """Клавиатура выбора класса"""
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [KeyboardButton(str(g)) for g in GRADES]
    keyboard.add(*buttons)
    keyboard.add(KeyboardButton("❌ Завершить"))
    return keyboard

def get_keyboard_subject():
    """Клавиатура выбора предмета"""
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [KeyboardButton(s.capitalize()) for s in SUBJECTS]
    keyboard.add(*buttons)
    keyboard.add(KeyboardButton("🔙 В начало"), KeyboardButton("❌ Завершить"))
    return keyboard

def get_keyboard_action():
    """Клавиатура действий после ответа"""
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(KeyboardButton("🔄 Следующий вопрос"), KeyboardButton("🔄 Сменить предмет"))
    keyboard.add(KeyboardButton("🏠 В начало"), KeyboardButton("❌ Завершить"))
    return keyboard

def get_keyboard_retry():
    """Клавиатура при неправильном ответе"""
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(KeyboardButton("🔄 Попробовать еще раз"))
    keyboard.add(KeyboardButton("🏠 В начало"), KeyboardButton("❌ Завершить"))
    return keyboard

def send_question(chat_id, user_id):
    """Отправить вопрос пользователю"""
    user = user_data.get(user_id)
    if not user or user["state"] not in [STATE_ANSWERING, STATE_RETRY]:
        return
    
    question = user["current_question"]
    if question:
        text = f"📚 Вопрос №{user['question_num']}\n\n{question['text']}\n\n✏️ Введи свой ответ:"
        bot.send_message(chat_id, text)
    else:
        bot.send_message(chat_id, "😔 К сожалению, для этого класса пока нет задач. Выбери другой класс.", reply_markup=get_keyboard_grade())
        user["state"] = STATE_START

@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    user_data[user_id] = {
        "state": STATE_START,
        "grade": None,
        "subject": None,
        "current_question": None,
        "attempts": 0,
        "question_num": 0
    }
    
    bot.send_message(
        message.chat.id,
        "🏫 *Добро пожаловать в Тренажер МЦКО!*\n\n"
        "Я помогу тебе подготовиться к проверочным работам.\n\n"
        "📌 *Выбери класс:*",
        reply_markup=get_keyboard_grade(),
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Основной обработчик сообщений"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    
    # Проверяем, есть ли пользователь в памяти
    if user_id not in user_data:
        user_data[user_id] = {
            "state": STATE_START,
            "grade": None,
            "subject": None,
            "current_question": None,
            "attempts": 0,
            "question_num": 0
        }
    
    user = user_data[user_id]
    
    # Обработка команд завершения
    if text == "❌ Завершить":
        bot.send_message(chat_id, "👋 До свидания! Чтобы начать заново, нажми /start", reply_markup=telebot.types.ReplyKeyboardRemove())
        if user_id in user_data:
            del user_data[user_id]
        return
    
    # Обработка команды "В начало"
    if text == "🏠 В начало":
        user["state"] = STATE_START
        user["grade"] = None
        user["subject"] = None
        user["current_question"] = None
        user["attempts"] = 0
        user["question_num"] = 0
        bot.send_message(chat_id, "🏠 Возвращаемся в начало. Выбери класс:", reply_markup=get_keyboard_grade())
        return
    
    # Обработка команды "Сменить предмет"
    if text == "🔄 Сменить предмет":
        user["state"] = STATE_GRADE_SELECTED
        bot.send_message(chat_id, f"📚 Класс {user['grade']}\n\nВыбери предмет:", reply_markup=get_keyboard_subject())
        return
    
    # Обработка "Следующий вопрос"
    if text == "🔄 Следующий вопрос" and user["state"] == STATE_RETRY:
        # Загружаем новый вопрос
        questions_list = QUESTIONS.get(user["grade"], {}).get(user["subject"], [])
        if questions_list:
            user["current_question"] = random.choice(questions_list)
            user["attempts"] = 0
            user["question_num"] += 1
            user["state"] = STATE_ANSWERING
            send_question(chat_id, user_id)
        else:
            bot.send_message(chat_id, "😔 Задачи закончились. Измени предмет или класс.", reply_markup=get_keyboard_main())
        return
    
    # Обработка "Попробовать еще раз"
    if text == "🔄 Попробовать еще раз" and user["state"] == STATE_RETRY:
        user["state"] = STATE_ANSWERING
        bot.send_message(chat_id, "Хорошо, попробуй еще раз. 👍\n\nВведи свой ответ:", reply_markup=telebot.types.ReplyKeyboardRemove())
        return
    
    # Обработка статистики
    if text == "📊 Моя статистика":
        stats = load_user_stats(user_id)
        total = stats["total_questions"]
        correct = stats["correct_answers"]
        percent = (correct / total * 100) if total > 0 else 0
        
        stats_text = f"📊 *Твоя статистика:*\n\n"
        stats_text += f"Всего задач: {total}\n"
        stats_text += f"✅ Правильно: {correct}\n"
        stats_text += f"❌ Неправильно: {total - correct}\n"
        stats_text += f"📈 Успеваемость: {percent:.1f}%\n\n"
        
        if stats["by_subject"]:
            stats_text += "*По предметам:*\n"
            for subject, data in stats["by_subject"].items():
                subj_total = data["total"]
                subj_correct = data["correct"]
                subj_percent = (subj_correct / subj_total * 100) if subj_total > 0 else 0
                stats_text += f"• {subject.capitalize()}: {subj_correct}/{subj_total} ({subj_percent:.0f}%)\n"
        
        bot.send_message(chat_id, stats_text, parse_mode='Markdown', reply_markup=get_keyboard_subject())
        return
    
    # СОСТОЯНИЕ: Выбор класса
    if user["state"] == STATE_START:
        if text.isdigit() and int(text) in GRADES:
            user["grade"] = int(text)
            user["state"] = STATE_GRADE_SELECTED
            bot.send_message(
                chat_id,
                f"✅ Выбран {user['grade']} класс\n\n📚 Теперь выбери предмет:",
                reply_markup=get_keyboard_subject()
            )
        else:
            bot.send_message(chat_id, f"❌ Выбери класс из предложенных: {', '.join(map(str, GRADES))}", reply_markup=get_keyboard_grade())
    
    # СОСТОЯНИЕ: Выбор предмета
    elif user["state"] == STATE_GRADE_SELECTED:
        subject_lower = text.lower()
        if subject_lower in SUBJECTS:
            user["subject"] = subject_lower
            user["state"] = STATE_ANSWERING
            user["attempts"] = 0
            user["question_num"] = 0
            
            # Загружаем первый вопрос
            questions_list = QUESTIONS.get(user["grade"], {}).get(user["subject"], [])
            if not questions_list:
                bot.send_message(chat_id, f"😔 Для {user['grade']} класса по предмету '{user['subject']}' пока нет задач. Выбери другой предмет.", reply_markup=get_keyboard_subject())
                user["state"] = STATE_GRADE_SELECTED
                return
            
            user["current_question"] = random.choice(questions_list)
            user["question_num"] += 1
            
            bot.send_message(
                chat_id,
                f"✅ Предмет '{user['subject'].capitalize()}' выбран!\n\n"
                f"🎯 Приступаем к решению.\n"
                f"У тебя {MAX_ATTEMPTS} попытки на каждый вопрос.\n\n"
                f"Поехали! 🚀",
                reply_markup=telebot.types.ReplyKeyboardRemove()
            )
            
            send_question(chat_id, user_id)
        else:
            bot.send_message(chat_id, "❌ Неверный выбор. Выбери предмет из списка:", reply_markup=get_keyboard_subject())
    
    # СОСТОЯНИЕ: Ответ на вопрос
    elif user["state"] == STATE_ANSWERING:
        question = user["current_question"]
        if not question:
            send_question(chat_id, user_id)
            return
        
        is_correct = check_answer(question, text)
        
        if is_correct:
            update_stats(user_id, user["subject"], True)
            bot.send_message(
                chat_id,
                f"✅ *Верно!* 🎉\n\n"
                f"📖 Пояснение: {question.get('explanation', 'Молодец!')}\n\n"
                f"Что дальше?",
                parse_mode='Markdown',
                reply_markup=get_keyboard_action()
            )
            user["state"] = STATE_RETRY
            user["attempts"] = 0
        else:
            user["attempts"] += 1
            
            if user["attempts"] >= MAX_ATTEMPTS:
                update_stats(user_id, user["subject"], False)
                bot.send_message(
                    chat_id,
                    f"❌ *Неверно!*\n\n"
                    f"Правильный ответ: *{question['answer']}*\n"
                    f"📖 Пояснение: {question.get('explanation', 'Будь внимательнее!')}\n\n"
                    f"Что будем делать?",
                    parse_mode='Markdown',
                    reply_markup=get_keyboard_action()
                )
                user["state"] = STATE_RETRY
                user["attempts"] = 0
            else:
                remaining = MAX_ATTEMPTS - user["attempts"]
                bot.send_message(
                    chat_id,
                    f"❌ *Неверно!*\n\n"
                    f"Осталось попыток: {remaining}\n"
                    f"Попробуй еще раз:",
                    parse_mode='Markdown',
                    reply_markup=get_keyboard_retry()
                )
    # СОСТОЯНИЕ: Ожидание действия после ответа
    elif user["state"] == STATE_RETRY:
        if text == "🔄 Следующий вопрос":
            questions_list = QUESTIONS.get(user["grade"], {}).get(user["subject"], [])
            if questions_list:
                user["current_question"] = random.choice(questions_list)
                user["attempts"] = 0
                user["question_num"] += 1
                user["state"] = STATE_ANSWERING
                send_question(chat_id, user_id)
        elif text == "🔄 Сменить предмет":
            user["state"] = STATE_GRADE_SELECTED
            bot.send_message(chat_id, f"📚 Класс {user['grade']}\n\nВыбери предмет:", reply_markup=get_keyboard_subject())
        elif text == "🏠 В начало":
            user["state"] = STATE_START
            user["grade"] = None
            user["subject"] = None
            user["current_question"] = None
            user["attempts"] = 0
            user["question_num"] = 0
            bot.send_message(chat_id, "🏠 В начало. Выбери класс:", reply_markup=get_keyboard_grade())
        else:
            bot.send_message(chat_id, "Пожалуйста, выбери действие из меню:", reply_markup=get_keyboard_action())

# Настройка для работы на Render
import signal
import sys

def signal_handler(sig, frame):
    print("\n🛑 Бот останавливается...")
    bot.stop_polling()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    print("=" * 50)
    print("🏫 Бот 'Тренажер МЦКО' запущен!")
    print("=" * 50)
    print(f"Доступные классы: {GRADES}")
    print(f"Предметы: {SUBJECTS}")
    print("-" * 50)
    total_questions = 0
    for grade in [3, 6]:
        for subject in SUBJECTS:
            count = len(QUESTIONS[grade][subject])
            total_questions += count
            print(f"{grade} класс - {subject}: {count} вопросов")
    print("-" * 50)
    print(f"ВСЕГО ВОПРОСОВ: {total_questions}")
    print("=" * 50)
    print("Нажми Ctrl+C для остановки")
    bot.infinity_polling()