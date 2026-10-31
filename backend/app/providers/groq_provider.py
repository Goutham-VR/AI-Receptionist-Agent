import os
import json
import time

from dotenv import load_dotenv
from groq import Groq
from groq import (
    APIConnectionError,
    RateLimitError,
    InternalServerError,
)

from app.providers.base import BaseLLMProvider

load_dotenv()


class GroqProvider(BaseLLMProvider):

    def __init__(self):

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is missing."
            )

        self.client = Groq(
            api_key=api_key
        )

        self.model_name = os.getenv(
            "GROQ_MODEL",
            "llama-3.3-70b-versatile"
        )

    # --------------------------------------------------
    # CONVERT MESSAGES
    # --------------------------------------------------

    def _convert_messages(
        self,
        messages: list[dict],
        system_instruction: str,
    ) -> list[dict]:

        formatted_messages = [
            {
                "role": "system",
                "content": system_instruction,
            }
        ]

        for message in messages:

            role = message["role"]

            # ------------------------------------------
            # USER MESSAGE
            # ------------------------------------------

            if role == "user":

                formatted_messages.append({
                    "role": "user",
                    "content": message["content"],
                })

            # ------------------------------------------
            # ASSISTANT MESSAGE
            # ------------------------------------------

            elif role == "assistant":

                tool_calls = message.get(
                    "tool_calls",
                    [],
                )

                if tool_calls:

                    formatted_tool_calls = []

                    for call in tool_calls:

                        formatted_tool_calls.append({
                            "id": call["id"],
                            "type": "function",
                            "function": {
                                "name": call["name"],
                                "arguments": json.dumps(
                                    call["arguments"]
                                ),
                            },
                        })

                    formatted_messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": formatted_tool_calls,
                    })

                else:

                    formatted_messages.append({
                        "role": "assistant",
                        "content": message.get("content") or "",
                    })

            # ------------------------------------------
            # TOOL RESULT
            # ------------------------------------------

            elif role == "tool":

                formatted_messages.append({
                    "role": "tool",
                    "tool_call_id": message["tool_call_id"],
                    "name": message["name"],
                    "content": message["content"],
                })

        return formatted_messages

    # --------------------------------------------------
    # GENERATE RESPONSE
    # --------------------------------------------------

    def generate_response(
        self,
        messages: list[dict],
        tools: list[dict],
        system_instruction: str,
    ) -> dict:

        formatted_messages = self._convert_messages(
            messages=messages,
            system_instruction=system_instruction,
        )

        for attempt in range(3):

            try:

                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=formatted_messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.2,
                )
                print("Provider:###############################################################################################################",self.model_name)


                if not response.choices:
                    raise RuntimeError(
                        "Groq returned no response choices."
                    )

                message = response.choices[0].message

                # --------------------------------------
                # TOOL CALL RESPONSE
                # --------------------------------------

                if message.tool_calls:

                    normalized_calls = []

                    for tool_call in message.tool_calls:

                        try:

                            arguments = json.loads(
                                tool_call.function.arguments
                            )

                        except json.JSONDecodeError as error:

                            raise RuntimeError(
                                "Groq returned invalid tool arguments."
                            ) from error

                        normalized_calls.append({
                            "id": tool_call.id,
                            "name": tool_call.function.name,
                            "arguments": arguments,
                        })

                    return {
                        "type": "tool_calls",
                        "tool_calls": normalized_calls,
                    }

                # --------------------------------------
                # NORMAL TEXT RESPONSE
                # --------------------------------------

                return {
                    "type": "text",
                    "text": message.content or (
                        "I couldn't generate a response."
                    ),
                }

            # ------------------------------------------
            # RETRY TEMPORARY ERRORS
            # ------------------------------------------

            except (
                APIConnectionError,
                RateLimitError,
                InternalServerError,
            ):

                if attempt == 2:
                    raise

                delay = 2 ** (attempt + 1)

                print(
                    f"Temporary Groq error. "
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)