# keyboards/__init__.py
from .menu import (
    router,
    main_menu,
    stats_menu,
    deposit_menu,
    confirm_reset_deposit_menu,
    direction_keyboard,
    result_keyboard,
    mistake_keyboard,
    add_trade_menu,
    open_trades_menu,
    confirm_delete_menu
)

__all__ = [
    'router',
    'main_menu',
    'stats_menu',
    'deposit_menu',
    'confirm_reset_deposit_menu',
    'direction_keyboard',
    'result_keyboard',
    'mistake_keyboard',
    'add_trade_menu',
    'open_trades_menu',
    'confirm_delete_menu'
]