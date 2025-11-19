"""
Хендлер выбора уровня активности в опросе Personal Plan.
"""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import SurveyStates
from bot.texts.survey import BODY_NOW_QUESTION_HEADER
from bot.services.image_sender import image_sender
from bot.services.events import log_survey_step_completed
from bot.utils.logger import logger

router = Router(name="survey_activity")


@router.callback_query(F.data.startswith("activity:"), SurveyStates.ACTIVITY)
async def process_activity(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обработка выбора уровня активности."""
    parts = callback.data.split(":")
    if len(parts) != 2:
        await callback.answer("❌ Некорректные данные", show_alert=True)
        logger.warning(f"Invalid activity callback_data: {callback.data}")
        return

    activity = parts[1]
    # Validate activity value against known options
    valid_activities = ["sedentary", "light", "moderate", "active", "very_active"]
    if activity not in valid_activities:
        await callback.answer("❌ Некорректный уровень активности", show_alert=True)
        logger.warning(f"Invalid activity value: {activity}")
        return

    await state.update_data(activity=activity)

    user_id = callback.from_user.id
    log_survey_step_completed(user_id, "ACTIVITY", {"activity": activity})

    # Переход к следующему шагу - BODY_NOW (показ изображений)
    await state.set_state(SurveyStates.BODY_NOW)
    await callback.answer()

    # Получить данные для удаления предыдущего сообщения
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")

    # Удаляем предыдущее сообщение бота (подтверждение целевого веса)
    try:
        if last_msg_id:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=last_msg_id)
    except Exception:
        pass

    # Удаляем сообщение с вопросом об активности
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Получить пол для показа правильных изображений
    gender = data.get("gender", "female")

    # Отправить изображения вариантов типов фигуры
    message_ids = await image_sender.send_body_type_options(
        bot=bot,
        chat_id=callback.message.chat.id,
        gender=gender,
        stage="now",
        header_message=BODY_NOW_QUESTION_HEADER
    )

    # Сохранить message_ids для последующего удаления
    await state.update_data(body_now_message_ids=message_ids)
