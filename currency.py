import sys
import asyncio
from datetime import datetime, timedelta
import aiohttp 


class CurrencyAPI:
    """Клас для взаємодії з API ПриватБанку."""

    BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date={}"

    async def fetch_exchange_rate(self, session, date: str):
        """Отримує дані про курс валют для конкретної дати."""
        url = self.BASE_URL.format(date)
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Помилка: API повернуло статус {response.status} для дати {date}")
        except aiohttp.ClientError as e:
            print(f"Помилка мережі для дати {date}: {e}")
        return None


class CurrencyService:
    """Клас для обробки даних про курс валют."""

    def __init__(self, api_client: CurrencyAPI):
        self.api_client = api_client

    async def get_exchange_rates(self, days: int):
        """Отримує курси валют за останні `days` днів."""
        today = datetime.now()
        results = []

        async with aiohttp.ClientSession() as session:
            for i in range(days):
                date = (today - timedelta(days=i)).strftime("%d.%m.%Y")
                data = await self.api_client.fetch_exchange_rate(session, date)
                if data:
                    rates = self._extract_currency_rates(data, date)
                    if rates:
                        results.append(rates)

        return results

    def _extract_currency_rates(self, data: dict, date: str):
        """Обробляє відповідь API для отримання курсів EUR та USD."""
        try:
            exchange_rates = data.get("exchangeRate", [])
            rates = {
                "EUR": next(rate for rate in exchange_rates if rate["currency"] == "EUR"),
                "USD": next(rate for rate in exchange_rates if rate["currency"] == "USD"),
            }
            return {
                date: {
                    "EUR": {"sale": rates["EUR"]["saleRate"], "purchase": rates["EUR"]["purchaseRate"]},
                    "USD": {"sale": rates["USD"]["saleRate"], "purchase": rates["USD"]["purchaseRate"]},
                }
            }
        except (KeyError, StopIteration) as e:
            print(f"Помилка обробки даних для дати {date}: {e}")
        return None


class CurrencyApp:
    """Клас для роботи з утилітою."""

    def __init__(self, currency_service: CurrencyService):
        self.currency_service = currency_service

    async def run(self, days: int):
        """Основний метод для запуску утиліти."""
        if not (1 <= days <= 10):
            print("Кількість днів повинна бути в межах від 1 до 10.")
            return

        print(f"Отримання курсу валют за останні {days} днів...")
        rates = await self.currency_service.get_exchange_rates(days)
        if rates:
            print(rates)
        else:
            print("Не вдалося отримати дані про курси валют.")


def main():
    """Основна функція для запуску програми."""
    if len(sys.argv) != 2:
        print("Usage: python main.py <кількість днів>")
        return

    try:
        days = int(sys.argv[1])
    except ValueError:
        print("Кількість днів повинна бути цілим числом.")
        return

    api_client = CurrencyAPI()
    currency_service = CurrencyService(api_client)
    app = CurrencyApp(currency_service)

    asyncio.run(app.run(days))


if __name__ == "__main__":
    main()
