# Roadmap: AI-Driven Personal Plan Feature для Telegram-бота

**Версия**: 1.0
**Дата**: 2025-11-16
**Оценка**: 10/10 детализации

---

## 1. Архитектура потока (E2E)

### 1.1. Точки входа

1. **Команда `/start`** (если новый пользователь) → основное меню → кнопка "Получить персональный план"
2. **Пункт меню "Персональный план"** → запуск опроса напрямую
3. **Мягкий триггер** (опционально): после первого успешного ввода калорий → подсказка "Хотите получить персональный план питания и тренировок?"

### 1.2. FSM-сценарий с навигацией

**Основной поток**:
```
IDLE → GENDER → AGE → HEIGHT → WEIGHT → TARGET_WEIGHT (опц.) →
ACTIVITY → BODY_NOW → BODY_IDEAL → TZ → CONFIRM → GENERATE → SHOW_PLAN → IDLE
```

**Возможности навигации**:
- На каждом шаге (кроме первого): кнопка "◀️ Назад" → возврат на предыдущий шаг
- Кнопка "❌ Отменить" → выход из опроса, возврат в главное меню
- Данные сохраняются в FSM state, не в БД до финального подтверждения

### 1.3. Ветви и крайние случаи

**Смена пола**:
- Если пользователь на шаге GENDER выбрал другой пол (после возврата назад)
- → Очистить `body_now_id`, `body_now_label`, `body_ideal_id`, `body_ideal_label` из FSM state
- → При достижении BODY_NOW/BODY_IDEAL показать правильный набор картинок

**Недоступность изображения**:
- При `FileNotFoundError` или `TelegramBadRequest`:
  - Логировать ошибку
  - Показать fallback-сообщение: "Изображение временно недоступно. Попробуйте снова."
  - Повторить попытку отправки через 2 сек (максимум 3 попытки)
  - Если все попытки неудачны → пропустить этот вариант, показать следующий

**Отмена**:
- Callback "cancel" → `state.clear()` → отправить "Опрос отменён. Вернитесь в меню /menu"

**Таймаут FSM**:
- TTL для состояния: 30 минут
- После истечения → автоматический сброс + уведомление при следующем взаимодействии

### 1.4. Отправка отдельных изображений (UX)

**Выбранный подход**: Отдельные сообщения с картинками (наиболее стабильно для aiogram 3.x)

**Реализация для BODY_NOW (пример для женщин, 5 вариантов)**:

1. Отправить сообщение-заголовок:
   ```
   📸 Выберите ваш текущий тип фигуры:
   ```

2. Отправить **5 отдельных сообщений** (последовательно):
   ```python
   for i in range(1, 6):
       photo = FSInputFile(f"assets/body_types/female/now/female_now_{i}.jpg")
       await bot.send_photo(
           chat_id=user_id,
           photo=photo,
           caption=f"Вариант {i}: {BODY_LABELS['female']['now'][i]}",
           reply_markup=inline_kb_single_choice(f"body_now_{i}")
       )
   ```

3. InlineKeyboard под каждой картинкой:
   ```
   [{"text": "✅ Выбрать", "callback_data": "body_now_1"}]
   ```

4. После выбора:
   - Удалить все 5 сообщений с картинками (сохранить `message_id` при отправке)
   - Показать подтверждение: "Вы выбрали: Вариант 2 — Склонность к животу"
   - Перейти к следующему шагу

**Альтернатива** (для будущего, если потребуется):
- MediaGroup (альбом) из 5 фото
- Одна InlineKeyboard под альбомом с 5 кнопками: `[1] [2] [3] [4] [5]`
- **Проблема**: в Telegram API нельзя прикрепить callback_data к отдельному фото в альбоме
- **Вывод**: для v1 используем отдельные сообщения

### 1.5. Подтверждение и генерация плана

**Шаг CONFIRM**:
```
✅ Проверьте данные:

Пол: Женский
Возраст: 28 лет
Рост: 165 см
Вес: 62 кг
Целевой вес: 58 кг
Активность: Лёгкая (1-2 тренировки/нед)
Текущий тип фигуры: Вариант 4
Идеал: Вариант 2
Часовой пояс: Europe/Paris (UTC+1)

[Всё верно ✅]  [Изменить ✏️]
```

**Callback "confirm_yes"** → состояние GENERATE:
1. Отправить "⏳ Генерирую персональный план... (~5-10 сек)"
2. Собрать payload для AI
3. Вызвать OpenRouter API
4. Валидация ответа (наличие диапазона калорий + фразы про тренера)
5. Сохранить в БД: `survey_answers`, `plans`
6. Отправить результат
7. Показать кнопку "Вернуться к учёту калорий"

---

## 2. FSM-карта

### 2.1. Состояния

```python
class SurveyStates(StatesGroup):
    GENDER = State()           # Выбор пола
    AGE = State()              # Ввод возраста (число)
    HEIGHT = State()           # Ввод роста (см)
    WEIGHT = State()           # Ввод веса (кг)
    TARGET_WEIGHT = State()    # Целевой вес (опционально, можно пропустить)
    ACTIVITY = State()         # Уровень активности
    BODY_NOW = State()         # Текущий тип фигуры (отдельные картинки)
    BODY_IDEAL = State()       # Идеальный тип фигуры (отдельные картинки)
    TZ = State()               # Часовой пояс (IANA)
    CONFIRM = State()          # Подтверждение данных
    GENERATE = State()         # Генерация плана (технический шаг)
```

### 2.2. Переходы и валидации

| Состояние       | Ввод                        | Валидация                                      | Следующее       |
|-----------------|------------------------------|------------------------------------------------|-----------------|
| GENDER          | InlineButton (m/f)           | gender in ["male", "female"]                   | AGE             |
| AGE             | Text (число)                 | 14 ≤ age ≤ 80                                  | HEIGHT          |
| HEIGHT          | Text (число)                 | 120 ≤ height_cm ≤ 250                          | WEIGHT          |
| WEIGHT          | Text (число, может дробь)    | 30 ≤ weight_kg ≤ 300                           | TARGET_WEIGHT   |
| TARGET_WEIGHT   | Text / кнопка "Пропустить"   | (опц.) 30 ≤ target ≤ 300, target ≠ weight      | ACTIVITY        |
| ACTIVITY        | InlineButton (sed/light/mod) | activity in ACTIVITY_LEVELS                    | BODY_NOW        |
| BODY_NOW        | InlineButton (body_now_N)    | 1 ≤ N ≤ count_for_gender                       | BODY_IDEAL      |
| BODY_IDEAL      | InlineButton (body_ideal_N)  | 1 ≤ N ≤ 3                                      | TZ              |
| TZ              | InlineButton / Text (IANA)   | validate_tz(tz_string)                         | CONFIRM         |
| CONFIRM         | InlineButton (yes/edit)      | —                                              | GENERATE / назад|
| GENERATE        | Автоматический переход       | —                                              | IDLE (конец)    |

### 2.3. Правила показа изображений

**BODY_NOW** (зависит от пола):
- `female`: 5 изображений (`female_now_1.jpg` … `female_now_5.jpg`)
- `male`: 4 изображения (`male_now_1.jpg` … `male_now_4.jpg`)

**BODY_IDEAL** (одинаково для обоих полов):
- `female`: 3 изображения (`female_ideal_1.jpg` … `female_ideal_3.jpg`)
- `male`: 3 изображения (`male_ideal_1.jpg` … `male_ideal_3.jpg`)

**ID варианта = номер в имени файла**:
- Callback `body_now_3` → файл `{gender}_now_3.jpg`
- Callback `body_ideal_2` → файл `{gender}_ideal_2.jpg`

### 2.4. Поведение "Назад"

**Реализация**:
```python
@router.callback_query(F.data == "back", SurveyStates.AGE)
async def back_to_gender(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SurveyStates.GENDER)
    await show_gender_selection(callback.message)
```

**Правило**: при возврате с BODY_NOW/BODY_IDEAL на GENDER:
- Если новый пол ≠ старый пол → очистить `body_now_*`, `body_ideal_*`
- Иначе сохранить выборы

**Сброс полностью** (кнопка "❌ Отменить"):
```python
await state.clear()
await message.answer("Опрос отменён. Введите /menu для возврата в меню.")
```

---

## 3. Схема БД и миграции

### 3.1. Таблицы

#### 3.1.1. `users`

```sql
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    tg_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    full_name VARCHAR(255),
    tz VARCHAR(64) DEFAULT 'Europe/Moscow',
    utc_offset_minutes INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_tg_id ON users(tg_id);
```

#### 3.1.2. `survey_answers`

```sql
CREATE TABLE IF NOT EXISTS survey_answers (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Ответы опроса
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('male', 'female')),
    age INTEGER NOT NULL CHECK (age BETWEEN 14 AND 80),
    height_cm INTEGER NOT NULL CHECK (height_cm BETWEEN 120 AND 250),
    weight_kg NUMERIC(5,2) NOT NULL CHECK (weight_kg BETWEEN 30 AND 300),
    target_weight_kg NUMERIC(5,2) CHECK (target_weight_kg BETWEEN 30 AND 300),
    activity VARCHAR(20) NOT NULL CHECK (activity IN ('sedentary', 'light', 'moderate', 'active', 'very_active')),

    -- Типы фигуры
    body_now_id INTEGER NOT NULL,
    body_now_label TEXT,
    body_now_file TEXT NOT NULL,  -- относительный путь или telegram_file_id

    body_ideal_id INTEGER NOT NULL,
    body_ideal_label TEXT,
    body_ideal_file TEXT NOT NULL,

    -- Часовой пояс
    tz VARCHAR(64) NOT NULL DEFAULT 'Europe/Moscow',
    utc_offset_minutes INTEGER NOT NULL,

    -- Метаданные
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_survey_answers_user_id ON survey_answers(user_id);
CREATE INDEX idx_survey_answers_completed_at ON survey_answers(completed_at);
```

#### 3.1.3. `plans`

```sql
CREATE TABLE IF NOT EXISTS plans (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    survey_answer_id BIGINT REFERENCES survey_answers(id) ON DELETE SET NULL,

    -- Ответ ИИ
    ai_text TEXT NOT NULL,
    ai_model VARCHAR(100),      -- например, "meta-llama/llama-3.1-70b-instruct"
    prompt_version VARCHAR(20), -- версия системного промпта, например, "v1.0"

    -- Метаданные
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_plans_user_id ON plans(user_id);
CREATE INDEX idx_plans_created_at ON plans(created_at);
```

#### 3.1.4. `events` (опционально, для аналитики)

```sql
CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    event VARCHAR(100) NOT NULL,  -- "survey_started", "survey_completed", "plan_generated"
    payload JSONB,                -- дополнительные данные
    ts TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_user_id ON events(user_id);
CREATE INDEX idx_events_event ON events(event);
CREATE INDEX idx_events_ts ON events(ts);
```

### 3.2. Alembic миграции

#### Миграция 1: Создание таблиц

**Файл**: `alembic/versions/001_create_survey_tables.py`

```python
"""Create survey and plans tables

Revision ID: 001
Revises: <previous_revision>
Create Date: 2025-11-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '001'
down_revision = '<previous_revision>'  # ID предыдущей миграции
branch_labels = None
depends_on = None

def upgrade():
    # Добавить колонки в users (если таблица уже существует)
    op.add_column('users', sa.Column('tz', sa.String(64), server_default='Europe/Moscow'))
    op.add_column('users', sa.Column('utc_offset_minutes', sa.Integer, nullable=True))

    # Создать survey_answers
    op.create_table(
        'survey_answers',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('gender', sa.String(10), nullable=False),
        sa.Column('age', sa.Integer, nullable=False),
        sa.Column('height_cm', sa.Integer, nullable=False),
        sa.Column('weight_kg', sa.Numeric(5, 2), nullable=False),
        sa.Column('target_weight_kg', sa.Numeric(5, 2), nullable=True),
        sa.Column('activity', sa.String(20), nullable=False),
        sa.Column('body_now_id', sa.Integer, nullable=False),
        sa.Column('body_now_label', sa.Text, nullable=True),
        sa.Column('body_now_file', sa.Text, nullable=False),
        sa.Column('body_ideal_id', sa.Integer, nullable=False),
        sa.Column('body_ideal_label', sa.Text, nullable=True),
        sa.Column('body_ideal_file', sa.Text, nullable=False),
        sa.Column('tz', sa.String(64), nullable=False, server_default='Europe/Moscow'),
        sa.Column('utc_offset_minutes', sa.Integer, nullable=False),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("gender IN ('male', 'female')", name='check_gender'),
        sa.CheckConstraint('age BETWEEN 14 AND 80', name='check_age'),
        sa.CheckConstraint('height_cm BETWEEN 120 AND 250', name='check_height'),
        sa.CheckConstraint('weight_kg BETWEEN 30 AND 300', name='check_weight'),
        sa.CheckConstraint('target_weight_kg IS NULL OR target_weight_kg BETWEEN 30 AND 300', name='check_target_weight'),
        sa.CheckConstraint("activity IN ('sedentary', 'light', 'moderate', 'active', 'very_active')", name='check_activity')
    )
    op.create_index('idx_survey_answers_user_id', 'survey_answers', ['user_id'])
    op.create_index('idx_survey_answers_completed_at', 'survey_answers', ['completed_at'])

    # Создать plans
    op.create_table(
        'plans',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('survey_answer_id', sa.BigInteger, sa.ForeignKey('survey_answers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('ai_text', sa.Text, nullable=False),
        sa.Column('ai_model', sa.String(100), nullable=True),
        sa.Column('prompt_version', sa.String(20), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_plans_user_id', 'plans', ['user_id'])
    op.create_index('idx_plans_created_at', 'plans', ['created_at'])

    # Создать events (опционально)
    op.create_table(
        'events',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event', sa.String(100), nullable=False),
        sa.Column('payload', JSONB, nullable=True),
        sa.Column('ts', sa.TIMESTAMP(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_events_user_id', 'events', ['user_id'])
    op.create_index('idx_events_event', 'events', ['event'])
    op.create_index('idx_events_ts', 'events', ['ts'])

def downgrade():
    op.drop_table('events')
    op.drop_table('plans')
    op.drop_table('survey_answers')
    op.drop_column('users', 'utc_offset_minutes')
    op.drop_column('users', 'tz')
```

### 3.3. Хранение `body_*_file`

**Два подхода**:

#### Вариант А: Относительный путь (простота)
```python
body_now_file = "assets/body_types/female/now/female_now_3.jpg"
```

**Плюсы**:
- Прозрачность, легко дебажить
- Независимость от Telegram API

**Минусы**:
- При каждой отправке загружается файл с диска → медленнее

#### Вариант Б: Telegram `file_id` (скорость) — **РЕКОМЕНДУЕТСЯ**

1. При первой отправке изображения сохранить `file_id` из ответа Telegram:
   ```python
   msg = await bot.send_photo(chat_id, photo=FSInputFile(path))
   file_id = msg.photo[-1].file_id  # самое большое разрешение
   # Сохранить в cache/БД: {"female_now_3": file_id}
   ```

2. При последующих отправках использовать `file_id`:
   ```python
   await bot.send_photo(chat_id, photo=file_id)  # мгновенная отправка
   ```

**Реализация кеша**:
- **Redis**: ключ `body_image:{gender}:{stage}:{variant}` → `file_id`, TTL = 30 дней
- **Fallback**: если `file_id` устарел → загрузить заново с диска

**В БД `survey_answers.body_now_file`** сохранять:
- Или путь (для истории): `"assets/body_types/female/now/female_now_3.jpg"`
- Или `file_id` (если нужно позже отправить пользователю снова)

**Рекомендация для v1**:
- В БД сохранять **относительный путь** (для независимости)
- В памяти/Redis кешировать **file_id** (для скорости)
- Логика: попытка отправить через `file_id` → если ошибка → загрузить с диска → обновить кеш

---

## 4. Контракты данных

### 4.1. Payload для ИИ (JSON)

**Формат отправки в OpenRouter API**:

```json
{
  "gender": "female",
  "age": 28,
  "height_cm": 165,
  "weight_kg": 62.0,
  "target_weight_kg": 58.0,
  "activity": "light",
  "body_now": {
    "id": 4,
    "label": "Склонность к животу и бокам"
  },
  "body_ideal": {
    "id": 2,
    "label": "Подтянутая фигура с лёгким рельефом"
  },
  "tz": "Europe/Paris",
  "utc_offset_minutes": 60,
  "goal": "fat_loss",
  "notes": ""
}
```

**Правила сбора**:
- `goal` автоматически определяется:
  - `target_weight_kg < weight_kg` → `"fat_loss"`
  - `target_weight_kg > weight_kg` → `"muscle_gain"`
  - `target_weight_kg == weight_kg` или `None` → `"maintenance"`
- `body_now.label`, `body_ideal.label` — из словаря `BODY_LABELS[gender][stage][id]`
- `utc_offset_minutes` вычисляется на момент отправки (учёт DST)

### 4.2. Формат ответа ИИ (текст)

**Структура блоков** (Telegram-сообщение, Markdown-форматирование):

```
🎯 **Ваш персональный план**

**1. Анализ текущего состояния**
Ваш ИМТ ≈ 22.8 (норма). Текущая фигура: склонность к накоплению жира в области живота и боков. Цель — снижение веса на 4 кг до 58 кг.

**2. Цель и темп**
Здоровый темп снижения веса: 0.3–0.5 кг/нед. Ориентировочный срок: 2–3 месяца.

**3. Тренировки (3–4 р/нед)**
• 2 силовые (всё тело или верх/низ)
• 1–2 кардио (30–40 мин, зона 60–70% ЧСС макс)
• Акцент: приседания, выпады, планки для укрепления кора

**4. Питание**
Ориентировочный диапазон: **≈ 1400–1600 ккал/сут**.
Распределение: белки ≈ 25–30%, жиры ≈ 25–30%, углеводы ≈ 40–50%.
Приоритет: цельные продукты, овощи, достаточное количество белка (≈ 90–110 г/сут).

⚠️ **Точные цифры индивидуальны — для точного расчёта обратитесь к тренеру.**

**5. Ежедневная активность**
Шаги: 8000–10000/сут. Добавьте прогулки, лестницы вместо лифта.

**6. Что НЕ делать**
❌ Экстремальные диеты (<1200 ккал)
❌ Кардио >5 р/нед без силовых
❌ Ожидать быстрых результатов (<2 недель)

**7. Таймлайн**
• 2 недели: адаптация, привычка к тренировкам
• 1 месяц: первые изменения (≈ 1.5–2 кг)
• 2–3 месяца: достижение цели 58 кг

**8. Следующий шаг**
Начните с учёта калорий 3–5 дней, чтобы понять текущий рацион. Затем внедряйте тренировки постепенно.
```

**Обязательные элементы**:
1. Диапазон калорий вида `≈ X–Y ккал/сут` (регулярное выражение: `≈?\s*\d{3,5}\s*[–—-]\s*\d{3,5}\s*ккал`)
2. Фраза: `Точные цифры индивидуальны — для точного расчёта обратитесь к тренеру.`

### 4.3. Валидация ответа ИИ

**Регулярные выражения**:

```python
import re

def validate_ai_response(text: str) -> dict:
    """
    Проверяет наличие обязательных элементов в ответе ИИ.
    Возвращает: {"valid": bool, "errors": list}
    """
    errors = []

    # 1. Диапазон калорий
    calorie_pattern = r'≈?\s*\d{3,5}\s*[–—-]\s*\d{3,5}\s*ккал'
    if not re.search(calorie_pattern, text):
        errors.append("Отсутствует диапазон калорий (формат: ≈ X–Y ккал)")

    # 2. Обязательная фраза про тренера
    disclaimer_pattern = r'[Тт]очные цифры индивидуальны.{0,10}для точного расчёта обратитесь к тренеру'
    if not re.search(disclaimer_pattern, text, re.IGNORECASE):
        errors.append("Отсутствует фраза про индивидуальный расчёт и тренера")

    # 3. Проверка на запрещённые паттерны (точные граммы БЖУ)
    exact_macros_pattern = r'\d+\s*г\s*(белк|жир|углевод)'
    if re.search(exact_macros_pattern, text, re.IGNORECASE):
        errors.append("ИИ указал точные граммы БЖУ (запрещено, допустимы только диапазоны)")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
```

---

## 5. Промпт-политика для ИИ (RU)

### 5.1. Системный промпт для агента

**Версия**: `v1.0`
**Модель**: `meta-llama/llama-3.1-70b-instruct` (или аналог с контекстом 8k+)

```markdown
Ты — профессиональный фитнес-консультант, который создаёт персонализированные планы питания и тренировок.

**КРИТИЧЕСКИ ВАЖНО**:
1. Выводи ТОЛЬКО диапазон калорий в формате «≈ X–Y ккал/сут». НИКОГДА не указывай точное значение.
2. ЗАПРЕЩЕНО указывать точные граммы БЖУ (белки/жиры/углеводы). Допустимы ТОЛЬКО диапазоны или проценты (например, "белки ≈ 90–110 г/сут" или "белки ≈ 25–30%").
3. В конце блока питания ОБЯЗАТЕЛЬНО добавь фразу: **"Точные цифры индивидуальны — для точного расчёта обратитесь к тренеру."**

**Формат ответа**:
Сгенерируй план в Markdown-разметке, структура:

1. **Анализ текущего состояния** (1–2 предложения: ИМТ, особенности фигуры, цель)
2. **Цель и темп** (реалистичная скорость изменений, срок)
3. **Тренировки (3–4 р/нед)** (типы тренировок в зависимости от цели: fat_loss/muscle_gain/maintenance)
4. **Питание**:
   - Диапазон калорий: **≈ X–Y ккал/сут**
   - Распределение БЖУ в процентах или диапазонах (не в точных граммах!)
   - Общие рекомендации по продуктам
   - ⚠️ **Точные цифры индивидуальны — для точного расчёта обратитесь к тренеру.**
5. **Ежедневная активность/шаги** (рекомендации NEAT, количество шагов)
6. **Что НЕ делать** (3–4 пункта: частые ошибки для данной цели)
7. **Таймлайн ожиданий** (что происходит через 2 недели, 1 месяц, 2–3 месяца)
8. **Следующий шаг** (с чего начать прямо сейчас)

**Ограничения**:
- Максимум 1600 символов
- Без медицинских диагнозов, лекарств, добавок (только тренировки и питание)
- Учитывай gender, body_now, body_ideal, activity, target_weight_kg
- Тон: дружелюбный, но профессиональный
- Если данных недостаточно → используй безопасные усреднённые рекомендации

**Входные данные** (JSON):
{user_data}
```

### 5.2. Пример запроса к OpenRouter API

```python
import httpx
import os

async def generate_plan(payload: dict) -> str:
    """
    Генерирует персональный план через OpenRouter API.
    """
    system_prompt = """Ты — профессиональный фитнес-консультант..."""  # (см. выше)

    user_message = f"""Создай персональный план для пользователя:

Данные:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Следуй всем правилам из системного промпта."""

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"),
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-70b-instruct"),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
```

---

## 6. TZ-шаг (часовой пояс)

### 6.1. UI для выбора часового пояса

**Сообщение**:
```
🌍 Укажите ваш часовой пояс:

Это поможет адаптировать рекомендации под ваш режим дня.
```

**InlineKeyboard**:
```
[Европа: Париж (UTC+1)]  [Европа: Москва (UTC+3)]
[Европа: Киев (UTC+2)]   [Азия: Алматы (UTC+5)]
[Азия: Бангкок (UTC+7)]  [США: Нью-Йорк (UTC-5)]
[Другой часовой пояс... ✏️]
```

**Callback-данные**:
```python
InlineKeyboardButton("Европа: Париж (UTC+1)", callback_data="tz:Europe/Paris")
InlineKeyboardButton("Другой часовой пояс... ✏️", callback_data="tz:manual")
```

### 6.2. Валидация и обработка

**Обработчик для кнопок**:
```python
@router.callback_query(F.data.startswith("tz:"), SurveyStates.TZ)
async def process_tz_button(callback: CallbackQuery, state: FSMContext):
    tz_value = callback.data.split(":", 1)[1]

    if tz_value == "manual":
        await callback.message.answer(
            "✏️ Введите часовой пояс вручную в формате IANA (например, Europe/London) "
            "или UTC±N (например, UTC+3):"
        )
        # Остаёмся в состоянии TZ, ждём текстовый ввод
    else:
        # Валидация IANA timezone
        if validate_iana_tz(tz_value):
            offset = get_utc_offset(tz_value)
            await state.update_data(tz=tz_value, utc_offset_minutes=offset)
            await state.set_state(SurveyStates.CONFIRM)
            await show_confirmation(callback.message, state)
        else:
            await callback.answer("❌ Некорректный часовой пояс", show_alert=True)
```

**Обработчик ручного ввода**:
```python
@router.message(SurveyStates.TZ)
async def process_tz_manual(message: Message, state: FSMContext):
    tz_input = message.text.strip()

    # Попытка 1: IANA timezone
    if validate_iana_tz(tz_input):
        offset = get_utc_offset(tz_input)
        await state.update_data(tz=tz_input, utc_offset_minutes=offset)
        await state.set_state(SurveyStates.CONFIRM)
        await show_confirmation(message, state)
        return

    # Попытка 2: UTC±N → маппинг на IANA
    utc_match = re.match(r'UTC([+-]\d{1,2})', tz_input, re.IGNORECASE)
    if utc_match:
        offset_hours = int(utc_match.group(1))
        iana_tz = map_utc_to_iana(offset_hours)  # Например, UTC+3 → Europe/Moscow
        offset_minutes = offset_hours * 60
        await state.update_data(tz=iana_tz, utc_offset_minutes=offset_minutes)
        await state.set_state(SurveyStates.CONFIRM)
        await show_confirmation(message, state)
        return

    # Ошибка
    await message.answer(
        "❌ Некорректный формат. Примеры:\n"
        "• Europe/London\n"
        "• Asia/Tokyo\n"
        "• UTC+3\n"
        "• UTC-5"
    )
```

### 6.3. Валидация и вычисление offset

```python
from datetime import datetime
import pytz

def validate_iana_tz(tz_name: str) -> bool:
    """Проверяет корректность IANA timezone."""
    try:
        pytz.timezone(tz_name)
        return True
    except pytz.UnknownTimeZoneError:
        return False

def get_utc_offset(tz_name: str) -> int:
    """
    Вычисляет текущий UTC offset в минутах для заданного часового пояса.
    Учитывает DST (летнее время).
    """
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)
    offset_seconds = now.utcoffset().total_seconds()
    return int(offset_seconds / 60)

def map_utc_to_iana(offset_hours: int) -> str:
    """
    Маппинг UTC±N на популярные IANA timezones.
    Упрощённая версия для основных поясов.
    """
    mapping = {
        -5: "America/New_York",
        -8: "America/Los_Angeles",
        0: "Europe/London",
        1: "Europe/Paris",
        2: "Europe/Kyiv",
        3: "Europe/Moscow",
        5: "Asia/Yekaterinburg",
        7: "Asia/Bangkok",
        8: "Asia/Shanghai",
        9: "Asia/Tokyo"
    }
    return mapping.get(offset_hours, f"Etc/GMT{-offset_hours:+d}")
```

### 6.4. Использование в БД и будущих фичах

**Сохранение**:
```python
# В survey_answers
tz = "Europe/Paris"
utc_offset_minutes = 60  # для конкретной даты опроса
```

**Будущие применения**:
- Отправка уведомлений в удобное время (например, напоминание записать калории в 20:00 по местному времени)
- Аналитика активности по часовым поясам
- Адаптация рекомендаций тренировок (утро/вечер в зависимости от часового пояса)

---

## 7. Feature-flag и безопасное внедрение

### 7.1. Конфигурация через ENV

**Файл `.env`**:
```bash
# Feature Flags
FEATURE_PERSONAL_PLAN=on  # on | off
```

**Загрузка в коде**:
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... другие настройки

    # Feature Flags
    FEATURE_PERSONAL_PLAN: str = "off"  # По умолчанию выключена

    @property
    def is_personal_plan_enabled(self) -> bool:
        return self.FEATURE_PERSONAL_PLAN.lower() == "on"

    class Config:
        env_file = ".env"

settings = Settings()
```

### 7.2. Условная регистрация хендлеров

**Файл `bot/handlers/__init__.py`**:
```python
from aiogram import Dispatcher
from bot.config import settings

def register_all_handlers(dp: Dispatcher):
    # Основные хендлеры (всегда активны)
    from bot.handlers import common, calories, menu
    dp.include_router(common.router)
    dp.include_router(calories.router)
    dp.include_router(menu.router)

    # Условно регистрируем Personal Plan
    if settings.is_personal_plan_enabled:
        from bot.handlers import personal_plan
        dp.include_router(personal_plan.router)
        print("✅ Personal Plan feature enabled")
    else:
        print("⚠️ Personal Plan feature disabled")
```

### 7.3. Условное отображение в меню

**Файл `bot/keyboards/main_menu.py`**:
```python
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.config import settings

def get_main_menu() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📊 Учёт калорий")],
        [KeyboardButton(text="📈 Статистика")],
    ]

    if settings.is_personal_plan_enabled:
        buttons.insert(1, [KeyboardButton(text="🎯 Получить персональный план")])

    buttons.append([KeyboardButton(text="⚙️ Настройки")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
```

### 7.4. Путь отката

**Сценарий**: Обнаружена критическая ошибка в новой фиче после деплоя.

**Действия**:
1. Изменить `.env`: `FEATURE_PERSONAL_PLAN=off`
2. Перезапустить бота: `systemctl restart telegram-bot` (или Docker restart)
3. Проверить:
   - Кнопка "Персональный план" исчезла из меню
   - Старые хендлеры работают без изменений
   - FSM-состояния для незавершённых опросов автоматически истекают (TTL 30 мин)

**Никаких изменений в коде не требуется** — просто переключение флага.

---

## 8. Acceptance Criteria и Test Plan

### 8.1. Acceptance Criteria

**AC-1: Корректный показ изображений по полу и этапу**
- [ ] При выборе пола "Женский" на шаге BODY_NOW показываются 5 изображений (`female_now_1..5.jpg`)
- [ ] При выборе пола "Мужской" на шаге BODY_NOW показываются 4 изображения (`male_now_1..4.jpg`)
- [ ] На шаге BODY_IDEAL для обоих полов показываются 3 изображения
- [ ] Каждое изображение отправляется отдельным сообщением с подписью и кнопкой "✅ Выбрать"

**AC-2: Выбор ровно одного варианта на шаг**
- [ ] После нажатия кнопки "Выбрать" все сообщения с вариантами удаляются
- [ ] Показывается подтверждение выбора: "Вы выбрали: Вариант N — <описание>"
- [ ] Нельзя выбрать несколько вариантов одновременно

**AC-3: Смена пола → сброс выборов фигуры**
- [ ] Если пользователь вернулся на шаг GENDER и изменил пол
- [ ] То выборы `body_now_id` и `body_ideal_id` из FSM state удаляются
- [ ] При повторном достижении BODY_NOW/BODY_IDEAL показываются правильные наборы картинок

**AC-4: Обязательное наличие диапазона калорий и фразы про тренера**
- [ ] Ответ ИИ содержит паттерн `≈ X–Y ккал/сут` (регулярное выражение проходит)
- [ ] Ответ ИИ содержит фразу "Точные цифры индивидуальны — для точного расчёта обратитесь к тренеру."
- [ ] Если валидация провалена → логируется ошибка, пользователю показывается fallback-сообщение

**AC-5: Сохранение данных в БД**
- [ ] После подтверждения создаётся запись в `survey_answers` со всеми полями
- [ ] После генерации плана создаётся запись в `plans` с `ai_text`, `ai_model`, `prompt_version`
- [ ] Поля `tz` и `utc_offset_minutes` корректно заполнены (offset вычислен на текущую дату)
- [ ] `survey_answers.completed_at` устанавливается в момент сохранения

**AC-6: Обработка недоступности изображения**
- [ ] При `FileNotFoundError` логируется ошибка
- [ ] Повторная попытка отправки через 2 сек (макс. 3 попытки)
- [ ] Если все попытки неудачны → показать "Изображение временно недоступно", пропустить этот вариант

### 8.2. Test Plan

#### 8.2.1. Функциональные тесты

**Тест 1: Полный проход опроса (happy path)**
```
Шаги:
1. /start → нажать "🎯 Получить персональный план"
2. Выбрать пол: Женский
3. Ввести возраст: 28
4. Ввести рост: 165
5. Ввести вес: 62
6. Ввести целевой вес: 58
7. Выбрать активность: Лёгкая
8. Выбрать BODY_NOW: Вариант 4
9. Выбрать BODY_IDEAL: Вариант 2
10. Выбрать часовой пояс: Europe/Paris
11. Подтвердить данные
12. Дождаться ответа ИИ

Ожидаемый результат:
- Все шаги проходятся без ошибок
- Изображения показываются корректно (5 для BODY_NOW, 3 для BODY_IDEAL)
- Ответ ИИ содержит диапазон калорий и фразу про тренера
- В БД созданы записи в survey_answers и plans
```

**Тест 2: Возврат назад и изменение данных**
```
Шаги:
1. Пройти до шага ACTIVITY
2. Нажать "◀️ Назад"
3. Изменить вес с 62 на 65
4. Продолжить опрос до конца

Ожидаемый результат:
- Возврат работает корректно
- Новое значение веса сохраняется в FSM state
- В итоговом подтверждении отображается 65 кг
```

**Тест 3: Смена пола и сброс выборов**
```
Шаги:
1. Выбрать пол: Женский
2. Пройти до BODY_NOW, выбрать вариант 3
3. Вернуться назад до GENDER
4. Изменить пол на Мужской
5. Пройти до BODY_NOW

Ожидаемый результат:
- body_now_id сброшен
- Показываются 4 мужских варианта (male_now_1..4.jpg)
- Нельзя случайно отправить женский вариант
```

**Тест 4: Пропуск целевого веса**
```
Шаги:
1. Пройти опрос, на шаге TARGET_WEIGHT нажать "Пропустить"
2. Завершить опрос

Ожидаемый результат:
- target_weight_kg = NULL в БД
- ИИ определяет goal как "maintenance"
- План корректно формируется без упоминания снижения/набора веса
```

**Тест 5: Ручной ввод часового пояса**
```
Шаги:
1. На шаге TZ нажать "Другой часовой пояс..."
2. Ввести "UTC+8"
3. Продолжить

Ожидаемый результат:
- Система маппит на Asia/Shanghai
- utc_offset_minutes = 480
- Сохранено в БД
```

#### 8.2.2. Пограничные случаи

**Тест 6: Экстремальные значения**
```
Входные данные:
- Возраст: 14 (минимум), 80 (максимум)
- Рост: 120 см (минимум), 250 см (максимум)
- Вес: 30 кг (минимум), 300 кг (максимум)

Ожидаемый результат:
- Валидация проходит
- ИИ даёт безопасные рекомендации (без экстремальных диет)
```

**Тест 7: Некорректный ввод**
```
Входные данные:
- Возраст: "abc", -5, 150
- Рост: "высокий", 50
- Вес: "много", 0

Ожидаемый результат:
- Показывается сообщение об ошибке с примером
- Пользователь остаётся на том же шаге FSM
```

**Тест 8: Недоступность OpenRouter API**
```
Сценарий:
1. Временно отключить интернет / указать неверный API ключ
2. Завершить опрос и подтвердить

Ожидаемый результат:
- Показывается "⚠️ Не удалось сгенерировать план. Попробуйте позже."
- В БД создаётся survey_answers, но НЕ создаётся plans
- Логируется ошибка с деталями (HTTPError, timeout)
```

**Тест 9: Ответ ИИ без диапазона калорий**
```
Сценарий:
1. Мокировать ответ ИИ, который не содержит "≈ X–Y ккал"
2. Отправить запрос

Ожидаемый результат:
- Валидация провалена
- Пользователю показывается fallback-сообщение:
  "⚠️ План сгенерирован, но требует проверки. Обратитесь к администратору."
- План сохраняется в БД, но помечается флагом (опц. поле validation_failed)
```

#### 8.2.3. Производительность и нагрузка

**Тест 10: Скорость отправки изображений**
```
Условия:
- Измерить время отправки 5 изображений на шаге BODY_NOW

Ожидаемый результат:
- При использовании file_id: <2 сек на все 5 изображений
- При загрузке с диска: <5 сек на все 5 изображений
```

**Тест 11: Параллельные запросы к ИИ**
```
Условия:
- 10 пользователей одновременно завершают опрос

Ожидаемый результат:
- Все запросы обрабатываются без ошибок
- Timeout для OpenRouter API: 30 сек
- Нет блокировок БД при записи plans
```

---

## 9. Ассеты и нейминг

### 9.1. Структура директории

```
assets/
└── body_types/
    ├── female/
    │   ├── now/
    │   │   ├── female_now_1.jpg  # Вариант 1: Равномерное распределение
    │   │   ├── female_now_2.jpg  # Вариант 2: Склонность к бёдрам
    │   │   ├── female_now_3.jpg  # Вариант 3: Склонность к верху
    │   │   ├── female_now_4.jpg  # Вариант 4: Склонность к животу и бокам
    │   │   └── female_now_5.jpg  # Вариант 5: Полная фигура
    │   └── ideal/
    │       ├── female_ideal_1.jpg  # Идеал 1: Стройная
    │       ├── female_ideal_2.jpg  # Идеал 2: Подтянутая с рельефом
    │       └── female_ideal_3.jpg  # Идеал 3: Атлетическая
    └── male/
        ├── now/
        │   ├── male_now_1.jpg  # Вариант 1: Худощавый
        │   ├── male_now_2.jpg  # Вариант 2: Средний
        │   ├── male_now_3.jpg  # Вариант 3: Склонность к животу
        │   └── male_now_4.jpg  # Вариант 4: Крупный
        └── ideal/
            ├── male_ideal_1.jpg  # Идеал 1: Поджарый
            ├── male_ideal_2.jpg  # Идеал 2: Атлетический
            └── male_ideal_3.jpg  # Идеал 3: Массивный
```

### 9.2. Соответствие ID ↔ имя файла

**Правило**: `ID варианта = номер в имени файла`

Примеры:
- Callback `body_now_3` → файл `female_now_3.jpg` или `male_now_3.jpg` (в зависимости от пола)
- Callback `body_ideal_2` → файл `female_ideal_2.jpg` или `male_ideal_2.jpg`

**Код маппинга**:
```python
def get_body_image_path(gender: str, stage: str, variant_id: int) -> str:
    """
    Возвращает относительный путь к изображению типа фигуры.

    Args:
        gender: "male" | "female"
        stage: "now" | "ideal"
        variant_id: номер варианта (1, 2, 3, ...)

    Returns:
        Путь вида "assets/body_types/female/now/female_now_3.jpg"
    """
    return f"assets/body_types/{gender}/{stage}/{gender}_{stage}_{variant_id}.jpg"
```

### 9.3. Словарь подписей (BODY_LABELS)

```python
BODY_LABELS = {
    "female": {
        "now": {
            1: "Равномерное распределение",
            2: "Склонность к бёдрам и ягодицам",
            3: "Склонность к верхней части тела",
            4: "Склонность к животу и бокам",
            5: "Полная фигура"
        },
        "ideal": {
            1: "Стройная фигура",
            2: "Подтянутая с лёгким рельефом",
            3: "Атлетическая с выраженными мышцами"
        }
    },
    "male": {
        "now": {
            1: "Худощавый, минимум жира",
            2: "Средний, пропорциональный",
            3: "Склонность к животу",
            4: "Крупный, значительный избыток веса"
        },
        "ideal": {
            1: "Поджарый с видимым прессом",
            2: "Атлетический, развитая мускулатура",
            3: "Массивный, максимум мышц"
        }
    }
}
```

### 9.4. Рекомендации по изображениям

**Размеры**:
- Разрешение: 800×1200 px (портретная ориентация)
- Формат: JPEG, качество 85%
- Вес файла: <200 КБ на изображение

**Стиль**:
- Схематичные иллюстрации (не фотографии реальных людей)
- Нейтральная цветовая гамма (серый, бежевый)
- Акцент на силуэт, без детализации лица
- Можно использовать сервисы: Midjourney, DALL-E, Stable Diffusion (промпт: "body type silhouette illustration, neutral colors, front view")

**Нумерация на изображении**:
- НЕ добавлять цифры на само изображение
- Номер передаётся через подпись в Telegram: `caption=f"Вариант {i}: {BODY_LABELS[gender][stage][i]}"`

---

## 10. Инкременты задач на 1–2 дня

### День 1: Фундамент (8 часов)

**Задача 1.1: Миграции БД** (1 ч)
- Создать Alembic миграцию `001_create_survey_tables.py`
- Добавить поля `tz`, `utc_offset_minutes` в `users`
- Создать таблицы `survey_answers`, `plans`, `events`
- Запустить миграцию: `alembic upgrade head`
- Проверить структуру: `psql -d bot_db -c "\d survey_answers"`

**Задача 1.2: FSM-опрос (базовый скелет)** (2 ч)
- Создать `bot/states/survey.py` с `SurveyStates`
- Создать хендлер входа: `/personal_plan` → `SurveyStates.GENDER`
- Реализовать шаги: GENDER → AGE → HEIGHT → WEIGHT (только текстовый ввод, без изображений)
- Добавить кнопку "◀️ Назад" на каждый шаг
- Проверить переходы между состояниями

**Задача 1.3: Словари и константы** (0.5 ч)
- Создать `bot/constants/survey.py`:
  - `BODY_LABELS` (подписи для вариантов фигур)
  - `ACTIVITY_LEVELS` (уровни активности)
  - `BODY_COUNTS` (количество вариантов по полу и стадии)
- Создать `bot/utils/paths.py`:
  - Функция `get_body_image_path(gender, stage, variant_id)`

**Задача 1.4: Валидаторы** (1 ч)
- Создать `bot/validators/survey.py`:
  - `validate_age(text: str) -> int | None`
  - `validate_height(text: str) -> int | None`
  - `validate_weight(text: str) -> float | None`
  - `validate_iana_tz(tz: str) -> bool`
- Добавить сообщения об ошибках с примерами

**Задача 1.5: Feature-flag** (0.5 ч)
- Добавить в `.env`: `FEATURE_PERSONAL_PLAN=on`
- Обновить `bot/config.py`: добавить `is_personal_plan_enabled`
- Условная регистрация роутера в `bot/handlers/__init__.py`
- Условная кнопка в главном меню

**Задача 1.6: README и требования** (1 ч)
- Обновить `README.md`: описание новой фичи
- Создать `requirements.txt`:
  - `aiogram==3.x`
  - `sqlalchemy[asyncio]`
  - `asyncpg`
  - `alembic`
  - `pytz`
  - `httpx`
  - `pydantic-settings`
- Создать `.env.example` с переменными OpenRouter

**Задача 1.7: Подготовка ассетов (заглушки)** (1 ч)
- Создать структуру `assets/body_types/female/now/`, `male/ideal/` и т.д.
- Добавить временные изображения-плейсхолдеры (можно сгенерировать простые цветные квадраты 800×1200 с текстом "Вариант 1", "Вариант 2")
- Проверить, что файлы доступны из кода

**Задача 1.8: Логирование и события** (1 ч)
- Создать `bot/services/events.py`:
  - Функция `log_event(user_id, event, payload)` → запись в таблицу `events`
- Добавить логирование:
  - `survey_started`
  - `survey_step_completed:{step_name}`
  - `survey_cancelled`

---

### День 2: Изображения и навигация (8 часов)

**Задача 2.1: Отправка отдельных изображений** (3 ч)
- Создать `bot/services/image_sender.py`:
  - Функция `send_body_type_options(chat_id, gender, stage, bot)`:
    - Отправить заголовок
    - Последовательно отправить N изображений (FSInputFile)
    - Под каждым изображением InlineKeyboard с кнопкой "✅ Выбрать"
    - Вернуть список `message_id` отправленных сообщений
- Реализовать удаление сообщений после выбора
- Обработать ошибку `FileNotFoundError` (повтор 3 раза, fallback)

**Задача 2.2: Хендлеры BODY_NOW и BODY_IDEAL** (2 ч)
- Реализовать шаг BODY_NOW:
  - Вызвать `send_body_type_options(..., stage="now")`
  - Callback `body_now_{id}` → сохранить в FSM, показать подтверждение, перейти к BODY_IDEAL
- Реализовать шаг BODY_IDEAL аналогично
- Добавить логику сброса при смене пола (проверка в хендлере GENDER)

**Задача 2.3: Кеширование file_id (опционально)** (1.5 ч)
- Создать `bot/services/image_cache.py`:
  - Redis-клиент для хранения `{gender}_{stage}_{id}` → `file_id`
  - Функция `get_cached_file_id(key)` и `cache_file_id(key, file_id, ttl=2592000)`  # 30 дней
- Модифицировать `image_sender.py`:
  - Попытка отправить через `file_id`
  - При ошибке → загрузка с диска, обновление кеша
- Fallback на MemoryStorage, если Redis недоступен

**Задача 2.4: Шаги TARGET_WEIGHT, ACTIVITY, TZ** (1.5 ч)
- TARGET_WEIGHT:
  - Кнопки: "Ввести вес" | "Пропустить"
  - Валидация: `target_weight_kg` должен отличаться от `weight_kg`
- ACTIVITY:
  - InlineKeyboard с 5 кнопками (sedentary, light, moderate, active, very_active)
- TZ:
  - Кнопки популярных зон + "Другой..."
  - Обработчик ручного ввода (IANA или UTC±N)
  - Вычисление `utc_offset_minutes` через `pytz`

---

### День 3: Интеграция ИИ (6 часов)

**Задача 3.1: Модуль OpenRouter** (2 ч)
- Создать `bot/services/ai/openrouter.py`:
  - Класс `OpenRouterClient`:
    - `__init__(base_url, api_key, model, timeout=30)`
    - `async def generate_plan(payload: dict) -> str`
  - Обработка ошибок: `httpx.HTTPStatusError`, `httpx.TimeoutException`
  - Логирование запросов и ответов

**Задача 3.2: Промпт для ИИ** (1 ч)
- Создать `bot/prompts/personal_plan.py`:
  - Системный промпт (версия v1.0) с правилами:
    - Диапазон калорий
    - Запрет на точные граммы БЖУ
    - Обязательная фраза про тренера
  - Функция `build_user_message(payload: dict) -> str`

**Задача 3.3: Валидация ответа ИИ** (1 ч)
- Создать `bot/validators/ai_response.py`:
  - Функция `validate_ai_response(text: str) -> dict`:
    - Проверка наличия диапазона калорий (regex)
    - Проверка фразы про тренера (regex)
    - Проверка на запрещённые паттерны (точные граммы БЖУ)
  - Возврат: `{"valid": bool, "errors": list}`

**Задача 3.4: Шаг CONFIRM и GENERATE** (2 ч)
- CONFIRM:
  - Сформировать сообщение с итоговыми данными (пол, возраст, рост, вес, активность, типы фигур, часовой пояс)
  - Кнопки: "Всё верно ✅" | "Изменить ✏️"
- GENERATE:
  - Callback "confirm_yes" → `state.set_state(SurveyStates.GENERATE)`
  - Показать "⏳ Генерирую план..."
  - Собрать payload для ИИ
  - Вызвать `OpenRouterClient.generate_plan(payload)`
  - Валидация ответа
  - Сохранение в БД: `survey_answers`, `plans`
  - Показать результат пользователю
  - Финальная подсказка: "Вернуться к учёту: /calories"

---

### День 4: Полировка и тестирование (6 часов)

**Задача 4.1: Тексты бота** (1 ч)
- Создать `bot/texts/survey.py`:
  - Приветствие для `/personal_plan`
  - Тексты для каждого шага (GENDER, AGE, HEIGHT, и т.д.)
  - Сообщения об ошибках
  - Текст подтверждения
  - Шапка перед ответом ИИ: "🎯 Ваш персональный план"
  - Финальная подсказка

**Задача 4.2: UX-улучшения** (2 ч)
- Кнопка "Посмотреть ещё раз" на шагах BODY_NOW/BODY_IDEAL (повторная отправка изображений)
- При повторном входе в шаг показывать текущий выбор: "Вы выбрали: Вариант 2"
- Добавить индикатор прогресса: "Шаг 3 из 9"
- Улучшить форматирование подтверждения (эмодзи, выравнивание)

**Задача 4.3: Обработка ошибок** (1.5 ч)
- Недоступность изображения → fallback-сообщение, повтор
- Timeout OpenRouter API → сообщение "Попробуйте позже"
- Некорректный ответ ИИ (валидация провалена) → fallback-план или сообщение администратору
- Ошибка записи в БД → логирование, уведомление пользователю

**Задача 4.4: Ручное тестирование** (1.5 ч)
- Пройти полный опрос (happy path)
- Проверить возврат назад на каждом шаге
- Протестировать смену пола и сброс выборов
- Протестировать пропуск целевого веса
- Протестировать ручной ввод часового пояса
- Проверить корректность данных в БД

---

## 11. Definition of Done (DoD) Checklist

### Код

- [ ] Все миграции Alembic созданы и успешно применены
- [ ] FSM-сценарий реализован со всеми 10 шагами + навигация "Назад"
- [ ] Изображения типов фигуры отправляются отдельными сообщениями (не коллажами)
- [ ] Логика смены пола → сброс выборов body_now/body_ideal работает
- [ ] Feature-flag `FEATURE_PERSONAL_PLAN` реализован и тестирован (вкл/выкл)
- [ ] Интеграция с OpenRouter API работает (env: BASE_URL, API_KEY, MODEL)
- [ ] Системный промпт для ИИ содержит правила про диапазон калорий и дисклеймер
- [ ] Валидация ответа ИИ (regex для калорий + фраза про тренера) реализована
- [ ] Часовой пояс: кнопки популярных IANA + ручной ввод + вычисление offset
- [ ] Данные сохраняются в БД: `survey_answers` (все поля + tz/offset), `plans` (ai_text, ai_model, prompt_version)

### Качество кода

- [ ] Код следует PEP 8 (проверка через `flake8` или `ruff`)
- [ ] Типизация добавлена для всех функций (type hints)
- [ ] Нет хардкода: все магические значения вынесены в константы/конфиг
- [ ] Логирование настроено для всех критичных операций (ошибки ИИ, БД, отправка изображений)
- [ ] Обработка исключений для всех внешних вызовов (OpenRouter, Telegram API, БД)

### Тестирование

- [ ] Пройдены все функциональные тесты из Test Plan (раздел 8.2.1)
- [ ] Пройдены все тесты пограничных случаев (раздел 8.2.2)
- [ ] Feature-flag протестирован: вкл → фича доступна, выкл → старый бот без изменений
- [ ] Ручное тестирование полного опроса с разными комбинациями (мужчины/женщины, с/без целевого веса)
- [ ] Проверка на недоступность изображений (удалить файл → проверить fallback)

### Документация

- [ ] `README.md` обновлён: описание фичи, как включить/выключить
- [ ] `requirements.txt` содержит все зависимости (aiogram, httpx, pytz, и т.д.)
- [ ] `.env.example` содержит переменные для OpenRouter и feature-flag
- [ ] Комментарии в коде для сложных участков (валидация, маппинг UTC→IANA)

### БД и миграции

- [ ] Alembic миграции применяются без ошибок (upgrade и downgrade)
- [ ] Индексы созданы для всех FK и часто используемых полей (user_id, completed_at)
- [ ] Ограничения CHECK работают корректно (возраст 14–80, вес 30–300, и т.д.)

### Деплой

- [ ] Feature-flag выключен по умолчанию в production до полного тестирования
- [ ] Rollback-процедура документирована (выключить флаг → перезапуск)
- [ ] Логи настроены для мониторинга (события survey_started, survey_completed, plan_generated)

---

## 12. Первый дневной спринт (День 1, детализация)

**Цель**: К концу дня получить работающий скелет опроса (без изображений, без ИИ) с базовой навигацией и сохранением в БД.

### Утро (4 часа)

**09:00–10:00: Подготовка окружения**
1. Создать ветку: `git checkout -b feature/personal-plan`
2. Обновить зависимости:
   ```bash
   pip install aiogram==3.14.0 sqlalchemy[asyncio] asyncpg alembic pytz httpx pydantic-settings
   pip freeze > requirements.txt
   ```
3. Создать `.env.example`:
   ```bash
   # Feature Flags
   FEATURE_PERSONAL_PLAN=off

   # OpenRouter API
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_MODEL=meta-llama/llama-3.1-70b-instruct
   ```
4. Скопировать в `.env`, установить `FEATURE_PERSONAL_PLAN=on`

**10:00–11:00: Миграции БД**
1. Создать миграцию:
   ```bash
   alembic revision -m "create_survey_tables"
   ```
2. Заполнить файл миграции (см. раздел 3.2)
3. Применить:
   ```bash
   alembic upgrade head
   ```
4. Проверить в БД:
   ```sql
   \d survey_answers
   \d plans
   \d events
   ```

**11:00–12:00: FSM-состояния и константы**
1. Создать `bot/states/survey.py`:
   ```python
   from aiogram.fsm.state import State, StatesGroup

   class SurveyStates(StatesGroup):
       GENDER = State()
       AGE = State()
       HEIGHT = State()
       WEIGHT = State()
       TARGET_WEIGHT = State()
       ACTIVITY = State()
       BODY_NOW = State()
       BODY_IDEAL = State()
       TZ = State()
       CONFIRM = State()
       GENERATE = State()
   ```
2. Создать `bot/constants/survey.py` с `BODY_LABELS`, `ACTIVITY_LEVELS`
3. Создать `bot/utils/paths.py` с `get_body_image_path()`

**12:00–13:00: Обед**

### День (4 часа)

**13:00–15:00: Базовые хендлеры (GENDER, AGE, HEIGHT, WEIGHT)**
1. Создать `bot/handlers/personal_plan.py`:
   ```python
   from aiogram import Router, F
   from aiogram.filters import Command
   from aiogram.types import Message, CallbackQuery
   from aiogram.fsm.context import FSMContext
   from bot.states.survey import SurveyStates

   router = Router(name="personal_plan")

   @router.message(Command("personal_plan"))
   async def start_survey(message: Message, state: FSMContext):
       await state.set_state(SurveyStates.GENDER)
       await message.answer(
           "🎯 Создадим ваш персональный план!\n\n"
           "Выберите ваш пол:",
           reply_markup=get_gender_keyboard()
       )

   @router.callback_query(F.data.in_(["gender_male", "gender_female"]), SurveyStates.GENDER)
   async def process_gender(callback: CallbackQuery, state: FSMContext):
       gender = callback.data.split("_")[1]  # "male" или "female"
       await state.update_data(gender=gender)
       await state.set_state(SurveyStates.AGE)
       await callback.message.answer("Отлично! Укажите ваш возраст (14–80 лет):")

   # Аналогично для AGE, HEIGHT, WEIGHT...
   ```
2. Создать клавиатуры: `bot/keyboards/survey.py`
3. Добавить валидаторы: `bot/validators/survey.py`

**15:00–16:00: Навигация "Назад"**
1. Добавить кнопку "◀️ Назад" во все клавиатуры (кроме GENDER)
2. Реализовать хендлер:
   ```python
   @router.callback_query(F.data == "back", SurveyStates.AGE)
   async def back_from_age(callback: CallbackQuery, state: FSMContext):
       await state.set_state(SurveyStates.GENDER)
       await callback.message.answer("Выберите пол:", reply_markup=get_gender_keyboard())
   ```
3. Добавить универсальный хендлер для "Отменить":
   ```python
   @router.callback_query(F.data == "cancel")
   async def cancel_survey(callback: CallbackQuery, state: FSMContext):
       await state.clear()
       await callback.message.answer("Опрос отменён. Введите /menu для возврата.")
   ```

**16:00–17:00: Feature-flag и интеграция**
1. Обновить `bot/config.py`:
   ```python
   class Settings(BaseSettings):
       FEATURE_PERSONAL_PLAN: str = "off"

       @property
       def is_personal_plan_enabled(self) -> bool:
           return self.FEATURE_PERSONAL_PLAN.lower() == "on"
   ```
2. Обновить `bot/handlers/__init__.py`:
   ```python
   def register_all_handlers(dp: Dispatcher):
       # ... существующие хендлеры

       if settings.is_personal_plan_enabled:
           from bot.handlers import personal_plan
           dp.include_router(personal_plan.router)
   ```
3. Обновить главное меню: добавить кнопку "🎯 Получить персональный план" (условно)

### Вечер (2 часа)

**17:00–18:00: Подготовка ассетов (заглушки)**
1. Создать структуру директорий:
   ```bash
   mkdir -p assets/body_types/female/{now,ideal}
   mkdir -p assets/body_types/male/{now,ideal}
   ```
2. Сгенерировать временные изображения (Python-скрипт):
   ```python
   from PIL import Image, ImageDraw, ImageFont

   def create_placeholder(gender, stage, variant_id):
       img = Image.new('RGB', (800, 1200), color=(200, 200, 200))
       draw = ImageDraw.Draw(img)
       text = f"{gender.capitalize()}\n{stage.capitalize()}\nВариант {variant_id}"
       draw.text((400, 600), text, fill=(0, 0, 0), anchor="mm")
       img.save(f"assets/body_types/{gender}/{stage}/{gender}_{stage}_{variant_id}.jpg")

   for gender in ["female", "male"]:
       for stage in ["now", "ideal"]:
           count = 5 if (gender == "female" and stage == "now") else (4 if (gender == "male" and stage == "now") else 3)
           for i in range(1, count + 1):
               create_placeholder(gender, stage, i)
   ```
3. Проверить наличие файлов

**18:00–19:00: Тестирование и commit**
1. Запустить бота:
   ```bash
   python -m bot
   ```
2. Протестировать:
   - `/personal_plan` → выбор пола → ввод возраста → ввод роста → ввод веса
   - Кнопка "Назад" с шага AGE → возврат на GENDER
   - Кнопка "Отменить" → очистка FSM
3. Проверить переключение feature-flag:
   - `.env`: `FEATURE_PERSONAL_PLAN=off` → перезапуск → кнопка исчезла из меню
   - `.env`: `FEATURE_PERSONAL_PLAN=on` → кнопка появилась
4. Commit:
   ```bash
   git add .
   git commit -m "feat: basic survey flow (GENDER->WEIGHT) with FSM and feature-flag"
   git push origin feature/personal-plan
   ```

**Результат Дня 1**:
- ✅ БД готова (миграции применены)
- ✅ FSM работает для первых 4 шагов (GENDER, AGE, HEIGHT, WEIGHT)
- ✅ Навигация "Назад" и "Отменить" функционирует
- ✅ Feature-flag интегрирован и протестирован
- ✅ Заглушки изображений созданы
- ✅ Код в репозитории

**Следующий день**: Реализация шагов с изображениями (BODY_NOW, BODY_IDEAL) и остальных шагов (TARGET_WEIGHT, ACTIVITY, TZ, CONFIRM).

---

## Конец Roadmap

**Статус документа**: Готов к реализации
**Следующий шаг**: Запросите дополнительные файлы (структуру репозитория, системный промпт, тексты бота) в отдельном сообщении.

