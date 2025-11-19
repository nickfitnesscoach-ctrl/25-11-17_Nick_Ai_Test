"""
Хендлеры команд для запуска опроса Personal Plan.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import SurveyStates
from bot.texts.survey import WELCOME_MESSAGE, GENDER_QUESTION
from bot.keyboards import get_start_survey_keyboard, get_gender_keyboard
from bot.services.events import log_survey_started
from bot.utils.logger import logger

router = Router(name="survey_commands")


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start - главная точка входа в бота."""
    user_id = message.from_user.id
    logger.info(f"User {user_id} pressed /start")

    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=get_start_survey_keyboard(),
        parse_mode="HTML",
        disable_notification=True
    )


@router.message(Command("personal_plan"))
async def cmd_personal_plan(message: Message, state: FSMContext):
    """Команда запуска опроса Personal Plan."""
    user_id = message.from_user.id
    logger.info(f"User {user_id} started personal plan survey")

    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=get_start_survey_keyboard(),
        parse_mode="HTML",
        disable_notification=True
    )


@router.callback_query(F.data == "survey:start")
async def start_survey(callback: CallbackQuery, state: FSMContext):
    """Начало опроса после нажатия кнопки."""
    user_id = callback.from_user.id
    log_survey_started(user_id)

    # Очистить старое состояние перед началом нового опроса
    await state.clear()

    await state.set_state(SurveyStates.GENDER)
    await callback.message.edit_text(
        GENDER_QUESTION,
        reply_markup=get_gender_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
