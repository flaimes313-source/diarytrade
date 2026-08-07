# services/import.py
import pandas as pd
from database.db import Database
from datetime import datetime

class ImportService:
    @staticmethod
    def import_from_excel(file_content, user_id):
        """Импорт сделок из Excel файла"""
        try:
            df = pd.read_excel(file_content, sheet_name='Шаблон сделок')
            
            imported = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Пропускаем пустые строки
                    if pd.isna(row.get('Монета')):
                        continue
                    
                    # Парсим дату
                    date_str = str(row.get('Дата', ''))
                    if date_str:
                        try:
                            trade_date = datetime.strptime(date_str, '%d.%m.%Y %H:%M')
                        except:
                            trade_date = datetime.now()
                    else:
                        trade_date = datetime.now()
                    
                    # Получаем данные
                    symbol = str(row.get('Монета', '')).upper()
                    direction = str(row.get('Направление', '')).upper()
                    
                    if direction not in ['LONG', 'SHORT']:
                        errors.append(f"Строка {index+2}: Неверное направление '{direction}'")
                        continue
                    
                    position_size = float(row.get('Размер позиции', 0))
                    if position_size <= 0:
                        errors.append(f"Строка {index+2}: Неверный размер позиции")
                        continue
                    
                    entry_price = float(row.get('Цена входа', 0)) if not pd.isna(row.get('Цена входа')) else None
                    exit_price = float(row.get('Цена выхода', 0)) if not pd.isna(row.get('Цена выхода')) else None
                    setup = str(row.get('Сетап', '')) if not pd.isna(row.get('Сетап')) else None
                    confidence = int(row.get('Уверенность', 0)) if not pd.isna(row.get('Уверенность')) else None
                    
                    # Результат
                    result = str(row.get('Результат', '')).lower()
                    if result not in ['profit', 'loss', 'breakeven']:
                        result = None
                    
                    pnl = float(row.get('PnL', 0)) if not pd.isna(row.get('PnL')) else None
                    mistake = str(row.get('Ошибка', '')) if not pd.isna(row.get('Ошибка')) else None
                    
                    # Создаем сделку
                    deposit = Database.get_current_deposit(user_id)
                    
                    trade_id = Database.add_trade(
                        user_id=user_id,
                        symbol=symbol,
                        direction=direction,
                        position_size=position_size,
                        setup=setup,
                        confidence=confidence,
                        deposit=deposit
                    )
                    
                    # Если сделка закрыта, добавляем результаты
                    if result and pnl is not None:
                        Database.close_trade(trade_id, result, pnl, mistake)
                        
                        # Обновляем депозит
                        current_deposit = Database.get_current_deposit(user_id)
                        new_deposit = current_deposit + pnl
                        Database.update_deposit(user_id, new_deposit)
                    
                    imported += 1
                    
                except Exception as e:
                    errors.append(f"Строка {index+2}: {str(e)}")
            
            return imported, errors
            
        except Exception as e:
            return 0, [f"Ошибка чтения файла: {str(e)}"]