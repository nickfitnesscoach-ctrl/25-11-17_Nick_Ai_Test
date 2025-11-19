# Интеграция aiogram бота с Django FoodMind AI

## Быстрый старт

Твой бот уже работает на сервере. Нужно добавить **одну функцию** для отправки данных в Django.

---

## 1. Добавь эту функцию в свой бот

```python
import httpx

# URL твоего Django API (локально через ngrok или на сервере)
DJANGO_API_URL = "http://localhost:8000/api/v1"  # Замени на ngrok URL для тестов

async def send_test_results_to_django(user, answers, kbzu):
    """
    Отправляет результаты AI теста в Django.

    Args:
        user: Telegram User object
        answers: dict с ответами пользователя
        kbzu: dict с расчитанными КБЖУ

    Example answers:
        {
            "age": 25,
            "gender": "M",  # или "F"
            "weight": 75,   # кг
            "height": 180,  # см
            "activity_level": "moderately_active",  # sedentary, lightly_active, moderately_active, very_active, extra_active
            "goal": "weight_loss"  # weight_loss, maintenance, weight_gain
        }

    Example kbzu:
        {
            "calories": 2100,
            "protein": 130,
            "fat": 70,
            "carbs": 240
        }
    """
    url = f"{DJANGO_API_URL}/telegram/save-test/"

    payload = {
        "telegram_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name or "",
        "username": user.username or "",
        "answers": answers,
        "calculated_kbzu": kbzu
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()

            result = response.json()
            print(f"✅ Данные сохранены в Django: user_id={result.get('user_id')}")
            return result

    except Exception as e:
        print(f"❌ Ошибка отправки в Django: {e}")
        return None
```

---

## 2. Вызови эту функцию после завершения теста

```python
from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# Твой existing код для завершения теста...

@router.callback_query(F.data == "finish_test")
async def finish_ai_test(callback: CallbackQuery, state: FSMContext):
    """Завершение AI теста и отображение результатов."""

    # Получаем данные из state (твой existing код)
    data = await state.get_data()

    # Твоя existing логика расчета КБЖУ
    answers = {
        "age": data.get("age"),
        "gender": data.get("gender"),
        "weight": data.get("weight"),
        "height": data.get("height"),
        "activity_level": data.get("activity_level"),
        "goal": data.get("goal")
    }

    kbzu = {
        "calories": data.get("calculated_calories", 2000),
        "protein": data.get("calculated_protein", 100),
        "fat": data.get("calculated_fat", 60),
        "carbs": data.get("calculated_carbs", 200)
    }

    # ✅ НОВОЕ: Отправляем в Django
    await send_test_results_to_django(callback.from_user, answers, kbzu)

    # Твой existing код для показа результатов
    message_text = f"""
✅ Твой персональный план готов!

📊 Норма калорий: {kbzu['calories']} ккал/день
• Белки: {kbzu['protein']}г
• Жиры: {kbzu['fat']}г
• Углеводы: {kbzu['carbs']}г

Что дальше?
"""

    # Создаем клавиатуру с 2 кнопками
    builder = InlineKeyboardBuilder()

    # Кнопка 1: Написать тренеру (обычная ссылка)
    builder.button(
        text="👤 Написать тренеру",
        url="https://t.me/твой_username"  # Замени на свой
    )

    # Кнопка 2: Открыть КБЖУ трекер (Mini App) - ПОКА ЗАГЛУШКА
    # Позже заменишь на реальный URL Mini App
    builder.button(
        text="📱 Открыть КБЖУ трекер",
        web_app=WebAppInfo(url="https://your-miniapp-url.vercel.app")  # Пока заглушка
    )

    builder.adjust(1)  # По 1 кнопке в ряду

    await callback.message.edit_text(
        message_text,
        reply_markup=builder.as_markup()
    )
```

---

## 3. Установи httpx (если еще нет)

```bash
pip install httpx
```

Добавь в `requirements.txt`:
```
httpx>=0.27.0
```

---

## 4. Тестирование локально

### Шаг 1: Запусти Django локально

```bash
python manage.py runserver
```

Django запустится на `http://localhost:8000`

### Шаг 2: Запусти ngrok

```bash
ngrok http 8000
```

Получишь URL типа: `https://abc123.ngrok.io`

### Шаг 3: Обнови URL в боте

```python
DJANGO_API_URL = "https://abc123.ngrok.io/api/v1"
```

### Шаг 4: Перезапусти бота

Бот теперь будет отправлять данные в Django через ngrok!

---

## 5. Проверка что данные сохранились

### Вариант 1: Django Admin

```bash
python manage.py createsuperuser
```

Открой `http://localhost:8000/admin/`

Зайди в **Telegram пользователи** → Увидишь сохраненные данные

### Вариант 2: Через API

```bash
# Получить список всех Telegram пользователей (только для разработки)
curl http://localhost:8000/api/v1/telegram/profile/ \
  -H "Authorization: Bearer <твой_jwt_token>"
```

---

## Структура данных

### Что отправляет бот в Django:

```json
{
  "telegram_id": 123456789,
  "first_name": "Иван",
  "last_name": "Иванов",
  "username": "ivan123",
  "answers": {
    "age": 25,
    "gender": "M",
    "weight": 75,
    "height": 180,
    "activity_level": "moderately_active",
    "goal": "weight_loss"
  },
  "calculated_kbzu": {
    "calories": 2100,
    "protein": 130,
    "fat": 70,
    "carbs": 240
  }
}
```

### Что создается в Django:

1. **Django User**
   - username: `tg_123456789`
   - first_name: `Иван`
   - email: `tg123456789@telegram.user`

2. **Profile** (связан с User)
   - gender: `M`
   - weight: `75`
   - height: `180`
   - activity_level: `moderately_active`
   - goal_type: `weight_loss`
   - birth_date: рассчитывается из age

3. **TelegramUser** (связан с User)
   - telegram_id: `123456789`
   - username: `ivan123`
   - first_name: `Иван`
   - ai_test_completed: `True`
   - ai_test_answers: `{...}`
   - recommended_calories: `2100`
   - recommended_protein: `130.00`
   - recommended_fat: `70.00`
   - recommended_carbs: `240.00`

4. **DailyGoal** (связан с User)
   - calories: `2100`
   - protein: `130`
   - fat: `70`
   - carbohydrates: `240`
   - source: `AUTO`
   - is_active: `True`

---

## Troubleshooting

### Ошибка: Connection refused

**Проблема:** Бот не может подключиться к Django

**Решение:**
- Проверь что Django запущен: `python manage.py runserver`
- Проверь что ngrok запущен: `ngrok http 8000`
- Используй ngrok URL в боте, не `localhost`

### Ошибка: 400 Bad Request

**Проблема:** Неверный формат данных

**Решение:**
- Проверь что отправляешь все обязательные поля
- Проверь формат JSON (особенно `calculated_kbzu`)

### Ошибка: 500 Internal Server Error

**Проблема:** Ошибка на стороне Django

**Решение:**
- Посмотри логи Django (в терминале где запущен `runserver`)
- Проверь что миграции применены: `python manage.py migrate`

---

## Что дальше?

После того как бот будет отправлять данные в Django:

1. **Создадим Mini App** (React приложение)
2. **Задеплоим Mini App** на Vercel
3. **Обновим кнопку** в боте с реальным URL
4. **Протестируем** полный flow

Готов к следующему шагу? 🚀
