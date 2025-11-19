"""
Клавиатуры для опроса Personal Plan.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.constants import ACTIVITY_LEVELS, POPULAR_TIMEZONES
from bot.config import settings


def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора пола."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👨 Мужской", callback_data="gender:male"),
        InlineKeyboardButton(text="👩 Женский", callback_data="gender:female")
    )
    return builder.as_markup()


def get_activity_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора уровня активности."""
    builder = InlineKeyboardBuilder()

    for key, data in ACTIVITY_LEVELS.items():
        builder.row(
            InlineKeyboardButton(text=data["label"], callback_data=f"activity:{key}")
        )

    return builder.as_markup()


def get_body_type_keyboard(variant_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура под одной картинкой типа фигуры.

    Args:
        variant_id: ID варианта (1, 2, 3, ...)
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"✅ Выбрать вариант {variant_id}", callback_data=f"body:{variant_id}")
    )
    return builder.as_markup()


def get_body_navigation_keyboard(stage: str) -> InlineKeyboardMarkup:
    """
    Клавиатура навигации после показа всех вариантов тела.

    Args:
        stage: "now" или "ideal"
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Посмотреть ещё раз", callback_data=f"body_review:{stage}")
    )
    return builder.as_markup()


def get_timezone_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора часового пояса."""
    builder = InlineKeyboardBuilder()

    # Популярные часовые пояса (2 в ряд)
    tz_items = list(POPULAR_TIMEZONES.items())
    for i in range(0, len(tz_items), 2):
        row_buttons = []
        for j in range(2):
            if i + j < len(tz_items):
                tz_key, tz_data = tz_items[i + j]
                row_buttons.append(
                    InlineKeyboardButton(
                        text=f"{tz_data['label']} (UTC{tz_data['offset']})",
                        callback_data=f"tz:{tz_key}"
                    )
                )
        builder.row(*row_buttons)

    # Кнопка "Другой..."
    builder.row(
        InlineKeyboardButton(text="✏️ Другой часовой пояс...", callback_data="tz:manual")
    )

    return builder.as_markup()


def get_target_weight_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для шага целевого веса (с возможностью пропустить)."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➡️ Пропустить (поддержание веса)", callback_data="target_weight:skip")
    )
    return builder.as_markup()


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения данных."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Всё верно, продолжить", callback_data="confirm:yes"),
        InlineKeyboardButton(text="✏️ Изменить данные", callback_data="confirm:edit")
    )
    return builder.as_markup()


def get_empty_keyboard() -> InlineKeyboardMarkup:
    """Пустая клавиатура (без кнопок)."""
    builder = InlineKeyboardBuilder()
    return builder.as_markup()


def get_start_survey_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для запуска опроса."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🚀 Начать опрос", callback_data="survey:start")
    )
    return builder.as_markup()


def get_contact_trainer_keyboard(trainer_username: str = None) -> InlineKeyboardMarkup:
    """
    Клавиатура со ссылкой на тренера.

    Args:
        trainer_username: Username тренера в Telegram (без @)
    """
    builder = InlineKeyboardBuilder()

    # Если указан username, создаём прямую ссылку на диалог
    if trainer_username:
        url = f"https://t.me/{trainer_username}"
    else:
        # Использовать username из конфигурации
        url = f"https://t.me/{settings.TRAINER_USERNAME}"

    builder.row(
        InlineKeyboardButton(text="✉️ Написать тренеру", url=url)
    )

    return builder.as_markup()
