import os
import sys
import unittest
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from openai import OpenAI

class TestLiveToolCalling(unittest.TestCase):
    def setUp(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.api_key
        )
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_time_and_date",
                    "description": "Get the exact current real-time clock, time, day, and date in India (IST)",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "show_famous_place",
                    "description": "Show a high-resolution photograph of a famous place/monument in the in-call bottom sheet",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "place_name": {"type": "string", "description": "Name of the place or monument"}
                        },
                        "required": ["place_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_live_weather",
                    "description": "Get the live current weather for any Indian city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "City name"}
                        }
                    }
                }
            }
        ]

    def test_time_tool_call(self):
        res = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful voice assistant. Use tools when appropriate."},
                {"role": "user", "content": "Abhi kitne baje hain?"}
            ],
            tools=self.tools,
            tool_choice="auto",
            max_tokens=150
        )
        msg = res.choices[0].message
        self.assertTrue(msg.tool_calls is not None and len(msg.tool_calls) > 0)
        self.assertEqual(msg.tool_calls[0].function.name, "get_current_time_and_date")

    def test_photo_tool_call(self):
        res = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful voice assistant. Use tools when appropriate."},
                {"role": "user", "content": "Taj Mahal ki photo dikhao"}
            ],
            tools=self.tools,
            tool_choice="auto",
            max_tokens=150
        )
        msg = res.choices[0].message
        self.assertTrue(msg.tool_calls is not None and len(msg.tool_calls) > 0)
        self.assertEqual(msg.tool_calls[0].function.name, "show_famous_place")

    def test_weather_tool_call(self):
        res = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful voice assistant. Use tools when appropriate."},
                {"role": "user", "content": "Delhi ka mausam kaisa hai?"}
            ],
            tools=self.tools,
            tool_choice="auto",
            max_tokens=150
        )
        msg = res.choices[0].message
        self.assertTrue(msg.tool_calls is not None and len(msg.tool_calls) > 0)
        self.assertEqual(msg.tool_calls[0].function.name, "get_live_weather")

if __name__ == "__main__":
    unittest.main()
