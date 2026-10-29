# 🤖 AI Receptionist Agent

An AI-powered receptionist that helps users with appointment scheduling through an LLM-powered agent, database tools, and a human-controlled booking approval workflow.

The project combines AI agent development, backend engineering, database management, authentication, and automated testing to demonstrate how an AI assistant can interact with real application services.

## 🚀 Project Overview

The AI Receptionist Agent is designed to assist users with appointment-related tasks while keeping important actions controlled and verifiable.

Instead of relying only on text generation, the agent can use application tools to retrieve appointment availability and initiate booking requests. Booking approvals are handled through a separate administrative workflow.

## ✨ Key Features

* **LLM-powered AI agent** — Uses Google's Gemini API to generate responses and support agent workflows.
* **Tool execution** — Allows the agent to interact with application functions rather than relying exclusively on generated text.
* **Appointment availability** — Checks available appointment slots through backend tools.
* **Booking requests** — Validates booking details and handles duplicate or invalid requests.
* **Human approval workflow** — Allows administrators to approve or reject pending booking requests.
* **JWT authentication** — Protects administrative operations using token-based authentication.
* **Password security** — Includes password hashing and credential validation.
* **PostgreSQL integration** — Stores appointment slots, booking records, and approval requests.
* **Concurrency protection** — Tests competing approval requests for the same appointment slot.
* **Automated testing** — Includes unit tests, API tests, integration tests, and PostgreSQL tests.
* **Controlled agent execution** — Includes execution-step limits and error handling.

## 🛠️ Technology Stack

| Component                   | Technology                 |
| --------------------------- | -------------------------- |
| Backend                     | Python, FastAPI            |
| AI / LLM                    | Google Gemini API          |
| Database                    | PostgreSQL                 |
| Database hosting            | Supabase                   |
| ORM                         | SQLAlchemy                 |
| Authentication              | JWT                        |
| API testing                 | Pytest, FastAPI TestClient |
| Version control             | Git, GitHub                |
| Planned frontend            | React, Vite                |
| Planned backend deployment  | Render                     |
| Planned frontend deployment | Vercel                     |

## 🏗️ Architecture

```text
                    User
                     |
                     v
              AI Receptionist
                     |
                     v
                 Gemini API
                     |
                     v
              Agent Tool Layer
                     |
          +----------+----------+
          |                     |
          v                     v
    Check Available       Submit Booking
        Slots                 Request
          |                     |
          +----------+----------+
                     |
                     v
              FastAPI Backend
                     |
                     v
             PostgreSQL Database
                     |
                     v
             Pending Approval
                     |
                     v
              Admin Workflow
                /       \
               v         v
            Approve    Reject
               |
               v
          Confirm Booking
```

The diagram illustrates the intended application workflow. Exact request routing and implementation details are defined by the backend code.

## 📅 Booking Approval Workflow

1. A user requests an appointment.
2. The backend validates the booking details.
3. The system checks appointment availability.
4. A valid request is stored for administrative review.
5. An administrator reviews the pending request.
6. If approved, the booking is created and the appointment slot is marked as booked.
7. If rejected, the request is marked as rejected without creating a booking.

The workflow includes checks for unavailable slots, previously reviewed requests, and duplicate bookings.

## 🔐 Security

The backend includes several security-related mechanisms:

* JWT-based authentication.
* Password hashing.
* Validation of administrative access.
* Handling of invalid and expired tokens.
* Database constraints to prevent conflicting bookings.
* Controlled execution of agent tools.

**Security note:** API keys and database credentials must be stored in environment variables and must never be committed to the repository.

## 🧪 Automated Testing

The project currently has **57 automated tests passing**.

The test suite covers:

* AI agent behavior and tool execution.
* Booking validation and error handling.
* Approval and rejection workflows.
* API authentication.
* JWT validation and expiration.
* Login and password security.
* PostgreSQL integration.
* Concurrent booking approval attempts.

Latest recorded test result:

```text
57 passed, 1 warning in 21.80s
```

The warning concerns a Starlette TestClient deprecation notice. It did not prevent the tests from passing.

Run the test suite locally:

```bash
python -m pytest -vv
```

## ⚙️ Local Setup

### Prerequisites

* Python 3.10 or a compatible Python version.
* Git.
* A PostgreSQL database or Supabase PostgreSQL instance.
* A Google Gemini API key.

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/AI-Receptionist-Agent.git
cd AI-Receptionist-Agent
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Create a virtual environment

On Windows:

```bash
python -m venv mainenv
mainenv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the backend's current project directory.

Configure the variables required by the application:

```env
DATABASE_URL=your_postgresql_connection_string
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET_KEY=your_secure_random_secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Use the actual variable names and expected formats defined by your application configuration. The values above are placeholders, not working credentials.

Never upload `.env` to GitHub.

### 5. Run the backend

Start the FastAPI application using the entry point and application object defined in your project.

For example, if your entry point is `main.py` and the FastAPI instance is named `app`:

```bash
uvicorn main:app --reload
```

### 6. Run the tests

```bash
python -m pytest -vv
```

Note: The PostgreSQL integration tests require a correctly configured database connection.

## 🌐 Deployment Roadmap

The planned deployment architecture is:

* **Backend API:** Render
* **Frontend:** Vercel
* **Database:** Supabase PostgreSQL
* **LLM:** Google Gemini API

The frontend will be developed separately using React and Vite and will communicate with the backend through HTTP APIs.

Deployment configuration, CORS, environment variables, and live API verification will be completed as part of the deployment process.

## 🎯 Engineering Goals

This project demonstrates practical work in:

* LLM-powered application development.
* AI agent tool integration.
* Backend API development.
* Database transaction handling.
* Human-in-the-loop workflows.
* Authentication and authorization.
* Automated software testing.
* Cloud deployment preparation.

## 👨‍💻 Author

**Goutham VR**

AI/ML Engineer & Developer

GitHub: [Goutham-VR](https://github.com/Goutham-VR)

---

*This project is under active development. The React frontend and online deployment are planned next.*
