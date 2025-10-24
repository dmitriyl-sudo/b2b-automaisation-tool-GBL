#!/usr/bin/env python3
"""
Менеджер пользователей для Telegram бота
Хранит список всех пользователей для массовых уведомлений
"""

import json
import os
from typing import Set, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserManager:
    """Класс для управления пользователями бота"""
    
    def __init__(self, users_file: str = "bot_users.json"):
        """
        Инициализация менеджера пользователей
        
        Args:
            users_file: Путь к файлу с пользователями
        """
        self.users_file = users_file
        self.users: Dict[str, Dict[str, Any]] = {}
        self.load_users()
    
    def load_users(self):
        """Загружает пользователей из файла"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
                logger.info(f"✅ Загружено {len(self.users)} пользователей")
            else:
                self.users = {}
                logger.info("📝 Создан новый файл пользователей")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки пользователей: {e}")
            self.users = {}
    
    def save_users(self):
        """Сохраняет пользователей в файл"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
            logger.debug(f"💾 Пользователи сохранены ({len(self.users)} записей)")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения пользователей: {e}")
    
    def add_user(self, user_id: str, username: str = None, first_name: str = None, last_name: str = None):
        """
        Добавляет пользователя в список
        
        Args:
            user_id: ID пользователя в Telegram
            username: Username пользователя
            first_name: Имя пользователя
            last_name: Фамилия пользователя
        """
        user_id_str = str(user_id)
        
        # Проверяем, есть ли уже такой пользователь
        is_new_user = user_id_str not in self.users
        
        # Обновляем информацию о пользователе
        self.users[user_id_str] = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "first_seen": self.users.get(user_id_str, {}).get("first_seen", datetime.now().isoformat()),
            "last_seen": datetime.now().isoformat(),
            "active": True
        }
        
        self.save_users()
        
        if is_new_user:
            logger.info(f"👤 Новый пользователь: {self.get_user_display_name(user_id_str)} ({user_id_str})")
        else:
            logger.debug(f"🔄 Обновлен пользователь: {self.get_user_display_name(user_id_str)}")
    
    def get_user_display_name(self, user_id: str) -> str:
        """
        Возвращает отображаемое имя пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            str: Отображаемое имя
        """
        user = self.users.get(str(user_id), {})
        
        if user.get("username"):
            return f"@{user['username']}"
        elif user.get("first_name"):
            name = user["first_name"]
            if user.get("last_name"):
                name += f" {user['last_name']}"
            return name
        else:
            return f"User {user_id}"
    
    def get_all_active_users(self) -> List[str]:
        """
        Возвращает список всех активных пользователей
        
        Returns:
            List[str]: Список ID пользователей
        """
        return [
            user_id for user_id, user_data in self.users.items()
            if user_data.get("active", True)
        ]
    
    def deactivate_user(self, user_id: str):
        """
        Деактивирует пользователя (не удаляет, но исключает из рассылки)
        
        Args:
            user_id: ID пользователя
        """
        user_id_str = str(user_id)
        if user_id_str in self.users:
            self.users[user_id_str]["active"] = False
            self.save_users()
            logger.info(f"🔇 Пользователь деактивирован: {self.get_user_display_name(user_id_str)}")
    
    def activate_user(self, user_id: str):
        """
        Активирует пользователя
        
        Args:
            user_id: ID пользователя
        """
        user_id_str = str(user_id)
        if user_id_str in self.users:
            self.users[user_id_str]["active"] = True
            self.save_users()
            logger.info(f"🔔 Пользователь активирован: {self.get_user_display_name(user_id_str)}")
    
    def get_users_count(self) -> Dict[str, int]:
        """
        Возвращает статистику пользователей
        
        Returns:
            Dict[str, int]: Статистика
        """
        active_count = len(self.get_all_active_users())
        total_count = len(self.users)
        
        return {
            "total": total_count,
            "active": active_count,
            "inactive": total_count - active_count
        }
    
    def get_users_info(self) -> List[Dict[str, Any]]:
        """
        Возвращает информацию о всех пользователях
        
        Returns:
            List[Dict]: Список пользователей с информацией
        """
        users_info = []
        for user_id, user_data in self.users.items():
            users_info.append({
                "user_id": user_id,
                "display_name": self.get_user_display_name(user_id),
                "username": user_data.get("username"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "first_seen": user_data.get("first_seen"),
                "last_seen": user_data.get("last_seen"),
                "active": user_data.get("active", True)
            })
        
        # Сортируем по последней активности
        users_info.sort(key=lambda x: x["last_seen"], reverse=True)
        return users_info

# Глобальный экземпляр менеджера пользователей
_user_manager: UserManager = None

def get_user_manager() -> UserManager:
    """
    Возвращает глобальный экземпляр менеджера пользователей
    
    Returns:
        UserManager: Экземпляр менеджера
    """
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager

def add_user_from_update(update):
    """
    Добавляет пользователя из Telegram Update
    
    Args:
        update: Telegram Update объект
    """
    if update.effective_user:
        user = update.effective_user
        manager = get_user_manager()
        manager.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

if __name__ == "__main__":
    # Тестирование менеджера пользователей
    manager = UserManager("test_users.json")
    
    # Добавляем тестовых пользователей
    manager.add_user("123456789", "testuser", "Test", "User")
    manager.add_user("987654321", "admin", "Admin", "User")
    
    print("👥 Пользователи:")
    for user_info in manager.get_users_info():
        print(f"  • {user_info['display_name']} ({user_info['user_id']}) - {'✅' if user_info['active'] else '❌'}")
    
    print(f"\n📊 Статистика: {manager.get_users_count()}")
    print(f"📋 Активные пользователи: {manager.get_all_active_users()}")
