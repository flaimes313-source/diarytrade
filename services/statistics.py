# services/statistics.py
from database.db import Database

class StatisticsService:
    @staticmethod
    def get_full_stats(user_id):
        """Получить полную статистику пользователя"""
        stats = Database.get_stats(user_id)
        
        # Добавляем информацию о депозите
        current_deposit = Database.get_current_deposit(user_id)
        user = Database.get_or_create_user(user_id)
        
        return {
            **stats,
            'current_deposit': current_deposit,
            'initial_deposit': user.initial_deposit
        }
    
    @staticmethod
    def get_trade_stats(user_id):
        """Получить статистику по сделкам (упрощенная)"""
        return Database.get_stats(user_id)
    
    @staticmethod
    def get_setup_stats(user_id):
        """Получить статистику по сетапам"""
        return Database.get_stats_by_setup(user_id)
    
    @staticmethod
    def get_monthly_stats(user_id):
        """Получить статистику по месяцам"""
        return Database.get_stats_by_month(user_id)
    
    @staticmethod
    def get_symbol_stats(user_id):
        """Получить статистику по монетам"""
        return Database.get_stats_by_symbol(user_id)
    
    @staticmethod
    def get_deposit_history(user_id):
        """Получить историю депозита"""
        return Database.get_deposit_history(user_id)
    
    @staticmethod
    def get_mistakes_stats(user_id):
        """Получить статистику по ошибкам"""
        return Database.get_mistakes_stats(user_id)