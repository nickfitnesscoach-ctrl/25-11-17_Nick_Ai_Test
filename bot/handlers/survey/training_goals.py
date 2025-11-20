"""Хендлеры для уровня тренированности и целей по телу."""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import SurveyStates
from bot.texts.survey import (
    TRAINING_LEVEL_LABELS,
    TRAINING_LEVEL_SAVED,
    BODY_GOALS_LABELS,
    BODY_GOALS_QUESTION,
    BODY_GOALS_SELECTED_TEMPLATE,
    BODY_GOALS_MIN_WARNING,
    BODY_NOW_QUESTION_HEADER,
)
from bot.keyboards import get_body_goals_keyboard
from bot.services.events import log_survey_step_completed
from bot.services.image_sender import image_sender
from .helpers import _safe_delete_message

router = Router(name="survey_training_goals")


def _format_selected_goals(selected: list[str]) -> str:
    if not selected:
        return "ничего не выбрано"
    return ", ".join(BODY_GOALS_LABELS.get(goal, goal) for goal in selected)


@router.callback_query(F.data.startswith("training_level:"), SurveyStates.TRAINING_LEVEL)
async def process_training_level(callback: CallbackQuery, state: FSMContext):
    """Сохраняет уровень тренированности и открывает выбор целей по телу."""
    parts = callback.data.split(":")
    if len(parts) != 2:
        await callback.answer("❌ Некорректные данные", show_alert=True)
        return

    training_level = parts[1]
    if training_level not in TRAINING_LEVEL_LABELS:
        await callback.answer("❌ Некорректный уровень", show_alert=True)
        return

    await state.update_data(training_level=training_level)
    user_id = callback.from_user.id
    log_survey_step_completed(user_id, "TRAINING_LEVEL", {"training_level": training_level})

    await state.set_state(SurveyStates.BODY_GOALS)

    selected_goals = (await state.get_data()).get("body_goals", [])
    selected_text = BODY_GOALS_SELECTED_TEMPLATE.format(
        selected=_format_selected_goals(selected_goals)
    )

    await callback.message.edit_text(
        TRAINING_LEVEL_SAVED.format(label=TRAINING_LEVEL_LABELS[training_level])
        + "\n\n"
        + BODY_GOALS_QUESTION
        + "\n\n"
        + selected_text,
        reply_markup=get_body_goals_keyboard(selected_goals),
        parse_mode="HTML",
    )

    await state.update_data(last_bot_message_id=callback.message.message_id)
    await callback.answer()


@router.callback_query(F.data.startswith("body_goal:"), SurveyStates.BODY_GOALS)
async def toggle_body_goal(callback: CallbackQuery, state: FSMContext):
    """Тоггл целей по телу."""
    parts = callback.data.split(":")
    if len(parts) != 2:
        await callback.answer("❌ Некорректные данные", show_alert=True)
        return

    goal = parts[1]
    if goal not in BODY_GOALS_LABELS:
        await callback.answer("❌ Некорректный вариант", show_alert=True)
        return

    data = await state.get_data()
    selected = set(data.get("body_goals", []))

    if goal in selected:
        selected.remove(goal)
    else:
        selected.add(goal)

    updated_list = list(selected)
    await state.update_data(body_goals=updated_list)

    selected_text = BODY_GOALS_SELECTED_TEMPLATE.format(
        selected=_format_selected_goals(updated_list)
    )

    training_label = TRAINING_LEVEL_LABELS.get(data.get("training_level"), "не указан")
    message_text = TRAINING_LEVEL_SAVED.format(label=training_label)
    message_text += "\n\n" + BODY_GOALS_QUESTION + "\n\n" + selected_text

    await callback.message.edit_text(
        message_text,
        reply_markup=get_body_goals_keyboard(updated_list),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "body_goals:done", SurveyStates.BODY_GOALS)
async def confirm_body_goals(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Фиксирует цели и открывает выбор текущего типа фигуры."""
    data = await state.get_data()
    selected = data.get("body_goals", []) or []

    if not selected:
        await callback.answer(BODY_GOALS_MIN_WARNING, show_alert=True)
        return

    user_id = callback.from_user.id
    log_survey_step_completed(user_id, "BODY_GOALS", {"body_goals": selected})

    await state.set_state(SurveyStates.BODY_NOW)

    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        await _safe_delete_message(bot, callback.message.chat.id, last_msg_id, user_id)
    try:
        await callback.message.delete()
    except Exception:
        pass

    gender = data.get("gender", "female")

    message_ids = await image_sender.send_body_type_options(
        bot=bot,
        chat_id=callback.message.chat.id,
        gender=gender,
        stage="now",
        header_message=BODY_NOW_QUESTION_HEADER,
    )

    await state.update_data(body_now_message_ids=message_ids)
    await callback.answer()
