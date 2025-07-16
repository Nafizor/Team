from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import ADMIN_ID

def get_main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Главная клавиатура"""
    keyboard = [
        [
            InlineKeyboardButton("Добавить номер", callback_data="add_number"),
            InlineKeyboardButton("Мои номера", callback_data="my_numbers")
        ],
        [
            InlineKeyboardButton("Очередь", callback_data="queue"),
            InlineKeyboardButton("Обновить", callback_data="refresh")
        ]
    ]
    
    # Добавляем кнопку статистики только для админов
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("Статистика", callback_data="statistics")])
    
    return InlineKeyboardMarkup(keyboard)

def get_my_numbers_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для раздела 'Мои номера'"""
    keyboard = [
        [
            InlineKeyboardButton("В работе", callback_data="numbers_in_work"),
            InlineKeyboardButton("Ожидает", callback_data="numbers_waiting")
        ],
        [
            InlineKeyboardButton("Успешные", callback_data="numbers_successful"),
            InlineKeyboardButton("Блок", callback_data="numbers_blocked")
        ],
        [InlineKeyboardButton("◀ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админ-панели"""
    keyboard = [
        [InlineKeyboardButton("Брать номера из очереди", callback_data="admin_take_numbers")],
        [InlineKeyboardButton("Сообщить о слёте", callback_data="admin_report_flight")],
        [InlineKeyboardButton("◀ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_flight_actions_keyboard(number_data: dict) -> InlineKeyboardMarkup:
    """Клавиатура для действий со слётом"""
    keyboard = [
        [
            InlineKeyboardButton("Слёт", callback_data=f"flight_success_{number_data['number']}_{number_data['user_id']}"),
            InlineKeyboardButton("Блок", callback_data=f"flight_block_{number_data['number']}_{number_data['user_id']}")
        ],
        [InlineKeyboardButton("◀ Назад", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_code_actions_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для действий с кодом"""
    keyboard = [
        [
            InlineKeyboardButton("Скип", callback_data="code_skip"),
            InlineKeyboardButton("Ввел", callback_data="code_entered")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой назад"""
    keyboard = [[InlineKeyboardButton("◀ Назад", callback_data="back_to_main")]]
    return InlineKeyboardMarkup(keyboard)