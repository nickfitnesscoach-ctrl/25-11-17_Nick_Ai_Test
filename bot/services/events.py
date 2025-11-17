"""
Сервис для логирования событий в БД (опционально).
"""

from typing import Optional, Dict, Any
from datetime import datetime

from bot.utils.logger import logger


class EventLogger:
    """
    Логирование событий для аналитики.

    На первом этапе - просто логирование в файл.
    В будущем можно добавить запись в БД (таблица events).
    """

    @staticmethod
    def log_event(
        user_id: int,
        event: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Логирует событие пользователя.

        Args:
            user_id: ID пользователя
            event: Название события (например, "survey_started")
            payload: Дополнительные данные
        """
        log_data = {
            "user_id": user_id,
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "payload": payload or {}
        }

        logger.info(f"EVENT: {event} | User: {user_id} | Data: {payload}")

        # TODO: В будущем - запись в таблицу events:
        # async with async_session() as session:
        #     event_record = Event(
        #         user_id=user_id,
        #         event=event,
        #         payload=payload,
        #         ts=datetime.now()
        #     )
        #     session.add(event_record)
        #     await session.commit()


# Глобальный экземпляр
event_logger = EventLogger()


# Хелперы для частых событий
def log_survey_started(user_id: int) -> None:
    """Логирует начало опроса."""
    event_logger.log_event(user_id, "survey_started")


def log_survey_step_completed(user_id: int, step_name: str, data: Optional[Dict] = None) -> None:
    """Логирует завершение шага опроса."""
    event_logger.log_event(
        user_id,
        f"survey_step_completed:{step_name}",
        payload=data
    )


def log_survey_cancelled(user_id: int, last_step: Optional[str] = None) -> None:
    """Логирует отмену опроса."""
    event_logger.log_event(
        user_id,
        "survey_cancelled",
        payload={"last_step": last_step}
    )


def log_survey_completed(user_id: int) -> None:
    """Логирует успешное завершение опроса."""
    event_logger.log_event(user_id, "survey_completed")


def log_plan_generated(user_id: int, model: str, validation_passed: bool) -> None:
    """Логирует генерацию плана."""
    event_logger.log_event(
        user_id,
        "plan_generated",
        payload={"model": model, "validation_passed": validation_passed}
    )


def log_ai_error(user_id: int, error_type: str, error_message: str) -> None:
    """Логирует ошибку при работе с ИИ."""
    event_logger.log_event(
        user_id,
        "ai_error",
        payload={"error_type": error_type, "error_message": error_message}
    )
