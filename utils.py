import re
from datetime import datetime
from typing import List, Dict

def format_main_menu(user_data: Dict, queue_count: int, user_queue_count: int) -> str:
    """Форматирует главное меню"""
    username = user_data.get('username', 'Unknown')
    reputation = user_data.get('reputation', 10)
    status = user_data.get('status', 'work 🟢')
    
    menu = f"""Full Work | {username}
➣Репутация: {reputation}
➢Статус ворка: {status}
╓Общая очередь: {queue_count}
║
╚Твои номера в очереди: {user_queue_count}"""
    
    return menu

def format_numbers_list(numbers: List[Dict], title: str) -> str:
    """Форматирует список номеров"""
    if not numbers:
        return f"{title}\n\nНет номеров"
    
    result = f"{title}\n\n"
    for i, number_data in enumerate(numbers, 1):
        number = number_data['number']
        added_at = datetime.fromisoformat(number_data['added_at']).strftime("%H:%M:%S")
        result += f"{i}. {number} (добавлен: {added_at})\n"
    
    return result

def format_statistics(stats: List[Dict]) -> str:
    """Форматирует статистику"""
    if not stats:
        return "Статистика\n\nНет пользователей"
    
    result = "📊 Статистика пользователей\n\n"
    for user in stats:
        username = user.get('username', 'Unknown')
        reputation = user.get('reputation', 10)
        queue_count = user.get('numbers_in_queue', 0)
        work_count = user.get('numbers_in_work', 0)
        successful_count = user.get('successful_numbers', 0)
        blocked_count = user.get('blocked_numbers', 0)
        
        result += f"👤 {username}\n"
        result += f"   Репутация: {reputation}\n"
        result += f"   В очереди: {queue_count}\n"
        result += f"   В работе: {work_count}\n"
        result += f"   Успешные: {successful_count}\n"
        result += f"   Заблокированные: {blocked_count}\n\n"
    
    return result

def validate_phone_number(number: str) -> bool:
    """Валидирует номер телефона"""
    # Убираем все пробелы и символы
    clean_number = re.sub(r'[\s\-\(\)\+]', '', number)
    
    # Проверяем что это цифры и длина от 10 до 15 символов
    if not clean_number.isdigit():
        return False
    
    if len(clean_number) < 10 or len(clean_number) > 15:
        return False
    
    return True

def format_phone_number(number: str) -> str:
    """Форматирует номер телефона для отображения"""
    # Убираем все пробелы и символы
    clean_number = re.sub(r'[\s\-\(\)\+]', '', number)
    
    # Форматируем номер
    if len(clean_number) == 11 and clean_number.startswith('7'):
        return f"+7 ({clean_number[1:4]}) {clean_number[4:7]}-{clean_number[7:9]}-{clean_number[9:11]}"
    elif len(clean_number) == 10:
        return f"+7 ({clean_number[0:3]}) {clean_number[3:6]}-{clean_number[6:8]}-{clean_number[8:10]}"
    else:
        return clean_number

def format_code_message(number: str, code: str) -> str:
    """Форматирует сообщение с кодом"""
    formatted_number = format_phone_number(number)
    return f"""✆ {formatted_number} ЗАПРОС АКТИВАЦИИ
 ⌨  Ожидай код для входа
 ✎ Ограничение времени активации: 2 минуты
✔ТВОЙ КОД: {code}"""

def format_expired_message(number: str) -> str:
    """Форматирует сообщение об истечении времени"""
    formatted_number = format_phone_number(number)
    return f"""✎ {formatted_number} Время для подтверждения активации истекло. Номер удален из очереди"""

def format_flight_report(number_data: Dict, flight_time: str) -> str:
    """Форматирует отчет о слёте"""
    number = format_phone_number(number_data['number'])
    added_at = datetime.fromisoformat(number_data['added_at']).strftime("%H:%M:%S")
    
    return f"""📊 Отчет о слёте

Номер: {number}
Время принятия: {added_at}
Время слёта: {flight_time}

Выберите действие:"""