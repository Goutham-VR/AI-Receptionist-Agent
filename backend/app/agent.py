import time
from google.genai.errors import ServerError
import os
import json

from app.models import AgentRun, AgentTrace
from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.database import SessionLocal

from app.tools.calendar_tools import check_slots
from app.tools.booking_tools import request_booking_approval

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing.")

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.6-flash"
MAX_STEPS = 8


# --------------------------------------------------
# TOOL 1: Check appointment availability
# --------------------------------------------------

def check_slots_tool(
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict:
    """
    Execute the existing database tool.
    """

    from datetime import datetime

    parsed_start = None
    parsed_end = None

    if start_time:
        parsed_start = datetime.fromisoformat(
            start_time.replace("Z", "+00:00")
        )

    if end_time:
        parsed_end = datetime.fromisoformat(
            end_time.replace("Z", "+00:00")
        )

    db = SessionLocal()

    try:
        return check_slots(
            db=db,
            start_time=parsed_start,
            end_time=parsed_end,
        )
    finally:
        db.close()

def request_booking_approval_tool(slot_id: int,customer_name: str,customer_email: str,) -> dict:
    db = SessionLocal()
    try:
        return request_booking_approval(
            db=db,
            slot_id=slot_id,
            customer_name=customer_name,
            customer_email=customer_email,
        )
    finally:
        db.close()

# --------------------------------------------------
# TOOL DEFINITIONS
# --------------------------------------------------

check_slots_declaration = types.FunctionDeclaration(
    name="check_slots",
    description=(
        "Find available appointment slots in the database. "
        "Use this when the user asks about available appointments. "
        "Optional times must be ISO 8601 datetime strings. "
        "Do not invent appointment availability."
    ),
    parameters={
        "type": "OBJECT",
        "properties": {
            "start_time": {
                "type": "STRING",
                "description": (
                    "Optional inclusive start datetime in ISO 8601 format."
                ),
            },
            "end_time": {
                "type": "STRING",
                "description": (
                    "Optional exclusive end datetime in ISO 8601 format."
                ),
            },
        },
        "required": [],
    },
)

request_booking_approval_declaration = types.FunctionDeclaration(
    name="request_booking_approval",
    description=(
        "Submit an appointment booking request for human approval. "
        "Use this only after checking availability and collecting "
        "the customer's name and email address. "
        "This tool does not confirm the booking."
    ),
    parameters={
        "type": "OBJECT",
        "properties": {
            "slot_id": {
                "type": "INTEGER",
                "description": "ID of the selected available appointment slot.",
            },
            "customer_name": {
                "type": "STRING",
                "description": "Full name of the customer.",
            },
            "customer_email": {
                "type": "STRING",
                "description": "Email address of the customer.",
            },
        },
        "required": [
            "slot_id",
            "customer_name",
            "customer_email",
        ],
    },
)

receptionist_tools = [
    types.Tool(
        function_declarations=[
            check_slots_declaration,
            request_booking_approval_declaration,
        ]
    )
]



def record_trace(
    db,
    run_id: int,
    step_number: int,
    action: str,
    details: dict,
):
    """
    Save one execution event to agent_traces.
    """

    trace = AgentTrace(
        run_id=run_id,
        step_number=step_number,
        action=action,
        details=details,
    )

    db.add(trace)
    db.commit()

def generate_with_retry(contents, max_retries=2):
    """
    Retry temporary Gemini server errors.

    max_retries=2 means:
    - 1 initial request
    - Up to 2 additional attempts
    """

    for attempt in range(max_retries + 1):
        try:
            return client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=(
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
                    ),
                    tools=receptionist_tools,
                    temperature=0.2,
                ),
            )

        except ServerError as error:
            if attempt == max_retries:
                raise

            delay = 2 ** (attempt + 1)

            print(
                f"Temporary Gemini server error. "
                f"Retrying in {delay} seconds..."
            )

            time.sleep(delay)

# --------------------------------------------------
# AGENT LOOP
# --------------------------------------------------
def receptionist_agent(
    user_message: str,
    conversation_history: list[dict] | None = None,
) -> str:

    db = SessionLocal()

    run = AgentRun(
        user_message=user_message,
        status="running",
        steps=0,
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    run_id = run.id
    step_count = 0

    contents = []

    for message in (conversation_history or [])[-20:]:
        role = message.get("role")
        message_text = message.get("content")

        if role not in ("user", "assistant"):
            continue

        if not isinstance(message_text, str) or not message_text.strip():
            continue

        contents.append(
            types.Content(
                role="user" if role == "user" else "model",
                parts=[types.Part(text=message_text)],
            )
        )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part(text=user_message)],
        )
    )

    try:
        record_trace(
            db,
            run_id,
            0,
            "run_started",
            {"message": user_message},
        )

        for step in range(MAX_STEPS):
            step_count = step + 1

            record_trace(
                db,
                run_id,
                step_count,
                "model_request",
                {"model": MODEL_NAME},
            )

            response = generate_with_retry(contents)

            if not response.candidates:
                raise RuntimeError(
                    "Gemini returned no response candidates."
                )

            model_content = response.candidates[0].content

            if model_content is None:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            contents.append(model_content)

            function_calls = [
                part.function_call
                for part in model_content.parts
                if part.function_call is not None
            ]

            if not function_calls:
                final_response = (
                    response.text
                    or "I couldn't generate a response."
                )

                run.status = "success"
                run.final_response = final_response
                run.steps = step_count

                record_trace(
                    db,
                    run_id,
                    step_count,
                    "run_completed",
                    {"status": "success"},
                )

                db.commit()

                return final_response

            tool_results = []

            for function_call in function_calls:
                tool_name = function_call.name

                record_trace(
                    db,
                    run_id,
                    step_count,
                    "tool_call",
                    {
                        "tool": tool_name,
                        "arguments": dict(
                            function_call.args or {}
                        ),
                    },
                )
                arguments = dict(function_call.args or {})

                try:
                    if tool_name == "check_slots":
                        tool_result = check_slots_tool(
                            start_time=arguments.get("start_time"),
                            end_time=arguments.get("end_time"),
                        )

                    elif tool_name == "request_booking_approval":
                        tool_result = request_booking_approval_tool(
                            slot_id=int(arguments["slot_id"]),
                            customer_name=arguments["customer_name"],
                            customer_email=arguments["customer_email"],
                        )

                    else:
                        tool_result = {
                            "success": False,
                            "error": f"Unknown tool requested: {tool_name}",
                        }

                except Exception as error:
                    print(f"Tool execution failed ({tool_name}): {error}")

                    tool_result = {
                        "success": False,
                        "error": f"Tool execution failed: {tool_name}",
                    }

                record_trace(
                    db,
                    run_id,
                    step_count,
                    "tool_result",
                    {
                        "tool": tool_name,
                        "success": tool_result.get(
                            "success", False
                        ),
                        "result_count": tool_result.get(
                            "count", 0
                        ),
                    },
                )

                tool_results.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response=tool_result,
                    )
                )

            contents.append(
                types.Content(
                    role="user",
                    parts=tool_results,
                )
            )

        raise RuntimeError(
            "Maximum agent steps reached."
        )

    except Exception as error:
        db.rollback()

        run.status = "failed"
        run.error_message = (
            f"{type(error).__name__}: {error}"
        )
        run.steps = step_count

        db.commit()

        record_trace(
            db,
            run_id,
            step_count,
            "run_failed",
            {"error_type": type(error).__name__},
        )

        raise

    finally:
        db.close()