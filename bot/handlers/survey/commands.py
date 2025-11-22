"""
Хендлеры команд для запуска опроса Personal Plan.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.config import settings
from bot.states import SurveyStates
from bot.texts.survey import WELCOME_MESSAGE, GENDER_QUESTION
from bot.keyboards import (
    get_start_survey_keyboard,
    get_gender_keyboard,
    get_admin_start_keyboard,
    get_open_webapp_keyboard,
    get_admin_panel_open_keyboard,
)
from bot.services.events import log_survey_started
from bot.utils.logger import logger

router = Router(name="survey_commands")


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start - главная точка входа в бота."""
    user_id = message.from_user.id
    logger.info(f"User {user_id} pressed /start")

    # Проверяем, является ли пользователь админом
    if user_id == settings.BOT_ADMIN_ID:
        # Для админа показываем кнопку открытия Mini App
        await message.answer(
            "👋 <b>Привет, Админ!</b>\n\n"
            "📱 <b>Откройте панель тренера</b>, чтобы управлять заявками и клиентами.\n\n"
            "Или начните опрос, если хотите протестировать бота.",
            reply_markup=get_admin_start_keyboard(),
            parse_mode="HTML",
            disable_notification=True
        )
    else:
        # Для обычных пользователей - стандартное приветствие
        await message.answer(
            WELCOME_MESSAGE,
            reply_markup=get_start_survey_keyboard(),
            parse_mode="HTML",
            disable_notification=True
        )


@router.message(Command("app"))
async def cmd_app(message: Message, state: FSMContext):
    """Команда /app - открыть Mini App (для всех пользователей)."""
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested app")

    await message.answer(
        "📱 <b>Откройте приложение</b>\n\n"
        "Нажмите кнопку ниже, чтобы открыть Mini App.",
        reply_markup=get_open_webapp_keyboard(),
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


@router.callback_query(F.data == "admin_panel:open")
async def open_trainer_panel(callback: CallbackQuery):
    """Открытие панели тренера с проверкой прав."""

    user_id = callback.from_user.id

    # Проверяем, что пользователь является админом
    if user_id != settings.BOT_ADMIN_ID:
        await callback.answer("Доступ только для тренера", show_alert=True)
        return

    target_url = settings.ADMIN_WEB_APP_URL or settings.WEB_APP_URL

    if target_url:
        await callback.message.answer(
            "📱 <b>Панель тренера</b>\n\nНажмите кнопку ниже, чтобы открыть админ-интерфейс.",
            reply_markup=get_admin_panel_open_keyboard(),
            parse_mode="HTML",
            disable_notification=True,
        )
    else:
        await callback.message.answer(
            "⚠️ URL панели тренера не настроен. Укажите ADMIN_WEB_APP_URL или WEB_APP_URL в конфигурации.",
            disable_notification=True,
        )

    await callback.answer()
