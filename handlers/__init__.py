# handlers/__init__.py
from .add_trade import router as add_trade_router
from .close_trade import router as close_trade_router
from .stats import router as stats_router
from .history import router as history_router
from .admin import router as admin_router

__all__ = [
    'add_trade_router', 
    'close_trade_router', 
    'stats_router', 
    'history_router',
    'admin_router'
]