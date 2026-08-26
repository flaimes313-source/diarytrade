# database/db.py
from database.models import Session, Trade, User
from datetime import datetime, timedelta
from sqlalchemy import func, and_, BIGINT
import os

class Database:
    @staticmethod
    def get_session():
        return Session()
    
    # ============= USER METHODS =============
    
    @staticmethod
    def get_or_create_user(user_id):
        """Получить пользователя или создать нового"""
        session = Session()
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            user = User(user_id=user_id)
            session.add(user)
            session.commit()
        session.close()
        return user
    
    @staticmethod
    def update_deposit(user_id, deposit):
        """Обновить текущий депозит пользователя"""
        session = Session()
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.current_deposit = deposit
            session.commit()
            print(f"💰 БД: Депозит обновлен на {deposit} для user_id={user_id}")
        else:
            print(f"❌ БД: Пользователь {user_id} не найден!")
        session.close()
    
    @staticmethod
    def get_current_deposit(user_id):
        """Получить текущий депозит пользователя"""
        session = Session()
        user = session.query(User).filter_by(user_id=user_id).first()
        deposit = user.current_deposit if user else 0
        session.close()
        print(f"💰 БД: Текущий депозит = {deposit}")
        return deposit
    
    @staticmethod
    def set_initial_deposit(user_id, deposit):
        """Установить начальный депозит"""
        session = Session()
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.initial_deposit = deposit
            if user.current_deposit == 0:
                user.current_deposit = deposit
            session.commit()
            print(f"💰 БД: Начальный депозит установлен на {deposit}")
        session.close()
    
    @staticmethod
    def get_all_users():
        """Получить всех пользователей"""
        session = Session()
        users = session.query(User).all()
        session.close()
        return users
    
    @staticmethod
    def get_total_users():
        """Получить общее количество пользователей"""
        session = Session()
        count = session.query(User).count()
        session.close()
        return count
    
    # ============= TRADE METHODS =============
    
    @staticmethod
    def add_trade(user_id, symbol, direction, position_size, setup=None, confidence=None, screenshot=None, deposit=None):
        """Добавить новую сделку"""
        session = Session()
        trade = Trade(
            user_id=user_id,
            symbol=symbol,
            direction=direction,
            position_size=position_size,
            setup=setup,
            confidence=confidence,
            screenshot=screenshot,
            deposit=deposit
        )
        session.add(trade)
        session.commit()
        trade_id = trade.id
        session.close()
        print(f"📊 БД: Сделка #{trade_id} добавлена: {symbol} {direction} {position_size}$")
        return trade_id
    
    @staticmethod
    def close_trade(trade_id, result, pnl, mistake=None):
        """Закрыть сделку"""
        session = Session()
        trade = session.query(Trade).filter_by(id=trade_id).first()
        if trade:
            trade.status = 'closed'
            trade.result = result
            trade.pnl = pnl
            trade.close_date = datetime.now()
            if mistake:
                trade.mistake = mistake
            session.commit()
            print(f"📊 БД: Сделка #{trade_id} закрыта: result={result}, pnl={pnl}")
        else:
            print(f"❌ БД: Сделка #{trade_id} не найдена!")
        session.close()
        return trade
    
    @staticmethod
    def get_open_trade(user_id):
        """Получить одну открытую сделку пользователя (устаревший метод)"""
        session = Session()
        trade = session.query(Trade).filter_by(user_id=user_id, status='open').first()
        session.close()
        return trade
    
    @staticmethod
    def get_open_trades(user_id):
        """Получить все открытые сделки пользователя"""
        session = Session()
        trades = session.query(Trade).filter_by(user_id=user_id, status='open').all()
        session.close()
        return trades
    
    @staticmethod
    def get_trade_by_id(trade_id):
        """Получить сделку по ID"""
        session = Session()
        trade = session.query(Trade).filter_by(id=trade_id).first()
        session.close()
        return trade
    
    @staticmethod
    def get_trades(user_id, limit=50):
        """Получить последние сделки пользователя"""
        session = Session()
        trades = session.query(Trade).filter_by(user_id=user_id).order_by(Trade.date.desc()).limit(limit).all()
        session.close()
        return trades
    
    @staticmethod
    def get_all_trades(user_id):
        """Получить все сделки пользователя"""
        session = Session()
        trades = session.query(Trade).filter_by(user_id=user_id).all()
        session.close()
        return trades
    
    @staticmethod
    def delete_trade(trade_id):
        """
        Удалить сделку по ID и пересчитать депозит через сумму PnL всех закрытых сделок.
        Это правильный способ удаления, так как он не зависит от порядка сделок.
        """
        session = Session()
        try:
            trade = session.query(Trade).filter_by(id=trade_id).first()
            if not trade:
                session.close()
                return False
            
            user_id = trade.user_id
            
            # Удаляем сделку
            session.delete(trade)
            session.commit()
            print(f"🗑️ БД: Сделка #{trade_id} удалена")
            
            # Пересчитываем депозит через сумму PnL всех закрытых сделок
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                closed_trades = session.query(Trade).filter_by(user_id=user_id, status='closed').all()
                total_pnl = sum(t.pnl for t in closed_trades if t.pnl is not None)
                new_deposit = user.initial_deposit + total_pnl
                user.current_deposit = new_deposit
                session.commit()
                print(f"💰 БД: Депозит пересчитан: {new_deposit} (initial={user.initial_deposit}, total_pnl={total_pnl})")
            
            session.close()
            return True
            
        except Exception as e:
            session.rollback()
            session.close()
            print(f"❌ БД: Ошибка при удалении сделки: {e}")
            return False
    
    @staticmethod
    def get_trades_by_date_range(user_id, start_date, end_date):
        """Получить сделки за период"""
        session = Session()
        trades = session.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.date >= start_date,
            Trade.date <= end_date
        ).all()
        session.close()
        return trades
    
    @staticmethod
    def get_total_trades():
        """Получить общее количество сделок (всех пользователей)"""
        session = Session()
        count = session.query(Trade).count()
        session.close()
        return count
    
    # ============= STATISTICS METHODS =============
    
    @staticmethod
    def get_stats(user_id):
        """Получить полную статистику по сделкам"""
        session = Session()
        closed_trades = session.query(Trade).filter_by(user_id=user_id, status='closed').all()
        
        total = len(closed_trades)
        wins = sum(1 for t in closed_trades if t.result == 'profit')
        losses = sum(1 for t in closed_trades if t.result == 'loss')
        breakevens = sum(1 for t in closed_trades if t.result == 'breakeven')
        
        total_pnl = sum(t.pnl for t in closed_trades if t.pnl is not None)
        
        profit_trades = [t.pnl for t in closed_trades if t.result == 'profit' and t.pnl is not None]
        loss_trades = [t.pnl for t in closed_trades if t.result == 'loss' and t.pnl is not None]
        
        avg_profit = sum(profit_trades) / len(profit_trades) if profit_trades else 0
        avg_loss = sum(loss_trades) / len(loss_trades) if loss_trades else 0
        
        gross_profit = sum(p for p in profit_trades)
        gross_loss = abs(sum(l for l in loss_trades)) if loss_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in sorted(closed_trades, key=lambda x: x.close_date or x.date):
            if trade.result == 'profit':
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            elif trade.result == 'loss':
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
            else:
                current_wins = 0
                current_losses = 0
        
        session.close()
        
        return {
            'total': total,
            'wins': wins,
            'losses': losses,
            'breakevens': breakevens,
            'win_rate': (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0,
            'total_pnl': total_pnl,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_wins': max_wins,
            'max_losses': max_losses
        }
    
    @staticmethod
    def get_stats_by_setup(user_id):
        """Получить статистику по сетапам"""
        session = Session()
        trades = session.query(Trade).filter_by(user_id=user_id, status='closed').all()
        
        setups = {}
        for trade in trades:
            if trade.setup:
                if trade.setup not in setups:
                    setups[trade.setup] = []
                setups[trade.setup].append(trade)
        
        result = {}
        for setup, trades_list in setups.items():
            total = len(trades_list)
            wins = sum(1 for t in trades_list if t.result == 'profit')
            losses = sum(1 for t in trades_list if t.result == 'loss')
            pnl = sum(t.pnl for t in trades_list if t.pnl is not None)
            
            result[setup] = {
                'total': total,
                'wins': wins,
                'losses': losses,
                'win_rate': (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0,
                'pnl': pnl
            }
        
        session.close()
        return dict(sorted(result.items(), key=lambda x: x[1]['win_rate'], reverse=True))
    
    @staticmethod
    def get_stats_by_month(user_id):
        """Получить статистику по месяцам"""
        session = Session()
        trades = session.query(Trade).filter_by(user_id=user_id, status='closed').all()
        
        months = {}
        for trade in trades:
            month_key = trade.date.strftime('%Y-%m')
            if month_key not in months:
                months[month_key] = []
            months[month_key].append(trade)
        
        result = {}
        for month, trades_list in months.items():
            total = len(trades_list)
            wins = sum(1 for t in trades_list if t.result == 'profit')
            losses = sum(1 for t in trades_list if t.result == 'loss')
            pnl = sum(t.pnl for t in trades_list if t.pnl is not None)
            
            result[month] = {
                'total': total,
                'wins': wins,
                'losses': losses,
                'win_rate': (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0,
                'pnl': pnl
            }
        
        session.close()
        return dict(sorted(result.items()))
    
    @staticmethod
    def get_stats_by_symbol(user_id):
        """Получить статистику по монетам"""
        session = Session()
        trades = session.query(Trade).filter_by(user_id=user_id, status='closed').all()
        
        symbols = {}
        for trade in trades:
            if trade.symbol not in symbols:
                symbols[trade.symbol] = []
            symbols[trade.symbol].append(trade)
        
        result = {}
        for symbol, trades_list in symbols.items():
            pnl = sum(t.pnl for t in trades_list if t.pnl is not None)
            result[symbol] = pnl
        
        session.close()
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
    
    @staticmethod
    def get_deposit_history(user_id):
        """Получить историю депозита (на основе начального депозита + сумма PnL)"""
        session = Session()
        trades = session.query(Trade).filter_by(user_id=user_id).order_by(Trade.date).all()
        
        user = session.query(User).filter_by(user_id=user_id).first()
        initial = user.initial_deposit if user else 0
        
        history = [initial]
        current = initial
        
        for trade in trades:
            if trade.status == 'closed' and trade.pnl is not None:
                current += trade.pnl
                history.append(current)
                print(f"📊 БД: История депозита: {current} (после сделки #{trade.id})")
        
        session.close()
        return history
    
    @staticmethod
    def get_mistakes_stats(user_id):
        """Получить статистику по ошибкам"""
        session = Session()
        trades = session.query(Trade).filter_by(user_id=user_id, status='closed').filter(Trade.mistake.isnot(None)).all()
        
        mistakes = {}
        for trade in trades:
            if trade.mistake:
                if trade.mistake not in mistakes:
                    mistakes[trade.mistake] = {'total': 0, 'losses': 0, 'pnl': 0}
                mistakes[trade.mistake]['total'] += 1
                if trade.result == 'loss':
                    mistakes[trade.mistake]['losses'] += 1
                if trade.pnl:
                    mistakes[trade.mistake]['pnl'] += trade.pnl
        
        session.close()
        return dict(sorted(mistakes.items(), key=lambda x: x[1]['total'], reverse=True))
    
    @staticmethod
    def get_best_setups(user_id, limit=5):
        """Получить ТОП сетапов по Win Rate"""
        setups = Database.get_stats_by_setup(user_id)
        return dict(list(setups.items())[:limit])
    
    @staticmethod
    def get_worst_setups(user_id, limit=5):
        """Получить худшие сетапы по Win Rate"""
        setups = Database.get_stats_by_setup(user_id)
        sorted_setups = sorted(setups.items(), key=lambda x: x[1]['win_rate'])
        return dict(sorted_setups[:limit])
    
    @staticmethod
    def get_today_stats(user_id):
        """Получить статистику за сегодня"""
        today = datetime.now().date()
        start_date = datetime(today.year, today.month, today.day)
        end_date = start_date + timedelta(days=1)
        
        session = Session()
        trades = session.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.status == 'closed',
            Trade.close_date >= start_date,
            Trade.close_date < end_date
        ).all()
        
        total = len(trades)
        wins = sum(1 for t in trades if t.result == 'profit')
        losses = sum(1 for t in trades if t.result == 'loss')
        pnl = sum(t.pnl for t in trades if t.pnl is not None)
        
        session.close()
        
        return {
            'total': total,
            'wins': wins,
            'losses': losses,
            'pnl': pnl,
            'win_rate': (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        }
    
    @staticmethod
    def get_open_trades_all_users():
        """Получить все открытые сделки всех пользователей (для админа)"""
        session = Session()
        trades = session.query(Trade).filter_by(status='open').all()
        session.close()
        return trades
    
    @staticmethod
    def clear_closed_trades(user_id):
        """
        Удалить все закрытые сделки пользователя и пересчитать депозит.
        Открытые сделки не затрагиваются.
        """
        session = Session()
        try:
            closed_trades = session.query(Trade).filter_by(user_id=user_id, status='closed').all()
            deleted_count = len(closed_trades)
            
            for trade in closed_trades:
                session.delete(trade)
            
            # Пересчитываем депозит
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                # Депозит становится равен начальному депозиту
                user.current_deposit = user.initial_deposit
                session.commit()
                print(f"💰 БД: Депозит сброшен до {user.initial_deposit}")
            
            session.commit()
            session.close()
            return deleted_count
        except Exception as e:
            session.rollback()
            session.close()
            print(f"❌ БД: Ошибка очистки статистики: {e}")
            return 0