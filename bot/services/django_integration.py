"""
Интеграция с Django API для отправки результатов AI теста.
"""

import httpx
from typing import Optional, Dict, Any
from datetime import datetime

from bot.config import settings
from bot.utils.logger import logger


async def send_test_results_to_django(
    telegram_id: int,
    first_name: str,
    last_name: Optional[str],
    username: Optional[str],
    survey_data: Dict[str, Any],
    calculated_kbzu: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Отправляет результаты AI теста в Django API.

    Args:
        telegram_id: ID пользователя в Telegram
        first_name: Имя пользователя
        last_name: Фамилия пользователя (опционально)
        username: Username в Telegram (опционально)
        survey_data: Данные опроса (gender, age, weight, height, activity, goal, etc.)
        calculated_kbzu: Рассчитанные КБЖУ (calories, protein, fat, carbs)

    Returns:
        Dict с результатом сохранения или None при ошибке

    Example survey_data:
        {
            "age": 25,
            "gender": "M",  # или "F"
            "weight_kg": 75,
            "height_cm": 180,
            "activity": "moderately_active",
            "goal": "fat_loss"  # fat_loss, maintenance, muscle_gain
        }

    Example calculated_kbzu:
        {
            "calories": 2100,
            "protein": 130,
            "fat": 70,
            "carbs": 240
        }
    """
    # Получаем URL Django API из настроек
    django_api_url = getattr(settings, 'DJANGO_API_URL', None)

    # Если URL не настроен, логируем и возвращаем None
    if not django_api_url:
        logger.warning("DJANGO_API_URL not configured, skipping Django integration")
        return None

    url = f"{django_api_url}/telegram/save-test/"

    # Маппинг полей бота на формат Django API
    # Bot использует: activity (e.g., "moderately_active"), goal (e.g., "fat_loss")
    # Django ожидает: activity_level, goal

    # Преобразуем данные опроса в формат Django
    answers = {
        "age": survey_data.get("age"),
        "gender": survey_data.get("gender"),
        "weight": float(survey_data.get("weight_kg", 0)),
        "height": int(survey_data.get("height_cm", 0)),
        "activity_level": survey_data.get("activity", "moderately_active"),
        "goal": survey_data.get("goal", "maintenance")
    }

    payload = {
        "telegram_id": telegram_id,
        "first_name": first_name,
        "last_name": last_name or "",
        "username": username or "",
        "answers": answers,
        "calculated_kbzu": calculated_kbzu
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()

            result = response.json()
            logger.info(
                f"✅ Test results saved to Django: "
                f"telegram_id={telegram_id}, user_id={result.get('user_id')}"
            )
            return result

    except httpx.HTTPStatusError as e:
        logger.error(
            f"❌ Django API returned error {e.response.status_code}: "
            f"{e.response.text} for telegram_id={telegram_id}"
        )
        return None
    except httpx.TimeoutException:
        logger.error(
            f"❌ Django API timeout for telegram_id={telegram_id}"
        )
        return None
    except Exception as e:
        logger.error(
            f"❌ Unexpected error sending to Django for telegram_id={telegram_id}: {e}",
            exc_info=True
        )
        return None


def extract_kbzu_from_plan_text(plan_text: str) -> Optional[Dict[str, Any]]:
    """
    Извлекает КБЖУ из текста плана, сгенерированного AI.

    Ищет паттерны вида:
    - Калории: 2100 ккал
    - Белки: 130г
    - Жиры: 70г
    - Углеводы: 240г

    Args:
        plan_text: Текст плана от AI

    Returns:
        Dict с КБЖУ или None если не найдено
    """
    import re

    try:
        # Паттерны для поиска значений
        calories_pattern = r'калори[ийя].*?(\d+)\s*ккал'
        protein_pattern = r'белк[иао].*?(\d+)\s*г'
        fat_pattern = r'жир[ыао].*?(\d+)\s*г'
        carbs_pattern = r'углевод[ыао].*?(\d+)\s*г'

        # Ищем значения (case-insensitive)
        calories_match = re.search(calories_pattern, plan_text, re.IGNORECASE)
        protein_match = re.search(protein_pattern, plan_text, re.IGNORECASE)
        fat_match = re.search(fat_pattern, plan_text, re.IGNORECASE)
        carbs_match = re.search(carbs_pattern, plan_text, re.IGNORECASE)

        # Если нашли все значения, возвращаем
        if all([calories_match, protein_match, fat_match, carbs_match]):
            return {
                "calories": int(calories_match.group(1)),
                "protein": int(protein_match.group(1)),
                "fat": int(fat_match.group(1)),
                "carbs": int(carbs_match.group(1))
            }

        logger.warning("Could not extract all KBZU values from plan text")
        return None

    except Exception as e:
        logger.error(f"Error extracting KBZU from plan: {e}", exc_info=True)
        return None
