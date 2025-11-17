"""
FSM состояния для опроса Personal Plan.
"""

from aiogram.fsm.state import State, StatesGroup


class SurveyStates(StatesGroup):
    """Состояния опроса для Personal Plan."""

    GENDER = State()           # Выбор пола
    AGE = State()              # Ввод возраста
    HEIGHT = State()           # Ввод роста
    WEIGHT = State()           # Ввод веса
    TARGET_WEIGHT = State()    # Целевой вес (опционально)
    ACTIVITY = State()         # Уровень активности
    BODY_NOW = State()         # Текущий тип фигуры
    BODY_IDEAL = State()       # Идеальный тип фигуры
    TZ = State()               # Часовой пояс
    CONFIRM = State()          # Подтверждение данных
    GENERATE = State()         # Генерация плана (технический шаг)
