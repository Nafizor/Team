import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)

from config import BOT_TOKEN, ADMIN_ID, REPUTATION_INCREASE, REPUTATION_DECREASE, CODE_EXPIRATION_TIME
from database import Database
from keyboards import (
    get_main_keyboard, get_my_numbers_keyboard, get_admin_keyboard,
    get_flight_actions_keyboard, get_code_actions_keyboard, get_back_keyboard
)
from utils import (
    format_main_menu, format_numbers_list, format_statistics,
    validate_phone_number, format_code_message, format_expired_message,
    format_flight_report
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_FOR_NUMBER = 1
WAITING_FOR_CODE = 2
WAITING_FOR_FLIGHT_TIME = 3

class TelegramBot:
    def __init__(self):
        self.db = Database()
        self.active_codes = {}  # {user_id: {number: code, message_id: id, timestamp: time}}
        self.admin_states = {}  # {admin_id: {state: data}}
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        user_data = self.db.get_or_create_user(user.id, user.username)
        
        queue_count = len(self.db.get_queue())
        user_queue_count = len(self.db.get_user_numbers_in_queue(user.id))
        
        menu_text = format_main_menu(user_data, queue_count, user_queue_count)
        keyboard = get_main_keyboard(user.id)
        
        await update.message.reply_text(menu_text, reply_markup=keyboard)
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /admin"""
        user = update.effective_user
        if user.id != ADMIN_ID:
            await update.message.reply_text("У вас нет доступа к админ-панели.")
            return
        
        keyboard = get_admin_keyboard()
        await update.message.reply_text("🔧 Админ-панель", reply_markup=keyboard)
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик всех кнопок"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "add_number":
            await self.handle_add_number(query)
        elif data == "my_numbers":
            await self.handle_my_numbers(query)
        elif data == "queue":
            await self.handle_queue(query)
        elif data == "refresh":
            await self.handle_refresh(query)
        elif data == "statistics":
            await self.handle_statistics(query)
        elif data == "back_to_main":
            await self.handle_back_to_main(query)
        elif data.startswith("numbers_"):
            await self.handle_numbers_section(query)
        elif data == "admin_take_numbers":
            await self.handle_admin_take_numbers(query)
        elif data == "admin_report_flight":
            await self.handle_admin_report_flight(query)
        elif data.startswith("flight_"):
            await self.handle_flight_action(query)
        elif data.startswith("code_"):
            await self.handle_code_action(query)
    
    async def handle_add_number(self, query):
        """Обработчик кнопки 'Добавить номер'"""
        await query.edit_message_text(
            "Введите номер телефона:",
            reply_markup=get_back_keyboard()
        )
    
    async def handle_my_numbers(self, query):
        """Обработчик кнопки 'Мои номера'"""
        keyboard = get_my_numbers_keyboard()
        await query.edit_message_text("📱 Мои номера", reply_markup=keyboard)
    
    async def handle_queue(self, query):
        """Обработчик кнопки 'Очередь'"""
        queue = self.db.get_queue()
        count = len(queue)
        await query.edit_message_text(
            f"📊 Общая очередь: {count}",
            reply_markup=get_back_keyboard()
        )
    
    async def handle_refresh(self, query):
        """Обработчик кнопки 'Обновить'"""
        user_id = query.from_user.id
        user_data = self.db.get_or_create_user(user_id, query.from_user.username)
        
        queue_count = len(self.db.get_queue())
        user_queue_count = len(self.db.get_user_numbers_in_queue(user_id))
        
        menu_text = format_main_menu(user_data, queue_count, user_queue_count)
        keyboard = get_main_keyboard(user_id)
        
        await query.edit_message_text(menu_text, reply_markup=keyboard)
    
    async def handle_statistics(self, query):
        """Обработчик кнопки 'Статистика'"""
        if query.from_user.id != ADMIN_ID:
            await query.edit_message_text("У вас нет доступа к статистике.")
            return
        
        stats = self.db.get_all_users_stats()
        stats_text = format_statistics(stats)
        await query.edit_message_text(stats_text, reply_markup=get_back_keyboard())
    
    async def handle_back_to_main(self, query):
        """Обработчик кнопки 'Назад'"""
        user_id = query.from_user.id
        user_data = self.db.get_or_create_user(user_id, query.from_user.username)
        
        queue_count = len(self.db.get_queue())
        user_queue_count = len(self.db.get_user_numbers_in_queue(user_id))
        
        menu_text = format_main_menu(user_data, queue_count, user_queue_count)
        keyboard = get_main_keyboard(user_id)
        
        await query.edit_message_text(menu_text, reply_markup=keyboard)
    
    async def handle_numbers_section(self, query):
        """Обработчик разделов 'Мои номера'"""
        user_id = query.from_user.id
        data = query.data
        
        if data == "numbers_in_work":
            numbers = self.db.get_user_numbers_in_work(user_id)
            text = format_numbers_list(numbers, "🔄 Номера в работе")
        elif data == "numbers_waiting":
            numbers = self.db.get_user_numbers_in_queue(user_id)
            text = format_numbers_list(numbers, "⏳ Номера в ожидании")
        elif data == "numbers_successful":
            numbers = self.db.get_user_successful_numbers(user_id)
            text = format_numbers_list(numbers, "✅ Успешные номера")
        elif data == "numbers_blocked":
            numbers = self.db.get_user_blocked_numbers(user_id)
            text = format_numbers_list(numbers, "🚫 Заблокированные номера")
        
        await query.edit_message_text(text, reply_markup=get_back_keyboard())
    
    async def handle_admin_take_numbers(self, query):
        """Обработчик кнопки 'Брать номера из очереди'"""
        if query.from_user.id != ADMIN_ID:
            await query.edit_message_text("У вас нет доступа к этой функции.")
            return
        
        queue = self.db.get_queue()
        if not queue:
            await query.edit_message_text(
                "Очередь пуста.",
                reply_markup=get_back_keyboard()
            )
            return
        
        # Берем первый номер из очереди (с наивысшей репутацией)
        number_data = queue[0]
        number = number_data['number']
        user_id = int(number_data['user_id'])
        
        # Генерируем код
        import random
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Отправляем код пользователю
        code_message = format_code_message(number, code)
        keyboard = get_code_actions_keyboard()
        
        try:
            message = await query.bot.send_message(
                chat_id=user_id,
                text=code_message,
                reply_markup=keyboard
            )
            
            # Сохраняем информацию о коде
            self.active_codes[user_id] = {
                'number': number,
                'code': code,
                'message_id': message.message_id,
                'timestamp': datetime.now(),
                'number_data': number_data
            }
            
            # Удаляем сообщение через 2 минуты
            asyncio.create_task(self.delete_code_message(user_id, message.message_id))
            
            await query.edit_message_text(
                f"Код {code} отправлен пользователю для номера {number}",
                reply_markup=get_back_keyboard()
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"Ошибка отправки кода: {str(e)}",
                reply_markup=get_back_keyboard()
            )
    
    async def handle_admin_report_flight(self, query):
        """Обработчик кнопки 'Сообщить о слёте'"""
        if query.from_user.id != ADMIN_ID:
            await query.edit_message_text("У вас нет доступа к этой функции.")
            return
        
        queue = self.db.get_queue()
        if not queue:
            await query.edit_message_text(
                "Очередь пуста.",
                reply_markup=get_back_keyboard()
            )
            return
        
        # Показываем список номеров для выбора
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = []
        for i, number_data in enumerate(queue[:10]):  # Показываем первые 10
            number = number_data['number']
            user_id = number_data['user_id']
            keyboard.append([InlineKeyboardButton(
                f"{number} (репутация: {number_data['reputation']})",
                callback_data=f"select_flight_{number}_{user_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("◀ Назад", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Выберите номер для отчета о слёте:",
            reply_markup=reply_markup
        )
    
    async def handle_flight_action(self, query):
        """Обработчик действий со слётом"""
        data = query.data
        
        if data.startswith("select_flight_"):
            # Пользователь выбрал номер для отчета о слёте
            parts = data.split("_")
            number = parts[2]
            user_id = parts[3]
            
            # Находим данные номера
            queue = self.db.get_queue()
            number_data = None
            for num in queue:
                if num['number'] == number and num['user_id'] == user_id:
                    number_data = num
                    break
            
            if not number_data:
                await query.edit_message_text(
                    "Номер не найден в очереди.",
                    reply_markup=get_back_keyboard()
                )
                return
            
            # Сохраняем состояние админа
            self.admin_states[query.from_user.id] = {
                'state': 'waiting_flight_time',
                'number_data': number_data
            }
            
            await query.edit_message_text(
                f"Введите время слёта для номера {number}:",
                reply_markup=get_back_keyboard()
            )
            return WAITING_FOR_FLIGHT_TIME
        
        elif data.startswith("flight_success_"):
            # Админ выбрал "Слёт"
            parts = data.split("_")
            number = parts[2]
            user_id = parts[3]
            
            # Находим данные номера
            queue = self.db.get_queue()
            number_data = None
            for num in queue:
                if num['number'] == number and num['user_id'] == user_id:
                    number_data = num
                    break
            
            if number_data:
                flight_time = self.admin_states.get(query.from_user.id, {}).get('flight_time', 'не указано')
                self.db.move_number_to_successful(number_data, flight_time)
                
                # Уведомляем пользователя
                try:
                    await query.bot.send_message(
                        chat_id=int(user_id),
                        text=f"✅ Номер {number} успешно обработан!"
                    )
                except:
                    pass
                
                await query.edit_message_text(
                    f"Номер {number} перемещен в успешные.",
                    reply_markup=get_back_keyboard()
                )
            else:
                await query.edit_message_text(
                    "Номер не найден в очереди.",
                    reply_markup=get_back_keyboard()
                )
        
        elif data.startswith("flight_block_"):
            # Админ выбрал "Блок"
            parts = data.split("_")
            number = parts[2]
            user_id = parts[3]
            
            # Находим данные номера
            queue = self.db.get_queue()
            number_data = None
            for num in queue:
                if num['number'] == number and num['user_id'] == user_id:
                    number_data = num
                    break
            
            if number_data:
                flight_time = self.admin_states.get(query.from_user.id, {}).get('flight_time', 'не указано')
                self.db.move_number_to_blocked(number_data, flight_time)
                
                # Уведомляем пользователя
                try:
                    await query.bot.send_message(
                        chat_id=int(user_id),
                        text=f"🚫 Номер {number} заблокирован."
                    )
                except:
                    pass
                
                await query.edit_message_text(
                    f"Номер {number} заблокирован.",
                    reply_markup=get_back_keyboard()
                )
            else:
                await query.edit_message_text(
                    "Номер не найден в очереди.",
                    reply_markup=get_back_keyboard()
                )
    
    async def handle_code_action(self, query):
        """Обработчик действий с кодом"""
        user_id = query.from_user.id
        data = query.data
        
        if user_id not in self.active_codes:
            await query.edit_message_text(
                "Код не найден или истек.",
                reply_markup=get_back_keyboard()
            )
            return
        
        code_data = self.active_codes[user_id]
        number_data = code_data['number_data']
        
        if data == "code_skip":
            # Пользователь выбрал "Скип"
            self.db.update_reputation(user_id, -REPUTATION_DECREASE)
            self.db.remove_number_from_queue(number_data)
            
            # Удаляем код из активных
            del self.active_codes[user_id]
            
            await query.edit_message_text(
                "Номер пропущен. Репутация уменьшена.",
                reply_markup=get_back_keyboard()
            )
        
        elif data == "code_entered":
            # Пользователь выбрал "Ввел"
            self.db.update_reputation(user_id, REPUTATION_INCREASE)
            self.db.move_number_to_work(number_data)
            
            # Удаляем код из активных
            del self.active_codes[user_id]
            
            await query.edit_message_text(
                "Номер добавлен в работу. Репутация увеличена.",
                reply_markup=get_back_keyboard()
            )
    
    async def handle_number_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ввода номера"""
        user = update.effective_user
        number = update.message.text.strip()
        
        if not validate_phone_number(number):
            await update.message.reply_text(
                "❌ Неверный формат номера. Попробуйте еще раз:",
                reply_markup=get_back_keyboard()
            )
            return WAITING_FOR_NUMBER
        
        # Добавляем номер в очередь
        self.db.add_number_to_queue(user.id, number)
        
        await update.message.reply_text(
            f"✅ Номер {number} добавлен в очередь!",
            reply_markup=get_back_keyboard()
        )
        
        return ConversationHandler.END
    
    async def handle_flight_time_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ввода времени слёта"""
        user = update.effective_user
        flight_time = update.message.text.strip()
        
        if user.id != ADMIN_ID:
            await update.message.reply_text("У вас нет доступа к этой функции.")
            return ConversationHandler.END
        
        admin_state = self.admin_states.get(user.id, {})
        number_data = admin_state.get('number_data')
        
        if not number_data:
            await update.message.reply_text("Ошибка: данные номера не найдены.")
            return ConversationHandler.END
        
        # Сохраняем время слёта
        self.admin_states[user.id]['flight_time'] = flight_time
        
        # Показываем отчет о слёте
        report_text = format_flight_report(number_data, flight_time)
        keyboard = get_flight_actions_keyboard(number_data)
        
        await update.message.reply_text(report_text, reply_markup=keyboard)
        
        return ConversationHandler.END
    
    async def delete_code_message(self, user_id: int, message_id: int):
        """Удаляет сообщение с кодом через 2 минуты"""
        await asyncio.sleep(CODE_EXPIRATION_TIME)
        
        if user_id in self.active_codes:
            code_data = self.active_codes[user_id]
            number = code_data['number']
            number_data = code_data['number_data']
            
            try:
                # Удаляем сообщение с кодом
                await self.application.bot.delete_message(chat_id=user_id, message_id=message_id)
                
                # Отправляем сообщение об истечении времени
                expired_message = format_expired_message(number)
                await self.application.bot.send_message(chat_id=user_id, text=expired_message)
                
                # Удаляем номер из очереди
                self.db.remove_number_from_queue(number_data)
                
                # Удаляем код из активных
                del self.active_codes[user_id]
                
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщения с кодом: {e}")
    
    def run(self):
        """Запускает бота"""
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        
        # ConversationHandler для добавления номера
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.handle_add_number, pattern="^add_number$")],
            states={
                WAITING_FOR_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_number_input)]
            },
            fallbacks=[CallbackQueryHandler(self.handle_back_to_main, pattern="^back_to_main$")]
        )
        self.application.add_handler(conv_handler)
        
        # ConversationHandler для ввода времени слёта
        flight_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.handle_admin_report_flight, pattern="^admin_report_flight$")],
            states={
                WAITING_FOR_FLIGHT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_flight_time_input)]
            },
            fallbacks=[CallbackQueryHandler(self.handle_back_to_main, pattern="^back_to_main$")]
        )
        self.application.add_handler(flight_conv_handler)
        
        # Обработчик всех остальных кнопок
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Запускаем бота
        self.application.run_polling()

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()