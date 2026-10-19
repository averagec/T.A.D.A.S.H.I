"""
Weather tool — current conditions via OpenWeatherMap API.
"""

import json
import httpx

from config import cfg
from tools.registry import BaseTool, register_tool


@register_tool
class WeatherTool(BaseTool):
    name = "get_weather"
    description = (
        "Get current weather conditions for a city or location. "
        "Returns temperature, humidity, wind, and conditions. "
        "Use when the user asks about weather anywhere."
    )
    parameters = {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name (e.g. 'Singapore', 'London, UK', 'New York, US')",
            },
            "units": {
                "type": "string",
                "enum": ["metric", "imperial"],
                "description": "Temperature units. Default: metric (Celsius).",
            },
        },
        "required": ["location"],
    }

    async def execute(self, location: str, units: str = "metric", **kwargs) -> str:
        if not cfg.openweather_key:
            return (
                "Weather API key not configured. "
                "Set OPENWEATHER_API_KEY in your .env file. "
                "Get a free key at https://openweathermap.org/api"
            )

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": cfg.openweather_key,
            "units": units,
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Location '{location}' not found. Try a different city name."
            return f"Weather API error: {e.response.status_code}"
        except httpx.RequestError as e:
            return f"Network error fetching weather: {e}"

        unit_symbol = "°C" if units == "metric" else "°F"
        speed_unit = "m/s" if units == "metric" else "mph"

        weather = data.get("weather", [{}])[0]
        main = data.get("main", {})
        wind = data.get("wind", {})

        return (
            f"Weather in {data.get('name', location)}:\n"
            f"  Conditions: {weather.get('description', 'N/A').title()}\n"
            f"  Temperature: {main.get('temp', 'N/A')}{unit_symbol} "
            f"(feels like {main.get('feels_like', 'N/A')}{unit_symbol})\n"
            f"  Humidity: {main.get('humidity', 'N/A')}%\n"
            f"  Wind: {wind.get('speed', 'N/A')} {speed_unit}\n"
            f"  Pressure: {main.get('pressure', 'N/A')} hPa"
        )
