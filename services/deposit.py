# services/deposit.py
"""
Сервис для работы с депозитом пользователя.
Централизованная логика расчета депозита на основе суммы PnL.
"""
from database.db import Database
from database.models import Session, Trade, User

class DepositService:
    
    @staticmethod
    def recalculate_deposit(user_id):
        """
        Пересчитать депозит через сумму PnL всех закрытых сделок.
        Это основной метод расчета депозита.
        """
        session = Session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                print(f"❌ Пользователь {user_id} не найден")
                return None
            
            # Считаем сумму PnL всех закрытых сделок
            closed_trades = session.query(Trade).filter_by(user_id=user_id, status='closed').all()
            total_pnl = sum(t.pnl for t in closed_trades if t.pnl is not None)
            
            # Депозит = начальный депозит + сумма PnL
            new_deposit = user.initial_deposit + total_pnl
            user.current_deposit = new_deposit
            session.commit()
            
            print(f"💰 Пересчет депозита: initial={user.initial_deposit}, total_pnl={total_pnl}, result={new_deposit}")
            session.close()
            return new_deposit
            
        except Exception as e:
            session.rollback()
            session.close()
            print(f"❌ Ошибка пересчета депозита: {e}")
            return None
    
    @staticmethod
    def get_current_deposit(user_id):
        """Получить текущий депозит пользователя"""
        return Database.get_current_deposit(user_id)
    
    @staticmethod
    def set_initial_deposit(user_id, amount):
        """Установить начальный депозит и пересчитать текущий"""
        Database.set_initial_deposit(user_id, amount)
        return DepositService.recalculate_deposit(user_id)
    
    @staticmethod
    def add_pnl_to_deposit(user_id, pnl):
        """
        Добавить PnL к депозиту и пересчитать.
        Используется при закрытии сделки.
        """
        deposit = DepositService.get_current_deposit(user_id)
        new_deposit = deposit + pnl
        Database.update_deposit(user_id, new_deposit)
        return new_deposit
    
    @staticmethod
    def get_deposit_history(user_id):
        """Получить историю изменения депозита"""
        return Database.get_deposit_history(user_id)
    
    @staticmethod
    def get_initial_deposit(user_id):
        """Получить начальный депозит"""
        user = Database.get_or_create_user(user_id)
        return user.initial_deposit
    
    @staticmethod
    def get_deposit_change(user_id):
        """Получить изменение депозита (текущий - начальный)"""
        current = DepositService.get_current_deposit(user_id)
        initial = DepositService.get_initial_deposit(user_id)
        return current - initial