import os
import time
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError

from app.providers.base import BaseLLMProvider

load_dotenv()

SYSTEM_INSTRUCTION = (
    "You are an AI receptionist agent. "
    "Help users check appointment availability and request bookings. "
    "Use check_slots to retrieve actual available appointments. "
    "Never invent appointment slots or availability. "
    "When a user wants to book an appointment, first check availability. "
    "If the user has not provided their name or email address, ask for "
    "the missing information before submitting a booking request. "
    "Use request_booking_approval only when you have a suitable available "
    "slot and the required customer information. "
    "Submitting a booking request does not confirm the appointment. "
    "Always tell the user that the request requires human approval. "
    "Never claim an appointment is confirmed unless the booking system "
    "explicitly confirms that it is. "
    "Do not claim to have sent emails because email functionality "
    "has not been implemented."
)


class GeminiProvider(BaseLLMProvider):

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is missing.")

        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.6-flash"
        )

    
    def _convert_tools(self, tools):
        declarations = []

        def convert_schema(schema):
            if not isinstance(schema, dict):
                return schema

            converted = dict(schema)

            property_type = converted.get("type", "string")

            if isinstance(property_type, list):
                property_type = next(
                    (
                        item for item in property_type
                        if item != "null"
                    ),
                    "string"
                )

            type_mapping = {
                "string": "STRING",
                "integer": "INTEGER",
                "number": "NUMBER",
                "boolean": "BOOLEAN",
                "object": "OBJECT",
                "array": "ARRAY",
            }

            converted["type"] = type_mapping.get(
                property_type.lower(),
                "STRING"
            )

            if "properties" in converted:
                converted["properties"] = {
                    name: convert_schema(property_schema)
                    for name, property_schema
                    in converted["properties"].items()
                }

            if "items" in converted:
                converted["items"] = convert_schema(
                    converted["items"]
                )

            return converted

        for tool in tools:
            function = tool["function"]

            declarations.append(
                types.FunctionDeclaration(
                    name=function["name"],
                    description=function["description"],
                    parameters=convert_schema(
                        function["parameters"]
                    ),
                )
            )

        return [
            types.Tool(function_declarations=declarations)
        ]



    def _convert_messages(self, messages):
        contents = []
        index = 0

        while index < len(messages):
            message = messages[index]
            role = message["role"]

            if role == "user":
                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part(text=message["content"])
                        ],
                    )
                )

            elif role == "assistant":
                tool_calls = message.get("tool_calls", [])

                if tool_calls:
                    original_content = (
                        message.get("provider_metadata", {})
                        .get("model_content")
                    )

                    if original_content is not None:
                        contents.append(original_content)

                    else:
                        raise RuntimeError(
                            "Original Gemini tool-call content is missing. "
                            "Thought signature cannot be preserved."
                        )

                else:
                    contents.append(
                        types.Content(
                            role="model",
                            parts=[
                                types.Part(
                                    text=message.get("content") or ""
                                )
                            ],
                        )
                    )

            elif role == "tool":
                tool_parts = []

                while (
                    index < len(messages)
                    and messages[index]["role"] == "tool"
                ):
                    tool_message = messages[index]

                    result = json.loads(
                        tool_message["content"]
                    )

                    tool_parts.append(
                        types.Part.from_function_response(
                            name=tool_message["name"],
                            response=result,
                        )
                    )

                    index += 1

                contents.append(
                    types.Content(
                        role="user",
                        parts=tool_parts,
                    )
                )

                continue

            index += 1

        return contents

    def generate_response(
        self,
        messages: list[dict],
        tools: list[dict],
        system_instruction: str = SYSTEM_INSTRUCTION,
    ) -> dict:

        contents = self._convert_messages(messages)
        gemini_tools = self._convert_tools(tools)

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        tools=gemini_tools,
                        temperature=0.2,
                    ),
                )

                if not response.candidates:
                    raise RuntimeError(
                        "Gemini returned no response candidates."
                    )

                model_content = response.candidates[0].content

                if model_content is None:
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                function_calls = [
                    part.function_call
                    for part in model_content.parts
                    if part.function_call is not None
                ]

                if function_calls:
                    normalized_calls = []

                    for index, function_call in enumerate(function_calls):
                        normalized_calls.append(
                            {
                                "id": f"gemini_{function_call.name}_{index}",
                                "name": function_call.name,
                                "arguments": dict(function_call.args or {}),
                            }
                        )

                    return {
                        "type": "tool_calls",
                        "tool_calls": normalized_calls,
                        "provider_metadata": {
                            "model_content": model_content,
                        },
                    }

                return {
                    "type": "text",
                    "text": response.text or (
                        "I couldn't generate a response."
                    ),
                }

            except ServerError:
                if attempt == 2:
                    raise

                delay = 2 ** (attempt + 1)

                print(
                    f"Temporary Gemini server error. "
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)