# services/deposit.py
from database.db import Database
from database.models import Session, Trade, User
from sqlalchemy import func

class DepositService:
    @staticmethod
    def recalculate(user_id):
        """Пересчитать депозит из истории: initial + SUM(pnl)"""
        session = Session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                return None

            total_pnl = session.query(func.sum(Trade.pnl)).filter(
                Trade.user_id == user_id,
                Trade.status == 'closed'
            ).scalar() or 0.0

            new_current = user.initial_deposit + total_pnl
            user.current_deposit = new_current
            session.commit()
            return new_current
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def get_current(user_id):
        return Database.get_current_deposit(user_id)

    @staticmethod
    def get_initial(user_id):
        user = Database.get_or_create_user(user_id)
        return user.initial_deposit

    @staticmethod
    def set_initial(user_id, amount):
        if amount < 0:
            raise ValueError("Депозит не может быть отрицательным")
        session = Session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                user = User(user_id=user_id)
                session.add(user)
            user.initial_deposit = amount
            session.commit()
            return DepositService.recalculate(user_id)
        finally:
            session.close()

    @staticmethod
    def change_initial(user_id, new_initial):
        """Изменить начальный депозит с пересчётом текущего"""
        return DepositService.set_initial(user_id, new_initial)

    @staticmethod
    def reset_to_initial(user_id):
        """Сбросить current_deposit до initial_deposit без изменения initial"""
        session = Session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.current_deposit = user.initial_deposit
                session.commit()
            return user.current_deposit if user else None
        finally:
            session.close()

    @staticmethod
    def get_total_pnl(user_id):
        session = Session()
        try:
            total = session.query(func.sum(Trade.pnl)).filter(
                Trade.user_id == user_id,
                Trade.status == 'closed'
            ).scalar() or 0.0
            return total
        finally:
            session.close()