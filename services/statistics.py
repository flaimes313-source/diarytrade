# services/statistics.py
from database.db import Database
from services.deposit import DepositService

class StatisticsService:
    
    @staticmethod
    def get_full_stats(user_id):
        """Получить полную статистику пользователя"""
        stats = Database.get_stats(user_id)
        
        # Используем DepositService для получения данных о депозите
        current_deposit = DepositService.get_current_deposit(user_id)
        initial_deposit = DepositService.get_initial_deposit(user_id)
        
        return {
            **stats,
            'current_deposit': current_deposit,
            'initial_deposit': initial_deposit,
            'deposit_change': current_deposit - initial_deposit
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
        return DepositService.get_deposit_history(user_id)
    
    @staticmethod
    def get_mistakes_stats(user_id):
        """Получить статистику по ошибкам"""
        return Database.get_mistakes_stats(user_id)
    
    @staticmethod
    def get_best_setups(user_id, limit=5):
        """Получить ТОП сетапов по Win Rate"""
        return Database.get_best_setups(user_id, limit)
    
    @staticmethod
    def get_worst_setups(user_id, limit=5):
        """Получить худшие сетапы по Win Rate"""
        return Database.get_worst_setups(user_id, limit)
    
    @staticmethod
    def get_today_stats(user_id):
        """Получить статистику за сегодня"""
        return Database.get_today_stats(user_id)