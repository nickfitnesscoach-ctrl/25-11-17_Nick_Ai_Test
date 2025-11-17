"""
Клавиатуры бота.
"""

from .survey import (
    get_gender_keyboard,
    get_activity_keyboard,
    get_body_type_keyboard,
    get_body_navigation_keyboard,
    get_timezone_keyboard,
    get_target_weight_keyboard,
    get_confirmation_keyboard,
    get_back_cancel_keyboard,
    get_start_survey_keyboard,
)

__all__ = [
    "get_gender_keyboard",
    "get_activity_keyboard",
    "get_body_type_keyboard",
    "get_body_navigation_keyboard",
    "get_timezone_keyboard",
    "get_target_weight_keyboard",
    "get_confirmation_keyboard",
    "get_back_cancel_keyboard",
    "get_start_survey_keyboard",
]
