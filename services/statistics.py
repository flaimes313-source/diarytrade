# services/statistics.py
from database.db import Database

class StatisticsService:
    @staticmethod
    def get_full_stats(user_id):
        stats = Database.get_stats(user_id)
        
        # Добавляем информацию о депозите
        current_deposit = Database.get_current_deposit(user_id)
        user = Database.get_or_create_user(user_id)
        
        return {
            **stats,
            'current_deposit': current_deposit,
            'initial_deposit': user.initial_deposit
        }