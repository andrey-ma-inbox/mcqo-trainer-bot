import random
import json
import os
from datetime import datetime

def get_question(grade, subject, all_questions):
    """Получить случайный вопрос для класса и предмета"""
    try:
        questions = all_questions.get(grade, {}).get(subject, [])
        if not questions:
            return None
        return random.choice(questions)
    except:
        return None

def check_answer(question, user_answer):
    """Проверить ответ пользователя"""
    correct_answer = question.get("answer", "").lower().strip()
    alt_answer = question.get("answer_alt", "").lower().strip()
    user_ans = user_answer.lower().strip()
    
    # Прямое сравнение
    if user_ans == correct_answer:
        return True
    
    # Сравнение с альтернативным ответом
    if alt_answer and user_ans == alt_answer:
        return True
    
    # Для вариантов А, Б, В, Г
    if user_ans.upper() in ['А', 'Б', 'В', 'Г'] and correct_answer.upper() == user_ans.upper():
        return True
    
    # Числовое сравнение с учетом запятых
    try:
        if float(user_ans.replace(',', '.')) == float(correct_answer.replace(',', '.')):
            return True
    except:
        pass
    
    return False

def save_user_stats(user_id, stats_data):
    """Сохранить статистику пользователя"""
    if not os.path.exists("users_data"):
        os.makedirs("users_data")
    
    file_path = f"users_data/{user_id}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, ensure_ascii=False, indent=2)

def load_user_stats(user_id):
    """Загрузить статистику пользователя"""
    file_path = f"users_data/{user_id}.json"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "total_questions": 0,
        "correct_answers": 0,
        "by_subject": {},
        "last_session": None
    }

def update_stats(user_id, subject, is_correct):
    """Обновить статистику"""
    stats = load_user_stats(user_id)
    stats["total_questions"] += 1
    if is_correct:
        stats["correct_answers"] += 1
    
    if subject not in stats["by_subject"]:
        stats["by_subject"][subject] = {"total": 0, "correct": 0}
    
    stats["by_subject"][subject]["total"] += 1
    if is_correct:
        stats["by_subject"][subject]["correct"] += 1
    
    stats["last_session"] = datetime.now().isoformat()
    save_user_stats(user_id, stats)