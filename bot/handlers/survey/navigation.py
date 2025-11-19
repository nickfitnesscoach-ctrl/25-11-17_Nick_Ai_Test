"""
Хендлеры навигации в опросе Personal Plan.
Включает: отмена опроса, возврат к предыдущему шагу.
"""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import SurveyStates
from bot.texts.survey import (
    SURVEY_CANCELLED, GENDER_QUESTION, AGE_QUESTION, HEIGHT_QUESTION,
    WEIGHT_QUESTION, TARGET_WEIGHT_QUESTION, ACTIVITY_QUESTION, TZ_QUESTION,
    BODY_NOW_QUESTION_HEADER, BODY_IDEAL_QUESTION_HEADER
)
from bot.keyboards import (
    get_gender_keyboard, get_target_weight_keyboard, get_activity_keyboard,
    get_timezone_keyboard
)
from bot.services.image_sender import image_sender
from bot.services.events import log_survey_cancelled

router = Router(name="survey_navigation")


@router.callback_query(F.data == "survey:cancel")
async def cancel_survey(callback: CallbackQuery, state: FSMContext):
    """Отмена опроса."""
    user_id = callback.from_user.id
    current_state = await state.get_state()
    log_survey_cancelled(user_id, current_state)

    await state.clear()
    await callback.message.edit_text(SURVEY_CANCELLED, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "survey:back")
async def go_back(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Универсальный обработчик кнопки 'Назад' для всех шагов опроса."""
    current_state = await state.get_state()

    # Маппинг: текущее состояние -> предыдущее состояние
    back_mapping = {
        SurveyStates.AGE: (SurveyStates.GENDER, GENDER_QUESTION, get_gender_keyboard),
        SurveyStates.HEIGHT: (SurveyStates.AGE, AGE_QUESTION, None),
        SurveyStates.WEIGHT: (SurveyStates.HEIGHT, HEIGHT_QUESTION, None),
        SurveyStates.TARGET_WEIGHT: (SurveyStates.WEIGHT, WEIGHT_QUESTION, None),
        SurveyStates.ACTIVITY: (SurveyStates.TARGET_WEIGHT, TARGET_WEIGHT_QUESTION, get_target_weight_keyboard),
        SurveyStates.BODY_NOW: (SurveyStates.ACTIVITY, ACTIVITY_QUESTION, get_activity_keyboard),
        SurveyStates.BODY_IDEAL: (SurveyStates.BODY_NOW, None, None),
        SurveyStates.TZ: (SurveyStates.BODY_IDEAL, None, None),
        SurveyStates.CONFIRM: (SurveyStates.TZ, TZ_QUESTION, get_timezone_keyboard),
    }

    if current_state not in back_mapping:
        await callback.answer()
        return

    prev_state, question_text, keyboard_func = back_mapping[current_state]

    # Удаляем только текущее сообщение с кнопками
    try:
        await callback.message.delete()
    except Exception:
        pass  # Игнорируем ошибки удаления

    # Специальная обработка для BODY_NOW (нужно показать изображения)
    if current_state == SurveyStates.BODY_IDEAL:
        data = await state.get_data()
        gender = data.get("gender", "female")

        await state.set_state(SurveyStates.BODY_NOW)
        await callback.answer()

        message_ids = await image_sender.send_body_type_options(
            bot=bot,
            chat_id=callback.message.chat.id,
            gender=gender,
            stage="now",
            header_message=BODY_NOW_QUESTION_HEADER
        )

        if message_ids:
            await state.update_data(body_now_message_ids=message_ids)
        return

    # Специальная обработка для TZ (нужно показать изображения для BODY_IDEAL)
    if current_state == SurveyStates.TZ:
        data = await state.get_data()
        gender = data.get("gender", "female")

        await state.set_state(SurveyStates.BODY_IDEAL)
        await callback.answer()

        message_ids = await image_sender.send_body_type_options(
            bot=bot,
            chat_id=callback.message.chat.id,
            gender=gender,
            stage="ideal",
            header_message=BODY_IDEAL_QUESTION_HEADER
        )

        if message_ids:
            await state.update_data(body_ideal_message_ids=message_ids)
        return

    # Стандартная обработка для остальных шагов
    await state.set_state(prev_state)
    await callback.answer()

    keyboard = keyboard_func() if keyboard_func else None

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=question_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
