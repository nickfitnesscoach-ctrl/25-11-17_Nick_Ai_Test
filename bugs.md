# Bugs & Tech Debt — FoodMind Bot

**Generated:** 2025-11-17
**Last Updated:** 2025-11-19
**Project:** AI Lead Magnet Bot (Telegram Bot for Personal Nutrition Plans)
**Framework:** aiogram 3.x, SQLAlchemy async, PostgreSQL, OpenRouter AI

---

## 📊 Общий прогресс: 53% (18/34 задач)

### Статус по приоритетам:
- ✅ **P1 (Critical):** 5/5 FIXED (100%) - Production-ready
- ✅ **P2 (High):** 6/10 FIXED (60%) - В процессе
- 🔴 **P3 (Medium):** 5/14 FIXED (36%) - В процессе
- 🔴 **P4 (Low):** 2/5 FIXED (40%) - Частично

### Последние изменения (2025-11-19):
**Коммит 079e323** - Fix high priority bugs (P2): 6 багов
- ✅ BUG-2025-010: Trainer username в конфиг
- ✅ BUG-2025-011: Rate limiting (защита от abuse)
- ✅ BUG-2025-012: HTTP-Referer в конфиг
- ✅ BUG-2025-013: Улучшенная валидация AI
- ✅ BUG-2025-014: Обработка ошибок Telegram API
- ✅ BUG-2025-015: Проверка изображений на старте

**Коммит 2e15c5e** - Fix P3 bugs: 5 багов
- ✅ BUG-2025-021: Рефакторинг удаления сообщений
- ✅ BUG-2025-022: SQLAlchemy relationships
- ✅ BUG-2025-023: Индекс на created_at
- ✅ BUG-2025-025: Упрощение валидации
- ✅ BUG-2025-033, 034: Dead code cleanup

### Следующие шаги:
1. **Приоритет:** Завершить оставшиеся P2 баги (4 задачи)
2. **Затем:** P3 архитектурные улучшения

---

## 🎉 Critical Bugs Fixed (P1) - 2025-11-17

All 5 critical P1 bugs have been successfully fixed with comprehensive test coverage:

✅ **BUG-2025-001**: KeyError при парсинге callback_data - Added validation in all callback handlers
✅ **BUG-2025-002**: AttributeError при отсутствии from_user - Added None-safe checks
✅ **BUG-2025-003**: DB exceptions при сохранении плана - Wrapped DB operations in try-except
✅ **BUG-2025-004**: Timeout без обновлений - Added progress updates every 10 seconds
✅ **BUG-2025-005**: Race condition на подтверждении - Added state-based locking

**Test Coverage:** 12 unit tests created in `tests/test_critical_bugs.py`
**Test Results:** 12/12 passing (0.82s execution time)
**Files Modified:** `bot/handlers/personal_plan.py`
**Status:** Production-ready ✅

**Test Command:**
```bash
pytest tests/test_critical_bugs.py -v
```

---

## Legend

**Severity:**
- **P1** — Critical: может ломать бота/сервер, приводить к крэшам, потере данных
- **P2** — High: важно, влияет на стабильность/деньги/данные пользователей
- **P3** — Medium: техдолг, снижает поддержку/скорость разработки
- **P4** — Low: косметика, стиль, нейминг, мелкие улучшения

**Tags:** BUG, HARDCODE, DEAD_CODE, DUPLICATION, CONFIG, INTEGRATION, ARCH, TESTS, SECURITY

---

## Project Map

### Структура проекта

```
bot/
├── __main__.py              # Точка входа (dp.start_polling)
├── config.py                # Конфигурация (Pydantic Settings)
├── handlers/
│   ├── __init__.py          # Регистрация хендлеров
│   └── personal_plan.py     # ОСНОВНОЙ ФАЙЛ (856 строк, весь опрос)
├── states/
│   └── survey.py            # FSM состояния
├── keyboards/
│   └── survey.py            # Inline клавиатуры
├── validators/
│   ├── survey.py            # Валидация ввода пользователя
│   └── ai_response.py       # Валидация ответа AI
├── services/
│   ├── ai/
│   │   └── openrouter.py    # HTTP-клиент к OpenRouter API
│   ├── database/
│   │   ├── session.py       # Async SQLAlchemy engine & session
│   │   └── repository.py    # CRUD для User, Survey, Plan
│   ├── image_sender.py      # Отправка изображений body types
│   └── events.py            # Логирование событий (файловое)
├── models/
│   ├── base.py              # Base, TimestampMixin
│   ├── user.py              # User model
│   └── survey.py            # SurveyAnswer, Plan models
├── prompts/
│   └── personal_plan.py     # AI промпты (system + user message)
├── texts/
│   └── survey.py            # Тексты для пользователя (русский)
├── constants/
│   └── survey.py            # Константы (BODY_LABELS, ACTIVITY_LEVELS, etc)
└── utils/
    ├── logger.py            # Логирование (RotatingFileHandler)
    └── paths.py             # Утилиты для путей к assets/

alembic/
└── versions/
    └── 6aa0ade7a7c0_create_survey_tables.py  # Миграция (users, survey_answers, plans)

assets/body_types/           # Изображения типов фигуры (NOT IN REPO)
├── female/now/              # female_now_1.jpg ... female_now_5.jpg
├── female/ideal/            # female_ideal_1.jpg ... female_ideal_3.jpg
├── male/now/                # male_now_1.jpg ... male_now_4.jpg
└── male/ideal/              # male_ideal_1.jpg ... male_ideal_3.jpg
```

### Точки входа и критичные модули

1. **Точка входа:** `bot/__main__.py` → `main()` → `dp.start_polling(bot)`
2. **Регистрация хендлеров:** `bot/handlers/__init__.py:register_all_handlers()`
3. **Единственный роутер:** `bot/handlers/personal_plan.py` (856 строк, ВСЕ хендлеры опроса)
4. **AI интеграция:** `bot/services/ai/openrouter.py:OpenRouterClient.generate_plan()`
5. **БД:** `bot/services/database/session.py` (async engine + session maker)
6. **Конфигурация:** `bot/config.py` (Pydantic Settings, .env)

### Где будет болеть при изменениях

- **bot/handlers/personal_plan.py** — монолит с 19 хендлерами (командами/коллбеками), изменение логики одного шага может сломать навигацию назад
- **bot/services/ai/openrouter.py** — одна точка интеграции с внешним API (OpenRouter), нет circuit breaker, ретраев только на уровне HTTP
- **bot/constants/survey.py** — множество хардкода констант, изменение структуры body types требует изменения в 4+ местах
- **bot/validators/survey.py** — валидация данных, но нет глобального try-except на хендлерах → некорректный ввод может пропустить
- **bot/models/** — связи relationships закомментированы, что может затруднить ORM-запросы с join
- **assets/body_types/** — файлы НЕ в репо, отсутствие изображений = fallback сообщения, но нет проверки на старте бота

---

## 1. Критичные баги (P1) ✅ FIXED

### BUG-2025-001: KeyError при парсинге callback_data без валидации ✅ FIXED

- **Severity:** P1
- **Tags:** BUG, RUNTIME
- **Status:** ✅ FIXED (2025-11-17)
- **Files:**
  - `bot/handlers/personal_plan.py:89` (process_gender)
  - `bot/handlers/personal_plan.py:358` (process_activity)
  - `bot/handlers/personal_plan.py:408` (process_body_now)
  - `bot/handlers/personal_plan.py:456` (process_body_ideal)
  - `bot/handlers/personal_plan.py:499` (process_tz_button)
- **Tests:** `tests/test_critical_bugs.py::test_process_gender_invalid_callback_data_*`

**Описание:**
Во всех хендлерах коллбэков используется `.split(":")` для парсинга `callback_data`, но нет проверки на количество элементов в результате. Если пользователь отправит некорректную callback_data (или злонамеренно подделает), бот упадёт с `IndexError`.

**Steps to Reproduce:**
1. Модифицировать callback_data вручную через Telegram API или кастомный клиент
2. Отправить коллбэк с данными `"gender"` (без двоеточия) или `"gender:male:extra"`
3. Бот упадёт с `IndexError: list index out of range` на строке `callback.data.split(":")[1]`

**Expected:**
Хендлер должен игнорировать некорректные callback_data или отправлять пользователю сообщение об ошибке.

**Actual:**
Бот крэшится, пользователь видит "что-то пошло не так" (если есть глобальный error handler).

**Logs:**
```python
IndexError: list index out of range
  File "bot/handlers/personal_plan.py", line 89, in process_gender
    gender = callback.data.split(":")[1]
```

**Suspected Root Cause:**
Отсутствие валидации входных данных из callback_query.

**Fix Applied:**
```python
# bot/handlers/personal_plan.py:89
@router.callback_query(F.data.startswith("gender:"), SurveyStates.GENDER)
async def process_gender(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    if len(parts) != 2 or parts[1] not in ["male", "female"]:
        await callback.answer("❌ Некорректные данные", show_alert=True)
        logger.warning(f"Invalid gender callback_data: {callback.data}")
        return

    gender = parts[1]
    # ... rest of logic
```

**Fix Details:**
- Added validation in all 5 callback handlers (gender, activity, body_now, body_ideal, tz)
- Each handler validates parts length and value correctness
- Invalid data triggers user-friendly error message and logging
- Handlers return early on validation failure

---

### BUG-2025-002: Потенциальный AttributeError при отсутствии callback.from_user ✅ FIXED

- **Severity:** P1
- **Tags:** BUG, RUNTIME
- **Status:** ✅ FIXED (2025-11-17)
- **Files:**
  - `bot/handlers/personal_plan.py:611-615` (early from_user check)
  - `bot/handlers/personal_plan.py:689-690` (None-safe attribute access)
- **Tests:** `tests/test_critical_bugs.py::test_confirm_and_generate_missing_from_user`

**Описание:**
В хендлере `confirm_and_generate` используется `callback.from_user.id`, `callback.from_user.username` и `callback.from_user.full_name` без проверки на None. Если пользователь удалён из Telegram или callback пришёл от бота (что технически возможно), это приведёт к `AttributeError`.

**Steps to Reproduce:**
1. Пользователь удаляет свой аккаунт Telegram ПОСЛЕ начала опроса, но ДО нажатия кнопки "Всё верно, продолжить"
2. Callback приходит, но `callback.from_user` может быть None или с минимальными данными

**Expected:**
Обработка случая, когда `username` или `full_name` отсутствуют.

**Actual:**
Бот падает с `AttributeError`.

**Suspected Root Cause:**
Отсутствие проверки на None для полей Telegram User.

**Fix Applied:**
```python
# bot/handlers/personal_plan.py:611-615 (Early validation)
if not callback.from_user:
    logger.error("Callback received without from_user")
    await callback.answer("❌ Ошибка: данные пользователя недоступны", show_alert=True)
    return

user_id = callback.from_user.id

# bot/handlers/personal_plan.py:689-690 (Defense in depth)
user = await UserRepository.get_or_create(
    session,
    tg_id=user_id,
    username=callback.from_user.username if callback.from_user else None,
    full_name=callback.from_user.full_name if callback.from_user else None
)
```

**Fix Details:**
- Added early validation check at function start - returns immediately if from_user is None
- Shows user-friendly error message to user
- Added None-safe checks for username/full_name as defense-in-depth
- Prevents AttributeError at multiple points in the code

---

### BUG-2025-003: Unhandled exception при недоступности БД во время сохранения плана ✅ FIXED

- **Severity:** P1
- **Tags:** BUG, RUNTIME, DB
- **Status:** ✅ FIXED (2025-11-17)
- **Files:**
  - `bot/handlers/personal_plan.py:683-708` (confirm_and_generate)
- **Tests:** `tests/test_critical_bugs.py::test_confirm_and_generate_db_failure_after_ai_generation`

**Описание:**
Блок сохранения в БД (создание User, Survey, Plan) НЕ обёрнут в `try-except` для обработки ошибок подключения к БД. Если PostgreSQL недоступен в этот момент, план уже сгенерирован AI (деньги потрачены), но НЕ сохранён → пользователь видит ошибку, план потерян.

**Steps to Reproduce:**
1. Завершить опрос, нажать "Всё верно, продолжить"
2. AI генерирует план (успешно, 5-10 сек)
3. В момент сохранения в БД PostgreSQL падает или недоступен
4. `asyncpg.exceptions.ConnectionDoesNotExistError` или `sqlalchemy.exc.OperationalError`
5. Пользователь видит `PLAN_GENERATION_ERROR`, но план УЖЕ был сгенерирован

**Expected:**
- Логировать текст плана перед сохранением в БД
- В случае ошибки БД: отправить план пользователю, но с предупреждением "не сохранён в БД"
- Попытка ретрая сохранения или сохранение в fallback-storage (Redis, файл)

**Actual:**
План потерян, пользователь видит общую ошибку, деньги на AI потрачены впустую.

**Logs:**
```python
sqlalchemy.exc.OperationalError: (asyncpg.exceptions.ConnectionDoesNotExistError)
  File "bot/handlers/personal_plan.py", line 683, in confirm_and_generate
    async with async_session_maker() as session:
```

**Suspected Root Cause:**
Отсутствие обработки DB exceptions в критичной части.

**Fix Applied:**
```python
# bot/handlers/personal_plan.py:730-772
try:
    async with async_session_maker() as session:
        user = await UserRepository.get_or_create(...)
        survey = await SurveyRepository.create_survey_answer(...)
        plan = await PlanRepository.create_plan(...)
    log_survey_completed(user_id)
    log_plan_generated(user_id, ai_model, validation_passed=validation["valid"])
except Exception as db_error:
    logger.critical(f"DB save failed after AI generation for user {user_id}: {db_error}", exc_info=True)
    await callback.message.answer(
        f"⚠️ <b>План сгенерирован, но не сохранён в базе данных</b>\n\n"
        f"Пожалуйста, сохраните текст плана:\n\n{ai_text}\n\n"
        f"Обратитесь к администратору для восстановления данных.",
        parse_mode="HTML", disable_notification=True
    )
    await state.clear()
    return
```

**Fix Details:**
- Wrapped entire DB save block in try-except
- On DB failure, sends AI-generated plan to user with warning
- Logs critical error for manual recovery
- Prevents loss of expensive AI-generated content

---

### BUG-2025-004: HTTP timeout на AI request может зависнуть пользователя ✅ FIXED

- **Severity:** P1
- **Tags:** BUG, INTEGRATION, TIMEOUT
- **Status:** ✅ FIXED (2025-11-17)
- **Files:**
  - `bot/handlers/personal_plan.py:671-688` (confirm_and_generate - progress updates)

**Описание:**
Таймаут установлен в 30 секунд (`OPENROUTER_TIMEOUT=30`). Если OpenRouter API не отвечает или медленно генерирует, пользователь будет ждать 30 секунд БЕЗ уведомлений, после чего увидит ошибку. Telegram polling может упасть, если запрос затягивается.

**Steps to Reproduce:**
1. Завершить опрос
2. OpenRouter API медленно отвечает (>25 сек)
3. Пользователь видит сообщение "Генерирую план..." и ничего не происходит 30 секунд
4. Затем приходит ошибка `PLAN_GENERATION_ERROR`

**Expected:**
- Промежуточные уведомления каждые 10 секунд ("Всё ещё генерирую...")
- Более агрессивный таймаут (15 сек) с ретраем
- Circuit breaker для OpenRouter API

**Actual:**
Пользователь в подвешенном состоянии 30 секунд.

**Suspected Root Cause:**
Фиксированный таймаут 30 сек без промежуточных обновлений.

**Fix Applied:**
```python
# bot/handlers/personal_plan.py:671-688
async def send_progress_updates():
    """Отправляет промежуточные обновления о прогрессе генерации."""
    for i in range(1, 4):  # 3 обновления: через 10, 20, 30 секунд
        await asyncio.sleep(10)
        try:
            await bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=progress_msg.message_id,
                text=f"⏳ Генерирую ваш персональный план... ({i * 10} сек)",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.debug(f"Failed to update progress message: {e}")
            break

# Запустить обновления в фоне
progress_task = asyncio.create_task(send_progress_updates())

# ... AI generation code ...

# Остановить обновления прогресса после завершения
progress_task.cancel()
```

**Fix Details:**
- Background task updates user every 10 seconds during AI generation
- Shows elapsed time to reduce user anxiety
- Task automatically cancelled after AI completes or on error
- Prevents "frozen" user experience during long waits

---

### BUG-2025-005: Race condition при множественных нажатиях кнопки подтверждения ✅ FIXED

- **Severity:** P1
- **Tags:** BUG, RACE_CONDITION
- **Status:** ✅ FIXED (2025-11-17)
- **Files:**
  - `bot/handlers/personal_plan.py:655-668` (confirm_and_generate)
- **Tests:** `tests/test_critical_bugs.py::test_confirm_and_generate_prevents_double_click`

**Описание:**
Если пользователь быстро нажмёт кнопку "✅ Всё верно, продолжить" 2+ раза (до того, как бот перешёл в состояние GENERATE), может произойти дублирование вызовов AI и двойное сохранение в БД.

**Steps to Reproduce:**
1. Пользователь на шаге подтверждения
2. Быстро нажать "✅ Всё верно" 2 раза подряд
3. Оба callback обработаны → 2 запроса к OpenRouter → 2 записи в БД

**Expected:**
Обработка только первого callback, последующие игнорируются.

**Actual:**
Дублирование AI запросов и записей в БД.

**Suspected Root Cause:**
Отсутствие idempotency-защиты или блокировки state перед переходом в GENERATE.

**Fix Applied:**
```python
# bot/handlers/personal_plan.py:660-668
@router.callback_query(F.data == "confirm:yes", SurveyStates.CONFIRM)
async def confirm_and_generate(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.from_user.id

    # Проверка: уже в процессе генерации?
    current_state = await state.get_state()
    if current_state == SurveyStates.GENERATE:
        await callback.answer("⏳ Уже генерирую план, подождите...", show_alert=True)
        logger.info(f"User {user_id} tried to confirm twice (race condition prevented)")
        return

    # Немедленно перейти в состояние GENERATE перед всеми операциями
    await state.set_state(SurveyStates.GENERATE)

    # ... rest of logic
```

**Fix Details:**
- Checks current state before processing
- Immediately sets state to GENERATE to block concurrent requests
- Shows user-friendly alert on duplicate clicks
- Logs race condition attempts for monitoring
- Prevents duplicate AI requests and DB saves

---

## 2. Высокий приоритет (P2)

### BUG-2025-010: Хардкод trainer username в клавиатуре ✅ FIXED

- **Severity:** P2
- **Tags:** HARDCODE, CONFIG
- **Status:** ✅ FIXED (2025-11-19)
- **Files:**
  - `bot/keyboards/survey.py:136` (get_contact_trainer_keyboard)
  - `bot/config.py` (TRAINER_USERNAME)

**Описание:**
Username тренера хардкодится прямо в коде: `url = "https://t.me/NicolasBatalin"`. При смене тренера или использовании бота в разных проектах нужно менять код.

**Expected:**
Username тренера должен быть в `.env` и `config.py`.

**Fix Applied:**
```python
# config.py
TRAINER_USERNAME: str = "NicolasBatalin"

# keyboards/survey.py:136
url = f"https://t.me/{settings.TRAINER_USERNAME}"
```

---

### BUG-2025-011: Отсутствие rate limiting на генерацию планов ✅ FIXED

- **Severity:** P2
- **Tags:** SECURITY, ABUSE
- **Status:** ✅ FIXED (2025-11-19)
- **Files:**
  - `bot/handlers/personal_plan.py:609` (confirm_and_generate)
  - `bot/services/database/repository.py:154-174` (count_plans_today)
  - `bot/config.py` (MAX_PLANS_PER_DAY)

**Описание:**
Нет защиты от abuse — пользователь может запросить генерацию плана 100 раз подряд, потратив деньги на OpenRouter API.

**Steps to Reproduce:**
1. Пользователь проходит опрос и нажимает "подтвердить"
2. План генерируется
3. Пользователь снова запускает `/personal_plan`, проходит опрос, генерирует
4. Повторять 100 раз

**Expected:**
Лимит на генерацию планов (например, 3 плана в день на пользователя).

**Fix Applied:**
```python
# bot/config.py
MAX_PLANS_PER_DAY: int = 3

# bot/services/database/repository.py:154-174
@staticmethod
async def count_plans_today(session: AsyncSession, user_id: int) -> int:
    today_start = datetime.combine(date.today(), datetime.min.time())
    result = await session.execute(
        select(func.count(Plan.id))
        .where(Plan.user_id == user_id)
        .where(Plan.created_at >= today_start)
    )
    return result.scalar_one()

# bot/handlers/personal_plan.py:609
# Rate limit check with fail-open design
try:
    async with async_session_maker() as session:
        plans_today = await PlanRepository.count_plans_today(session, user_id)
        if plans_today >= settings.MAX_PLANS_PER_DAY:
            await callback.message.answer(...)
            return
except Exception as e:
    logger.error(f"Rate limit check failed: {e}")
    # Fail-open: allow generation if check fails
```

**Fix Details:**
- Added configurable MAX_PLANS_PER_DAY setting (default: 3)
- Implemented count_plans_today() repository method
- Fail-open design: if DB check fails, allows generation (logged)
- User-friendly error message when limit exceeded

---

### BUG-2025-012: HTTP-Referer хардкод в OpenRouter запросе ✅ FIXED

- **Severity:** P2
- **Tags:** HARDCODE, CONFIG
- **Status:** ✅ FIXED (2025-11-19)
- **Files:**
  - `bot/services/ai/openrouter.py:64`
  - `bot/config.py` (PROJECT_URL)

**Описание:**
В заголовке запроса к OpenRouter API указан хардкод URL: `"HTTP-Referer": "https://github.com/your-repo"`. Это должно быть в конфигурации.

**Fix Applied:**
```python
# config.py
PROJECT_URL: str = "https://github.com/your-username/ai-lead-magnet-bot"

# openrouter.py:64
"HTTP-Referer": settings.PROJECT_URL,
```

---

### BUG-2025-013: Валидация AI response может пропустить некорректные ответы ✅ FIXED

- **Severity:** P2
- **Tags:** BUG, VALIDATION
- **Status:** ✅ FIXED (2025-11-19)
- **Files:**
  - `bot/validators/ai_response.py:9-69` (validate_ai_response)

**Описание:**
Валидация проверяет наличие ключевых слов, но НЕ проверяет:
- Длину ответа (должна быть <2000 символов по промпту, но может быть >4096 = Telegram limit)
- Наличие HTML-тегов без закрытия (может сломать форматирование)
- Наличие запрещённых слов (лекарства, добавки)

**Expected:**
Более строгая валидация:
- Длина ответа
- HTML валидация
- Проверка на запрещённые слова

**Fix Applied:**
```python
# bot/validators/ai_response.py:9-69
from typing import Dict, List, Any  # Fixed type hint

def validate_ai_response(text: str) -> Dict[str, Any]:
    errors: List[str] = []

    # 0. Проверка длины ответа (Telegram limit 4096, делаем запас)
    MAX_LENGTH = 4000
    if len(text) > MAX_LENGTH:
        errors.append(f"Ответ слишком длинный: {len(text)} символов (лимит {MAX_LENGTH})")

    # 0.1. Проверка минимальной длины
    MIN_LENGTH = 200
    if len(text) < MIN_LENGTH:
        errors.append(f"Ответ слишком короткий: {len(text)} символов (минимум {MIN_LENGTH})")

    # 0.2. Проверка на запрещённые слова (добавки, препараты)
    forbidden_words = ["добавк", "препарат", "лекарств", "витамин", "бад"]
    found_forbidden = []
    for word in forbidden_words:
        if word in text.lower():
            found_forbidden.append(word)
    if found_forbidden:
        errors.append(f"Обнаружены запрещённые слова: {', '.join(found_forbidden)}")

    # ... rest of checks (calories, disclaimer, etc.)
```

**Fix Details:**
- Added length validation (min 200, max 4000 chars)
- Added forbidden words check (добавки, препараты, БАДы, витамины)
- Fixed type hint: Dict[str, any] → Dict[str, Any]
- Prevents sending invalid/dangerous AI responses to users

---

### BUG-2025-014: Недостаточная обработка ошибок при удалении сообщений ✅ FIXED

- **Severity:** P2
- **Tags:** BUG, RUNTIME
- **Status:** ✅ FIXED (2025-11-19)
- **Files:**
  - `bot/handlers/personal_plan.py:52-76` (_safe_delete_message helper)
  - Multiple locations where message deletion occurs

**Описание:**
При удалении предыдущих сообщений бота используется голый `try-except: pass`, что скрывает реальные ошибки. Например, если Telegram API вернёт `MessageToDeleteNotFound`, это нормально, но если вернёт `BotBlocked` или `ChatNotFound`, это критичная ситуация.

**Expected:**
Логировать конкретные исключения и обрабатывать критичные случаи.

**Fix Applied:**
```python
# bot/handlers/personal_plan.py:52-76
async def _safe_delete_message(bot: Bot, chat_id: int, message_id: int) -> None:
    """
    Безопасно удаляет сообщение с подробным логированием ошибок.

    Args:
        bot: Bot instance
        chat_id: ID чата
        message_id: ID сообщения для удаления
    """
    from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest as e:
        if "message to delete not found" in str(e).lower():
            logger.debug(f"Message {message_id} already deleted")
        else:
            logger.warning(f"Failed to delete message {message_id}: {e}")
    except TelegramForbiddenError as e:
        logger.error(f"Bot blocked by user in chat {chat_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error deleting message {message_id}: {e}")
```

**Fix Details:**
- Created _safe_delete_message() helper function
- Handles TelegramBadRequest, TelegramForbiddenError separately
- Logs specific errors instead of silent try-except pass
- Detects bot blocks and logs critical events
- Applied to all message deletion points in handlers

---

### BUG-2025-015: Отсутствие проверки существования изображений на старте бота ✅ FIXED

- **Severity:** P2
- **Tags:** BUG, CONFIG
- **Status:** ✅ FIXED (2025-11-19)
- **Files:**
  - `bot/__main__.py:26-42` (on_startup image validation)

**Описание:**
Бот запускается БЕЗ проверки наличия критичных файлов в `assets/body_types/`. Если изображения отсутствуют, пользователь узнает об этом только при прохождении опроса до шага BODY_NOW → fallback сообщения.

**Expected:**
Проверка на старте бота + warning в логах, если файлы отсутствуют.

**Fix Applied:**
```python
# bot/__main__.py:26-42
async def on_startup():
    logger.info("[START] Starting bot...")

    # Проверка наличия изображений body types
    from bot.utils.paths import validate_image_file_exists
    from bot.constants import BODY_COUNTS

    missing_images = []
    for gender in ["male", "female"]:
        for stage in ["now", "ideal"]:
            count = BODY_COUNTS[gender][stage]
            for variant_id in range(1, count + 1):
                if not validate_image_file_exists(gender, stage, variant_id):
                    missing_images.append(f"{gender}/{stage}/{variant_id}")

    if missing_images:
        logger.warning(f"[!] Missing body type images: {', '.join(missing_images)}")
        logger.warning("[!] Users will see fallback messages for missing images")
    else:
        logger.info("[OK] All body type images found")
```

**Fix Details:**
- Added startup check for body type images
- Validates all required images (male/female, now/ideal)
- Logs warning with missing image paths
- Non-blocking: bot continues if images missing (fallback messages work)

---

## 3. Средний приоритет (P3)

### BUG-2025-020: Монолитный хендлер файл (856 строк)

- **Severity:** P3
- **Tags:** ARCH, DUPLICATION
- **Files:**
  - `bot/handlers/personal_plan.py` (весь файл)

**Описание:**
Весь опрос (19 хендлеров) в одном файле на 856 строк. Сложно поддерживать, найти нужный хендлер, тестировать изолированно.

**Expected:**
Разбить на модули:
- `bot/handlers/survey/gender.py`
- `bot/handlers/survey/metrics.py` (age, height, weight, target_weight)
- `bot/handlers/survey/activity.py`
- `bot/handlers/survey/body_types.py`
- `bot/handlers/survey/timezone.py`
- `bot/handlers/survey/confirmation.py`
- `bot/handlers/survey/navigation.py` (back, cancel)

---

### BUG-2025-021: Дублирование логики удаления сообщений ✅ FIXED

- **Severity:** P3
- **Tags:** DUPLICATION
- **Status:** ✅ FIXED (2025-11-19) - Fixed in P2 work
- **Files:**
  - `bot/handlers/personal_plan.py:52-76` (_safe_delete_message helper)
  - Multiple handler locations updated

**Описание:**
Блок удаления предыдущего сообщения бота дублируется в 10+ хендлерах. Нарушение DRY.

**Fix Applied:**
See BUG-2025-014 for implementation details. This was addressed as part of P2 error handling improvements.

---

### BUG-2025-022: Relationships в моделях закомментированы ✅ FIXED

- **Severity:** P3
- **Tags:** ARCH, DB
- **Status:** ✅ FIXED (2025-11-19)
- **Files:**
  - `bot/models/user.py:27-28` (relationships uncommented)
  - `bot/models/survey.py:52-53` (SurveyAnswer relationships)
  - `bot/models/survey.py:106-107` (Plan relationships)

**Fix Applied:**
```python
# bot/models/user.py:27-28
survey_answers: Mapped[List["SurveyAnswer"]] = relationship(back_populates="user", cascade="all, delete-orphan")
plans: Mapped[List["Plan"]] = relationship(back_populates="user", cascade="all, delete-orphan")

# bot/models/survey.py:52-53
user: Mapped["User"] = relationship(back_populates="survey_answers")
plans: Mapped[List["Plan"]] = relationship(back_populates="survey_answer")

# bot/models/survey.py:106-107
user: Mapped["User"] = relationship(back_populates="plans")
survey_answer: Mapped[Optional["SurveyAnswer"]] = relationship(back_populates="plans")
```

**Fix Details:**
- Enabled ORM relationships in all models (User, SurveyAnswer, Plan)
- Added missing `List` import in survey.py
- Allows for JOIN queries and lazy/eager loading
- Tested: Models import successfully with relationships

---

### BUG-2025-023: Отсутствие индекса на survey_answers.created_at ✅ FIXED

- **Severity:** P3
- **Tags:** DB, PERFORMANCE
- **Status:** ✅ FIXED (2025-11-19)
- **Files:**
  - `alembic/versions/46e97e78aed0_add_index_survey_answers_created_at.py` (new migration)

**Описание:**
В таблице `survey_answers` есть индекс на `completed_at`, но нет на `created_at`. Если нужно будет делать аналитику по времени начала опроса, запросы будут медленными.

**Fix Applied:**
```python
# alembic/versions/46e97e78aed0_*.py
def upgrade() -> None:
    """Добавляет индекс на survey_answers.created_at для аналитики времени начала опроса."""
    op.create_index(
        'ix_survey_answers_created_at',
        'survey_answers',
        ['created_at']
    )

def downgrade() -> None:
    """Удаляет индекс survey_answers.created_at."""
    op.drop_index('ix_survey_answers_created_at', 'survey_answers')
```

**Fix Details:**
- Created new Alembic migration: 46e97e78aed0
- Added ix_survey_answers_created_at index for analytics
- Improves query performance for survey start time analysis
- Migration includes proper upgrade/downgrade functions

---

### BUG-2025-024: Отсутствие docstring в большинстве функций

- **Severity:** P3
- **Tags:** STYLE, DOCS
- **Files:**
  - Множество файлов (например, `bot/handlers/personal_plan.py`)

**Описание:**
Большинство хендлеров НЕ имеют docstring с описанием логики, параметров, возвращаемых значений.

---

### BUG-2025-025: Дублирование блоков валидации в process_target_weight_text ✅ FIXED

- **Severity:** P3
- **Tags:** DUPLICATION
- **Status:** ✅ FIXED (2025-11-19)
- **Files:**
  - `bot/handlers/personal_plan.py:301-317` (simplified from 45 to 17 lines)

**Fix Applied:**
```python
# bot/handlers/personal_plan.py:301-317
async def process_target_weight_text(message: Message, state: FSMContext):
    """Обработка ввода целевого веса."""
    data = await state.get_data()
    current_weight = data.get("weight_kg")

    # Валидация целевого веса (включает проверку числа и отличия от текущего)
    target_weight = validate_target_weight(message.text, current_weight)

    if target_weight is None:
        # Delete invalid input and show error
        ...
        return

    # Save and continue to next step
    ...
```

**Fix Details:**
- Simplified validation logic from 45 lines to 17 lines (-62%)
- Removed redundant validate_weight() calls
- validate_target_weight() already includes all necessary checks
- Reduces code duplication and potential for bugs

---

## 4. Низкий приоритет (P4)

### BUG-2025-030: Inconsistent naming: snake_case vs camelCase в AI response

- **Severity:** P4
- **Tags:** STYLE
- **Files:**
  - `bot/validators/ai_response.py:9`

**Описание:**
Тип возврата функции `validate_ai_response` использует строковый ключ `"any"` вместо `Any` из `typing`.

**Proposed Fix:**
```python
from typing import Dict, List, Any

def validate_ai_response(text: str) -> Dict[str, Any]:
    ...
```

---

### BUG-2025-031: Magic numbers в промпте (v2.3.1)

- **Severity:** P4
- **Tags:** HARDCODE
- **Files:**
  - `bot/prompts/personal_plan.py:10`

**Описание:**
Версия промпта хардкодится строкой `"v2.3.1"` без семантики. Лучше использовать semantic versioning с комментариями к изменениям.

---

### BUG-2025-032: Отсутствие type hints в некоторых функциях

- **Severity:** P4
- **Tags:** STYLE
- **Files:**
  - `bot/handlers/personal_plan.py:558` (show_confirmation)

---

### BUG-2025-033: Unused constants в survey.py ✅ FIXED

- **Severity:** P4
- **Tags:** DEAD_CODE
- **Status:** ✅ FIXED (2025-11-19)
- **Files:**
  - `bot/constants/survey.py` (removed TOTAL_STEPS, STEP_NAMES)
  - `bot/constants/__init__.py` (updated exports)

**Fix Applied:**
- Deleted TOTAL_STEPS and STEP_NAMES from constants/survey.py
- Removed from constants/__init__.py exports
- Added comment explaining removal for future reference
- Verified no usage in codebase via grep

---

### BUG-2025-034: Пустая функция get_back_cancel_keyboard() ✅ FIXED

- **Severity:** P4
- **Tags:** DEAD_CODE
- **Status:** ✅ FIXED (2025-11-19)
- **Files:**
  - `bot/keyboards/survey.py:108-111` (renamed to get_empty_keyboard)
  - `bot/keyboards/__init__.py` (updated exports)
  - `bot/handlers/personal_plan.py` (3 usage locations updated)

**Fix Applied:**
```python
# bot/keyboards/survey.py:108-111
def get_empty_keyboard() -> InlineKeyboardMarkup:
    """Пустая клавиатура (без кнопок)."""
    builder = InlineKeyboardBuilder()
    return builder.as_markup()
```

**Fix Details:**
- Renamed get_back_cancel_keyboard() to get_empty_keyboard()
- Updated all imports and usage (3 locations in personal_plan.py)
- New name accurately reflects function purpose (empty keyboard, not back/cancel)
- Tested: Import successful, all tests pass

---

## 5. Хардкод и конфигурация (P2-P3)

### BUG-2025-040: HTTP-клиент timeout хардкод

- **Severity:** P2
- **Tags:** CONFIG, HARDCODE
- **Files:**
  - `bot/services/ai/openrouter.py:58`

**Описание:**
Таймаут берётся из `settings.OPENROUTER_TIMEOUT` (30 сек), но нет возможности задать разные таймауты для разных эндпоинтов (connection timeout vs read timeout).

---

### BUG-2025-041: Отсутствие CORS/Origin в OpenRouter request

- **Severity:** P3
- **Tags:** INTEGRATION
- **Files:**
  - `bot/services/ai/openrouter.py:64-65`

**Описание:**
В заголовках указан `HTTP-Referer` и `X-Title`, но по best practices для OpenRouter рекомендуется также указывать `X-Origin` для аналитики.

---

## 6. Интеграции и зависимости (P2-P3)

### BUG-2025-050: Отсутствие retry логики для OpenRouter API

- **Severity:** P2
- **Tags:** INTEGRATION
- **Files:**
  - `bot/services/ai/openrouter.py:58-76`

**Описание:**
При HTTP ошибке от OpenRouter (503, 429) бот сразу возвращает ошибку. Нет ретраев с exponential backoff.

**Proposed Fix:**
```python
# Использовать библиотеку tenacity для ретраев
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.HTTPStatusError)
)
async def _make_openrouter_request(self, payload):
    ...
```

---

### BUG-2025-051: Отсутствие connection pooling для БД

- **Severity:** P3
- **Tags:** DB, PERFORMANCE
- **Files:**
  - `bot/services/database/session.py:14-18`

**Описание:**
SQLAlchemy async engine создаётся без явных настроек пула соединений. По умолчанию pool_size=5, но для бота с большим количеством пользователей может понадобиться больше.

**Proposed Fix:**
```python
# bot/services/database/session.py:14
engine = create_async_engine(
    settings.database_url,
    echo=settings.DEBUG_MODE,
    pool_pre_ping=True,
    pool_size=20,            # Увеличить до 20
    max_overflow=30,         # Дополнительные соединения
    pool_recycle=3600        # Переиспользовать соединения каждый час
)
```

---

## 7. Безопасность (P2-P3)

### BUG-2025-060: Логирование может содержать PII (Personal Identifiable Information)

- **Severity:** P2
- **Tags:** SECURITY, PRIVACY
- **Files:**
  - `bot/services/events.py:40` (log_event)

**Описание:**
В логах пишется `user_id` и `payload` с персональными данными (возраст, вес, рост, timezone). В production это может нарушать GDPR/CCPA.

**Expected:**
Либо маскировать PII в логах, либо логировать только агрегированные данные.

---

### BUG-2025-061: Отсутствие SQL injection защиты (LOW RISK, но стоит отметить)

- **Severity:** P3
- **Tags:** SECURITY
- **Files:**
  - `bot/services/database/repository.py` (весь файл)

**Описание:**
Используется ORM (SQLAlchemy), что само по себе защищает от SQL injection. Однако, если в будущем добавят raw SQL запросы без параметризации, это станет уязвимостью.

**Recommendation:**
Добавить в linter правило: запретить использование `text()` без bind parameters.

---

### BUG-2025-062: API ключ может попасть в логи при DEBUG_MODE=True

- **Severity:** P2
- **Tags:** SECURITY
- **Files:**
  - `bot/services/database/session.py:16` (echo=settings.DEBUG_MODE)

**Описание:**
При `DEBUG_MODE=True` и `echo=True` SQLAlchemy логирует ВСЕ SQL-запросы, включая INSERT с API keys (если бы они хранились в БД). Также `httpx` может логировать headers с `Authorization: Bearer API_KEY`.

**Proposed Fix:**
```python
# Отключить логирование HTTP headers с секретами
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
```

---

## 8. Тестирование (P2-P3)

### BUG-2025-070: Отсутствие unit tests

- **Severity:** P2
- **Tags:** TESTS
- **Files:**
  - Весь проект (директория `tests/` не существует)

**Описание:**
В проекте НЕТ ни одного теста. Любое изменение может сломать бота.

**Proposed Fix:**
Создать базовую структуру тестов:
```
tests/
├── __init__.py
├── conftest.py           # pytest fixtures
├── test_validators.py    # Unit tests для валидаторов
├── test_ai_client.py     # Mock тесты для OpenRouter
├── test_repositories.py  # DB тесты с pytest-asyncio
└── test_handlers.py      # Integration тесты хендлеров
```

---

### BUG-2025-071: Отсутствие CI/CD pipeline

- **Severity:** P3
- **Tags:** TESTS, CI
- **Files:**
  - `.github/workflows/` (не существует)

**Описание:**
Нет автоматического прогона тестов, линтеров, проверки форматирования при push/PR.

---

## 9. Архитектурные проблемы (P3)

### BUG-2025-080: Отсутствие слоя бизнес-логики (Service Layer)

- **Severity:** P3
- **Tags:** ARCH
- **Files:**
  - `bot/handlers/personal_plan.py:622-651` (confirm_and_generate)

**Описание:**
Вся бизнес-логика смешана с хендлерами. Например, определение `goal` (fat_loss/muscle_gain) происходит прямо в хендлере.

**Expected:**
Вынести в отдельный сервис:
```python
# bot/services/survey_service.py
class SurveyService:
    @staticmethod
    def determine_goal(weight_kg: float, target_weight_kg: Optional[float]) -> str:
        if not target_weight_kg:
            return "maintenance"
        if target_weight_kg < weight_kg:
            return "fat_loss"
        if target_weight_kg > weight_kg:
            return "muscle_gain"
        return "maintenance"
```

---

### BUG-2025-081: Отсутствие middleware для логирования запросов

- **Severity:** P3
- **Tags:** ARCH
- **Files:**
  - `bot/__main__.py:50`

**Описание:**
Нет middleware для автоматического логирования всех входящих обновлений (messages, callbacks). Сложно дебажить проблемы.

---

## 10. Dead Code & Unused Imports

### BUG-2025-090: Unused import в personal_plan.py

- **Severity:** P4
- **Tags:** DEAD_CODE
- **Files:**
  - `bot/handlers/personal_plan.py:262` (дублируется импорт `validate_weight`)

**Описание:**
В строке 262 импортируется `from bot.validators import validate_weight`, но он уже импортирован в строке 14.

---

---

## Fix Roadmap

### Этап 1: Критичные баги (P1) — Стабилизация ✅ COMPLETED

**Статус:** ✅ **5/5 FIXED (100%)** - Завершено 2025-11-17

1. ✅ **BUG-2025-001: Валидация callback_data** - FIXED
2. ✅ **BUG-2025-002: AttributeError при отсутствии from_user** - FIXED
3. ✅ **BUG-2025-003: DB exception handling при сохранении плана** - FIXED
4. ✅ **BUG-2025-004: Промежуточные уведомления при генерации AI** - FIXED
5. ✅ **BUG-2025-005: Race condition на подтверждении** - FIXED

**Тестирование:** 12/12 тестов passing в `tests/test_critical_bugs.py`

---

### Этап 2: Безопасность и конфигурация (P2) — 60% COMPLETED

**Статус:** ✅ **6/10 FIXED (60%)** - Частично завершено 2025-11-19

✅ **Выполнено:**
1. ✅ **BUG-2025-010: Trainer username в конфиг** - FIXED
2. ✅ **BUG-2025-011: Rate limiting на генерацию планов** - FIXED
3. ✅ **BUG-2025-012: HTTP-Referer в конфиг** - FIXED
4. ✅ **BUG-2025-013: Улучшенная валидация AI** - FIXED
5. ✅ **BUG-2025-014: Обработка ошибок Telegram API** - FIXED
6. ✅ **BUG-2025-015: Проверка изображений на старте** - FIXED

🔴 **Осталось:**
- BUG-2025-050: Retry логика для OpenRouter
- BUG-2025-060: Маскировка PII в логах
- BUG-2025-062: Отключить логирование API keys
- BUG-2025-040: HTTP-клиент timeout хардкод
- BUG-2025-041: CORS/Origin в OpenRouter request

---

### Этап 3: Рефакторинг архитектуры (P3) — 36% COMPLETED

**Статус:** ✅ **5/14 FIXED (36%)** - Частично завершено 2025-11-19

✅ **Выполнено:**
1. ✅ **BUG-2025-021: Вынести дублирующуюся логику удаления сообщений** - FIXED (в составе P2)
2. ✅ **BUG-2025-022: Раскомментировать relationships в моделях** - FIXED
3. ✅ **BUG-2025-023: Добавить индекс на survey_answers.created_at** - FIXED
4. ✅ **BUG-2025-025: Убрать дублирование валидации** - FIXED
5. ✅ **BUG-2025-033: Удалить unused constants** - FIXED (P4, но завершено)
6. ✅ **BUG-2025-034: Переименовать get_empty_keyboard()** - FIXED (P4, но завершено)

🔴 **Осталось (архитектура и документация):**
- BUG-2025-020: Разбить монолитный хендлер на модули (856 строк)
- BUG-2025-024: Добавить docstrings
- BUG-2025-051: Connection pooling для БД
- BUG-2025-080: Добавить Service Layer
- BUG-2025-081: Middleware для логирования
- И другие P3 задачи

**Проверка:** Регресс-тестирование после рефакторинга - все 12 тестов passing.

---

### Этап 5: Тестирование (P2-P3) [2-3 дня]

**Цель:** Покрытие тестами критичных модулей.

1. **BUG-2025-070: Добавить unit tests**
   - `tests/test_validators.py` (100% coverage)
   - `tests/test_ai_client.py` (mock OpenRouter)
   - `tests/test_repositories.py` (DB с pytest-asyncio)
   - `tests/test_handlers.py` (интеграционные тесты хендлеров)

2. **BUG-2025-071: Настроить CI/CD**
   - `.github/workflows/test.yml` (pytest + coverage)
   - `.github/workflows/lint.yml` (ruff/black/mypy)

**Проверка:** Coverage >70% для критичных модулей.

---

### Этап 4: Оптимизация и dead code (P4) — 40% COMPLETED

**Статус:** ✅ **2/5 FIXED (40%)**

✅ **Выполнено:**
1. ✅ **BUG-2025-033: Удалить unused constants** - FIXED
2. ✅ **BUG-2025-034: Переименовать get_empty_keyboard()** - FIXED

🔴 **Осталось:**
- BUG-2025-030: Fix type hint Any (cosmetic)
- BUG-2025-031: Magic numbers в промпте
- BUG-2025-032: Type hints в некоторых функциях
- BUG-2025-090: Unused import

---

## Статистика

**Всего найдено проблем:** 34

**По приоритетам:**
- P1 (Critical): 5 багов → ✅ **5/5 FIXED (100%)**
- P2 (High): 10 проблем → ✅ **6/10 FIXED (60%)**
  - ✅ BUG-2025-010, 011, 012, 013, 014, 015
  - 🔴 BUG-2025-050, 060, 062 (осталось 3 + BUG-2025-040, 041 из P2-P3)
- P3 (Medium): 14 проблем → ✅ **5/14 FIXED (36%)**
  - ✅ BUG-2025-021, 022, 023, 025, 033, 034 (6 из них, но 021 считался как часть P2)
  - 🔴 BUG-2025-020, 024, 051, 080, 081 (осталось 9)
- P4 (Low): 5 проблем → ✅ **2/5 FIXED (40%)**
  - ✅ BUG-2025-033, 034
  - 🔴 BUG-2025-030, 031, 032, 090 (осталось 3)

**По типам:**
- BUG (runtime): 8
- HARDCODE: 5
- ARCH: 5
- SECURITY: 4
- INTEGRATION: 4
- TESTS: 2
- DUPLICATION: 3
- DEAD_CODE: 3

**Прогресс фиксов:**
- ✅ Этап 1 (P1): ЗАВЕРШЕНО - 5/5 багов (100%)
- ✅ Этап 2 (P2 security): В ПРОЦЕССЕ - 6/10 багов (60%)
- 🔴 Этап 3 (P3 refactoring): В ПРОЦЕССЕ - 5/14 багов (36%)
- 🔴 Этап 4 (P4 optimization): В ПРОЦЕССЕ - 2/5 багов (40%)
- 🔴 Этап 5 (tests): НЕ НАЧАТО - 0/2 задач

**Общий прогресс:** 18/34 задач завершено (53%)

**Оставшееся время:**
- Этап 2 (осталось 4 P2): ~0.5 дня
- Этап 3 (осталось 9 P3): ~2 дня
- Этап 4 (осталось 3 P4): ~0.5 дня
- Этап 5 (тесты): ~2 дня

**Итого осталось:** ~5 рабочих дней

---

## Приоритизация для первого спринта

Если нужно выбрать минимальный набор для production-ready состояния:

**Must-Have (блокеры для прода):**
- BUG-2025-001, 002, 003, 005 (крэши)
- BUG-2025-011 (rate limiting)
- BUG-2025-015 (проверка изображений на старте)
- BUG-2025-050 (retry для OpenRouter)
- BUG-2025-060 (PII в логах)

**Nice-to-Have (не блокируют, но важны):**
- BUG-2025-004 (промежуточные уведомления)
- BUG-2025-013 (валидация AI)
- BUG-2025-020, 021 (рефакторинг)

---

## Контакты для уточнений

Если нужно обсудить приоритеты, уточнить детали багов или обсудить патчи — создай Issue в репозитории или свяжись с командой.

**Следующий шаг:** Начать с Этапа 1 (P1 баги), создать feature-ветку `fix/p1-critical-bugs` и фиксить по одному багу за раз с минимальными диффами и обязательными тестами.
