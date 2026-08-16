"""Совместимость со старым именем модуля.

Основная реализация Stars теперь находится в stars_listener.py.
"""

from stars_listener import start_stars_listener, run_stars_listener_forever

__all__ = ["start_stars_listener", "run_stars_listener_forever"]
