from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app import agent


@pytest.fixture
def mock_db():
    db = MagicMock()

    def refresh_object(obj):
        if hasattr(obj, "id") and obj.id is None:
            obj.id = 1

    db.refresh.side_effect = refresh_object

    with patch("app.agent.SessionLocal", return_value=db):
        yield db


def make_response(text=None, function_call=None):
    if function_call is not None:
        parts = [
            SimpleNamespace(function_call=function_call)
        ]
    else:
        parts = [
            SimpleNamespace(function_call=None)
        ]

    content = SimpleNamespace(parts=parts)
    candidate = SimpleNamespace(content=content)

    return SimpleNamespace(
        candidates=[candidate],
        text=text,
    )


def test_agent_returns_normal_response(mock_db):
    response = make_response(
        text="Hello! I am your AI receptionist."
    )

    with patch(
        "app.agent.generate_with_retry",
        return_value=response,
    ):
        result = agent.receptionist_agent("Hello")

    assert result == "Hello! I am your AI receptionist."

    mock_db.add.assert_called()
    mock_db.commit.assert_called()
    mock_db.close.assert_called_once()


def test_agent_executes_check_slots_tool(mock_db):
    tool_call = SimpleNamespace(
        name="check_slots",
        args={},
    )

    tool_response = make_response(
        function_call=tool_call
    )

    final_response = make_response(
        text="There are two available appointment slots."
    )

    with patch(
        "app.agent.generate_with_retry",
        side_effect=[
            tool_response,
            final_response,
        ],
    ) as mock_generate, patch(
        "app.agent.check_slots_tool",
        return_value={
            "success": True,
            "count": 2,
            "slots": [
                {"id": 1},
                {"id": 2},
            ],
        },
    ) as mock_check_slots:

        result = agent.receptionist_agent(
            "Show me available appointment slots."
        )

    assert result == (
        "There are two available appointment slots."
    )

    mock_check_slots.assert_called_once_with(
        start_time=None,
        end_time=None,
    )

    assert mock_generate.call_count == 2

    mock_db.close.assert_called_once()


def test_agent_handles_tool_execution_error(mock_db):
    tool_call = SimpleNamespace(
        name="check_slots",
        args={},
    )

    tool_response = make_response(
        function_call=tool_call
    )

    final_response = make_response(
        text="Sorry, I could not retrieve the appointments."
    )

    with patch(
        "app.agent.generate_with_retry",
        side_effect=[
            tool_response,
            final_response,
        ],
    ), patch(
        "app.agent.check_slots_tool",
        side_effect=RuntimeError("Database unavailable"),
    ) as mock_check_slots:

        result = agent.receptionist_agent(
            "Check available appointment slots."
        )

    assert result == (
        "Sorry, I could not retrieve the appointments."
    )

    mock_check_slots.assert_called_once()

    mock_db.close.assert_called_once()


def test_agent_stops_at_maximum_steps(mock_db):
    tool_call = SimpleNamespace(
        name="check_slots",
        args={},
    )

    tool_response = make_response(
        function_call=tool_call
    )

    with patch(
        "app.agent.generate_with_retry",
        return_value=tool_response,
    ), patch(
        "app.agent.check_slots_tool",
        return_value={
            "success": True,
            "count": 0,
            "slots": [],
        },
    ), patch(
        "app.agent.MAX_STEPS",
        2,
    ):

        with pytest.raises(
            RuntimeError,
            match="Maximum agent steps reached.",
        ):
            agent.receptionist_agent(
                "Check available appointments."
            )

    mock_db.close.assert_called_once()

def test_agent_executes_booking_approval_tool(mock_db):
    tool_call = SimpleNamespace(
        name="request_booking_approval",
        args={
            "slot_id": 1,
            "customer_name": "John Smith",
            "customer_email": "john@example.com",
        },
    )

    tool_response = make_response(
        function_call=tool_call
    )

    final_response = make_response(
        text=(
            "Your booking request has been submitted "
            "and is awaiting human approval."
        )
    )

    with patch(
        "app.agent.generate_with_retry",
        side_effect=[
            tool_response,
            final_response,
        ],
    ), patch(
        "app.agent.request_booking_approval_tool",
        return_value={
            "success": True,
            "message": "Booking request submitted for human approval.",
            "approval_id": 101,
            "slot_id": 1,
            "status": "pending",
        },
    ) as mock_booking_tool:

        result = agent.receptionist_agent(
            "Book an appointment for John Smith, "
            "john@example.com, slot 1."
        )

    assert result == (
        "Your booking request has been submitted "
        "and is awaiting human approval."
    )

    mock_booking_tool.assert_called_once_with(
        slot_id=1,
        customer_name="John Smith",
        customer_email="john@example.com",
    )

    mock_db.close.assert_called_once()


def test_agent_handles_booking_failure(mock_db):
    tool_call = SimpleNamespace(
        name="request_booking_approval",
        args={
            "slot_id": 1,
            "customer_name": "John Smith",
            "customer_email": "john@example.com",
        },
    )

    tool_response = make_response(
        function_call=tool_call
    )

    final_response = make_response(
        text=(
            "Sorry, the appointment request could not "
            "be submitted because the slot is unavailable."
        )
    )

    with patch(
        "app.agent.generate_with_retry",
        side_effect=[
            tool_response,
            final_response,
        ],
    ), patch(
        "app.agent.request_booking_approval_tool",
        return_value={
            "success": False,
            "message": "This appointment slot is no longer available.",
        },
    ) as mock_booking_tool:

        result = agent.receptionist_agent(
            "Book slot 1 for John Smith, john@example.com."
        )

    assert "slot is unavailable" in result

    mock_booking_tool.assert_called_once()

    mock_db.close.assert_called_once()


def test_agent_passes_booking_arguments_correctly(mock_db):
    tool_call = SimpleNamespace(
        name="request_booking_approval",
        args={
            "slot_id": 25,
            "customer_name": "Alice Brown",
            "customer_email": "alice@example.com",
        },
    )

    tool_response = make_response(
        function_call=tool_call
    )

    final_response = make_response(
        text="Your request is awaiting approval."
    )

    with patch(
        "app.agent.generate_with_retry",
        side_effect=[
            tool_response,
            final_response,
        ],
    ), patch(
        "app.agent.request_booking_approval_tool",
        return_value={
            "success": True,
            "message": "Booking request submitted for human approval.",
            "approval_id": 102,
            "slot_id": 25,
            "status": "pending",
        },
    ) as mock_booking_tool:

        result = agent.receptionist_agent(
            "Request slot 25 for Alice Brown, alice@example.com."
        )

    assert result == "Your request is awaiting approval."

    mock_booking_tool.assert_called_once_with(
        slot_id=25,
        customer_name="Alice Brown",
        customer_email="alice@example.com",
    )


def test_agent_does_not_confirm_pending_booking(mock_db):
    tool_call = SimpleNamespace(
        name="request_booking_approval",
        args={
            "slot_id": 1,
            "customer_name": "John Smith",
            "customer_email": "john@example.com",
        },
    )

    tool_response = make_response(
        function_call=tool_call
    )

    final_response = make_response(
        text=(
            "Your appointment request has been submitted "
            "and is pending human approval. "
            "Your appointment is not yet confirmed."
        )
    )

    with patch(
        "app.agent.generate_with_retry",
        side_effect=[
            tool_response,
            final_response,
        ],
    ), patch(
        "app.agent.request_booking_approval_tool",
        return_value={
            "success": True,
            "message": "Booking request submitted for human approval.",
            "approval_id": 103,
            "slot_id": 1,
            "status": "pending",
        },
    ):

        result = agent.receptionist_agent(
            "Book an appointment for John Smith, "
            "john@example.com, slot 1."
        )

    assert "pending human approval" in result.lower()
    assert "not yet confirmed" in result.lower()