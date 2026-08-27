# services/broadcast.py
import asyncio
import logging
from typing import Dict, Any
from aiogram import Bot
from aiogram.types import Chat
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramBadRequest,
    TelegramRetryAfter,
    TelegramNetworkError,
    TelegramAPIError
)
from database.db import Database
from datetime import datetime

logger = logging.getLogger(__name__)

class BroadcastService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self._running = False

    async def send_to_user(self, user_id: int, text: str, photo_path: str = None) -> Dict[str, Any]:
        """Отправить одному пользователю с полной диагностикой"""
        result = {
            'user_id': user_id,
            'status': 'unknown',
            'error': None,
            'attempts': 0
        }

        # Проверка chat доступности
        try:
            chat = await self.bot.get_chat(user_id)
            if not chat:
                result['status'] = 'chat_not_found'
                return result
        except TelegramForbiddenError:
            result['status'] = 'blocked'
            return result
        except TelegramBadRequest as e:
            if 'chat not found' in str(e).lower():
                result['status'] = 'chat_not_found'
            else:
                result['status'] = 'bad_request'
                result['error'] = str(e)
            return result
        except Exception as e:
            result['status'] = 'chat_check_error'
            result['error'] = str(e)
            return result

        # Отправка с ретраями
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            result['attempts'] = attempt
            try:
                if photo_path:
                    await self.bot.send_photo(user_id, photo_path, caption=text, parse_mode="HTML")
                else:
                    await self.bot.send_message(user_id, text, parse_mode="HTML")
                result['status'] = 'ok'
                return result
            except TelegramForbiddenError:
                result['status'] = 'blocked'
                return result
            except TelegramBadRequest as e:
                if 'chat not found' in str(e).lower():
                    result['status'] = 'chat_not_found'
                else:
                    result['status'] = 'bad_request'
                    result['error'] = str(e)
                return result
            except TelegramRetryAfter as e:
                wait = e.retry_after
                logger.warning(f"RetryAfter {wait}s для user {user_id}, попытка {attempt}")
                await asyncio.sleep(wait)
                continue
            except (TelegramNetworkError, TelegramAPIError) as e:
                logger.warning(f"Сетевая ошибка для {user_id}: {e}, попытка {attempt}")
                await asyncio.sleep(1 * attempt)
                continue
            except Exception as e:
                result['status'] = 'unknown_error'
                result['error'] = str(e)
                return result

        result['status'] = 'retry_exhausted'
        return result

    async def broadcast(self, text: str, photo_path: str = None, only_active: bool = True) -> Dict[str, Any]:
        """Основная рассылка с отчётом"""
        if self._running:
            return {'error': 'Рассылка уже запущена'}

        self._running = True
        try:
            users = Database.get_all_users()
            if only_active:
                users = [u for u in users if u.is_active == 1]

            total = len(users)
            report = {
                'total': total,
                'ok': 0,
                'blocked': 0,
                'chat_not_found': 0,
                'bad_request': 0,
                'unknown_error': 0,
                'retry_exhausted': 0,
                'details': []
            }

            for idx, user in enumerate(users, 1):
                result = await self.send_to_user(user.user_id, text, photo_path)
                status = result['status']
                report['details'].append({
                    'user_id': user.user_id,
                    'status': status,
                    'error': result.get('error'),
                    'attempts': result.get('attempts', 1)
                })

                if status == 'ok':
                    report['ok'] += 1
                elif status == 'blocked':
                    report['blocked'] += 1
                    # Помечаем пользователя как неактивного
                    Database.mark_user_blocked(user.user_id)
                elif status == 'chat_not_found':
                    report['chat_not_found'] += 1
                elif status == 'bad_request':
                    report['bad_request'] += 1
                elif status == 'retry_exhausted':
                    report['retry_exhausted'] += 1
                else:
                    report['unknown_error'] += 1

                # Защита от флуда
                if idx % 10 == 0:
                    await asyncio.sleep(0.1)

            return report
        finally:
            self._running = False