RECEPTIONIST_TOOLS = [
    {
        "type": "function",
        "function": {
        "name": "check_slots",
        "description": (
        "Find available appointment slots in the database. "
        "Use this when the user asks about available appointments. "
        "Optional times must be ISO 8601 datetime strings. "
        "Use null when the user does not specify a time range. "
        "Do not invent appointment availability."
        ),
        "parameters": {
        "type": "object",
        "properties": {
        "start_time": {
        "type": ["string", "null"],
        "description": (
        "Optional inclusive start datetime "
        "in ISO 8601 format. Use null if unspecified."
        ),
        },
        "end_time": {
        "type": ["string", "null"],
        "description": (
        "Optional exclusive end datetime "
        "in ISO 8601 format. Use null if unspecified."
        ),
        },
        },
        "required": [],
        },
        },
        },
        {
        "type": "function",
        "function": {
        "name": "request_booking_approval",
        "description": (
        "Submit an appointment booking request for human approval. "
        "Use this only after checking availability and collecting "
        "the customer's name and email address. "
        "This tool does not confirm the booking."
        ),
        "parameters": {
        "type": "object",
        "properties": {
        "slot_id": {
        "type": "integer",
        "description": (
        "ID of the selected available appointment slot."
        ),
        },
        "customer_name": {
        "type": "string",
        "description": "Full name of the customer.",
        },
        "customer_email": {
        "type": "string",
        "description": "Email address of the customer.",
        },
        },
        "required": [
        "slot_id",
        "customer_name",
        "customer_email",
        ],
        },
    },
},
]
