"""
OpenRouter API клиент для генерации персональных планов.
"""

import httpx
from typing import Dict, Any, Optional

from bot.config import settings
from bot.prompts.personal_plan import get_system_prompt, build_user_message, get_prompt_version
from bot.utils.logger import logger


class OpenRouterClient:
    """Клиент для работы с OpenRouter API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Инициализация клиента.

        Args:
            base_url: Base URL OpenRouter API
            api_key: API ключ
            model: Название модели
            timeout: Таймаут запроса в секундах
        """
        self.base_url = base_url or settings.OPENROUTER_BASE_URL
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model = model or settings.OPENROUTER_MODEL
        self.timeout = timeout or settings.OPENROUTER_TIMEOUT

    async def generate_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует персональный план через OpenRouter API.

        Args:
            payload: Данные опроса пользователя

        Returns:
            Словарь с результатом:
            {
                "success": bool,
                "text": str,  # Текст плана от ИИ
                "model": str,  # Использованная модель
                "prompt_version": str,  # Версия промпта
                "error": str | None  # Сообщение об ошибке
            }
        """
        system_prompt = get_system_prompt()
        user_message = build_user_message(payload)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url=f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/your-repo",  # Для аналитики OpenRouter
                        "X-Title": "AI Lead Magnet Bot"
                    },
                    json={
                        "model": self.model,
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

                # Извлечь текст ответа
                ai_text = data["choices"][0]["message"]["content"]

                logger.info(f"AI plan generated successfully. Model: {self.model}, Length: {len(ai_text)}")

                return {
                    "success": True,
                    "text": ai_text,
                    "model": self.model,
                    "prompt_version": get_prompt_version(),
                    "error": None
                }

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(f"OpenRouter API HTTP error: {error_msg}")
            return {
                "success": False,
                "text": "",
                "model": self.model,
                "prompt_version": get_prompt_version(),
                "error": error_msg
            }

        except httpx.TimeoutException as e:
            error_msg = f"Request timeout after {self.timeout}s"
            logger.error(f"OpenRouter API timeout: {error_msg}")
            return {
                "success": False,
                "text": "",
                "model": self.model,
                "prompt_version": get_prompt_version(),
                "error": error_msg
            }

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"OpenRouter API unexpected error: {error_msg}", exc_info=True)
            return {
                "success": False,
                "text": "",
                "model": self.model,
                "prompt_version": get_prompt_version(),
                "error": error_msg
            }


# Глобальный экземпляр клиента
openrouter_client = OpenRouterClient()
