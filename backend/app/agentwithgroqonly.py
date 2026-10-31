import json
import os

from dotenv import load_dotenv

from app.models import AgentRun, AgentTrace
from app.database import SessionLocal

from app.tools.calendar_tools import check_slots
from app.tools.booking_tools import request_booking_approval

from app.providers.factory import get_llm_provider
from app.providers.tool_definitions import RECEPTIONIST_TOOLS


load_dotenv()

MAX_STEPS = 8

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


# --------------------------------------------------
# PROVIDER
# --------------------------------------------------

provider = get_llm_provider()


# --------------------------------------------------
# TOOL 1: CHECK APPOINTMENT AVAILABILITY
# --------------------------------------------------

def check_slots_tool(
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict:

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


# --------------------------------------------------
# TOOL 2: REQUEST BOOKING APPROVAL
# --------------------------------------------------

def request_booking_approval_tool(
    slot_id: int,
    customer_name: str,
    customer_email: str,
) -> dict:

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
# EXECUTE TOOLS
# --------------------------------------------------

def execute_tool(
    tool_name: str,
    arguments: dict,
) -> dict:

    if tool_name == "check_slots":

        return check_slots_tool(
            start_time=arguments.get("start_time"),
            end_time=arguments.get("end_time"),
        )

    elif tool_name == "request_booking_approval":

        return request_booking_approval_tool(
            slot_id=int(arguments["slot_id"]),
            customer_name=arguments["customer_name"],
            customer_email=arguments["customer_email"],
        )

    return {
        "success": False,
        "error": f"Unknown tool requested: {tool_name}",
    }


# --------------------------------------------------
# DATABASE TRACE
# --------------------------------------------------

def record_trace(
    db,
    run_id: int,
    step_number: int,
    action: str,
    details: dict,
):

    trace = AgentTrace(
        run_id=run_id,
        step_number=step_number,
        action=action,
        details=details,
    )

    db.add(trace)
    db.commit()


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

    messages = []

    try:

        # ------------------------------------------
        # PREVIOUS CONVERSATION HISTORY
        # ------------------------------------------

        for message in (conversation_history or [])[-20:]:

            role = message.get("role")
            content = message.get("content")

            if role not in ("user", "assistant"):
                continue

            if not isinstance(content, str) or not content.strip():
                continue

            messages.append({
                "role": role,
                "content": content,
            })

        # ------------------------------------------
        # CURRENT USER MESSAGE
        # ------------------------------------------

        messages.append({
            "role": "user",
            "content": user_message,
        })

        record_trace(
            db,
            run_id,
            0,
            "run_started",
            {
                "message": user_message,
                "provider": os.getenv("LLM_PROVIDER", "gemini"),
            },
        )

        # ------------------------------------------
        # MAIN AGENT EXECUTION LOOP
        # ------------------------------------------

        for step in range(MAX_STEPS):

            step_count = step + 1

            record_trace(
                db,
                run_id,
                step_count,
                "model_request",
                {
                    "provider": os.getenv("LLM_PROVIDER", "gemini"),
                },
            )

            response = provider.generate_response(
                messages=messages,
                tools=RECEPTIONIST_TOOLS,
                system_instruction=SYSTEM_INSTRUCTION,
            )

            # --------------------------------------
            # NORMAL TEXT RESPONSE
            # --------------------------------------

            if response["type"] == "text":

                final_response = (
                    response.get("text")
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
                    {
                        "status": "success",
                    },
                )

                db.commit()

                return final_response

            # --------------------------------------
            # TOOL CALLS
            # --------------------------------------

            if response["type"] == "tool_calls":

                tool_calls = response.get("tool_calls", [])

                # Build normalized assistant message
                assistant_message = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call["id"],
                            "name": call["name"],
                            "arguments": call["arguments"],
                        }
                        for call in tool_calls
                    ],
                }

                # IMPORTANT:
                # Preserve original provider metadata.
                # Gemini needs its original model_content
                # to retain the function-call thought_signature.

                provider_metadata = response.get(
                    "provider_metadata"
                )

                if provider_metadata:
                    assistant_message["provider_metadata"] = (
                        provider_metadata
                    )

                messages.append(assistant_message)

                # ----------------------------------
                # EXECUTE EACH TOOL
                # ----------------------------------

                for tool_call in tool_calls:

                    tool_name = tool_call["name"]
                    arguments = tool_call["arguments"]

                    record_trace(
                        db,
                        run_id,
                        step_count,
                        "tool_call",
                        {
                            "tool": tool_name,
                            "arguments": arguments,
                        },
                    )

                    try:

                        tool_result = execute_tool(
                            tool_name=tool_name,
                            arguments=arguments,
                        )

                    except Exception as error:

                        print(
                            f"Tool execution failed "
                            f"({tool_name}): {error}"
                        )

                        tool_result = {
                            "success": False,
                            "error": (
                                f"Tool execution failed: {tool_name}"
                            ),
                        }

                    record_trace(
                        db,
                        run_id,
                        step_count,
                        "tool_result",
                        {
                            "tool": tool_name,
                            "success": tool_result.get(
                                "success",
                                False,
                            ),
                            "result_count": tool_result.get(
                                "count",
                                0,
                            ),
                        },
                    )

                    # ----------------------------------
                    # ADD TOOL RESULT TO CONVERSATION
                    # ----------------------------------

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
                        "content": json.dumps(
                            tool_result,
                            default=str,
                        ),
                    })

        # ------------------------------------------
        # MAXIMUM STEPS REACHED
        # ------------------------------------------

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
            {
                "error_type": type(error).__name__,
            },
        )

        raise

    finally:
        db.close()