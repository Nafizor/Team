import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class Database:
    def __init__(self):
        self.users_file = "users.json"
        self.numbers_file = "numbers.json"
        self.load_data()
    
    def load_data(self):
        """Загружает данные из файлов"""
        # Загружаем пользователей
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r', encoding='utf-8') as f:
                self.users = json.load(f)
        else:
            self.users = {}
        
        # Загружаем номера
        if os.path.exists(self.numbers_file):
            with open(self.numbers_file, 'r', encoding='utf-8') as f:
                self.numbers = json.load(f)
        else:
            self.numbers = {
                'queue': [],  # Общая очередь
                'in_work': {},  # Номера в работе {user_id: [numbers]}
                'successful': {},  # Успешные номера {user_id: [numbers]}
                'blocked': {}  # Заблокированные номера {user_id: [numbers]}
            }
    
    def save_data(self):
        """Сохраняет данные в файлы"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
        
        with open(self.numbers_file, 'w', encoding='utf-8') as f:
            json.dump(self.numbers, f, ensure_ascii=False, indent=2)
    
    def get_or_create_user(self, user_id: int, username: str = None) -> Dict:
        """Получает или создает пользователя"""
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {
                'username': username,
                'reputation': 10,
                'status': 'work 🟢',
                'created_at': datetime.now().isoformat()
            }
            self.save_data()
        return self.users[user_id]
    
    def update_reputation(self, user_id: int, change: float):
        """Обновляет репутацию пользователя"""
        user_id = str(user_id)
        if user_id in self.users:
            self.users[user_id]['reputation'] += change
            self.save_data()
    
    def add_number_to_queue(self, user_id: int, number: str):
        """Добавляет номер в очередь"""
        user_id = str(user_id)
        number_data = {
            'number': number,
            'user_id': user_id,
            'added_at': datetime.now().isoformat(),
            'reputation': self.users.get(user_id, {}).get('reputation', 10)
        }
        self.numbers['queue'].append(number_data)
        # Сортируем по репутации (высокая репутация в начале)
        self.numbers['queue'].sort(key=lambda x: x['reputation'], reverse=True)
        self.save_data()
    
    def get_queue(self) -> List[Dict]:
        """Получает очередь номеров"""
        return self.numbers['queue']
    
    def get_user_numbers_in_queue(self, user_id: int) -> List[Dict]:
        """Получает номера пользователя в очереди"""
        user_id = str(user_id)
        return [num for num in self.numbers['queue'] if num['user_id'] == user_id]
    
    def get_user_numbers_in_work(self, user_id: int) -> List[Dict]:
        """Получает номера пользователя в работе"""
        user_id = str(user_id)
        return self.numbers['in_work'].get(user_id, [])
    
    def get_user_successful_numbers(self, user_id: int) -> List[Dict]:
        """Получает успешные номера пользователя"""
        user_id = str(user_id)
        return self.numbers['successful'].get(user_id, [])
    
    def get_user_blocked_numbers(self, user_id: int) -> List[Dict]:
        """Получает заблокированные номера пользователя"""
        user_id = str(user_id)
        return self.numbers['blocked'].get(user_id, [])
    
    def move_number_to_work(self, number_data: Dict):
        """Перемещает номер в работу"""
        user_id = number_data['user_id']
        if user_id not in self.numbers['in_work']:
            self.numbers['in_work'][user_id] = []
        
        number_data['moved_to_work_at'] = datetime.now().isoformat()
        self.numbers['in_work'][user_id].append(number_data)
        
        # Удаляем из очереди
        self.numbers['queue'] = [num for num in self.numbers['queue'] 
                               if not (num['number'] == number_data['number'] and 
                                     num['user_id'] == number_data['user_id'])]
        self.save_data()
    
    def move_number_to_successful(self, number_data: Dict, flight_time: str):
        """Перемещает номер в успешные"""
        user_id = number_data['user_id']
        if user_id not in self.numbers['successful']:
            self.numbers['successful'][user_id] = []
        
        number_data['flight_time'] = flight_time
        number_data['moved_to_successful_at'] = datetime.now().isoformat()
        self.numbers['successful'][user_id].append(number_data)
        
        # Удаляем из очереди и работы
        self.numbers['queue'] = [num for num in self.numbers['queue'] 
                               if not (num['number'] == number_data['number'] and 
                                     num['user_id'] == number_data['user_id'])]
        
        if user_id in self.numbers['in_work']:
            self.numbers['in_work'][user_id] = [num for num in self.numbers['in_work'][user_id] 
                                               if not (num['number'] == number_data['number'] and 
                                                     num['user_id'] == number_data['user_id'])]
        self.save_data()
    
    def move_number_to_blocked(self, number_data: Dict, flight_time: str):
        """Перемещает номер в заблокированные"""
        user_id = number_data['user_id']
        if user_id not in self.numbers['blocked']:
            self.numbers['blocked'][user_id] = []
        
        number_data['flight_time'] = flight_time
        number_data['moved_to_blocked_at'] = datetime.now().isoformat()
        self.numbers['blocked'][user_id].append(number_data)
        
        # Удаляем из очереди и работы
        self.numbers['queue'] = [num for num in self.numbers['queue'] 
                               if not (num['number'] == number_data['number'] and 
                                     num['user_id'] == number_data['user_id'])]
        
        if user_id in self.numbers['in_work']:
            self.numbers['in_work'][user_id] = [num for num in self.numbers['in_work'][user_id] 
                                               if not (num['number'] == number_data['number'] and 
                                                     num['user_id'] == number_data['user_id'])]
        self.save_data()
    
    def remove_number_from_queue(self, number_data: Dict):
        """Удаляет номер из очереди"""
        self.numbers['queue'] = [num for num in self.numbers['queue'] 
                               if not (num['number'] == number_data['number'] and 
                                     num['user_id'] == number_data['user_id'])]
        self.save_data()
    
    def get_all_users_stats(self) -> List[Dict]:
        """Получает статистику всех пользователей"""
        stats = []
        for user_id, user_data in self.users.items():
            user_stats = {
                'user_id': user_id,
                'username': user_data.get('username', 'Unknown'),
                'reputation': user_data.get('reputation', 10),
                'numbers_in_queue': len(self.get_user_numbers_in_queue(int(user_id))),
                'numbers_in_work': len(self.get_user_numbers_in_work(int(user_id))),
                'successful_numbers': len(self.get_user_successful_numbers(int(user_id))),
                'blocked_numbers': len(self.get_user_blocked_numbers(int(user_id)))
            }
            stats.append(user_stats)
        return stats