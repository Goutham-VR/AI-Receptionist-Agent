
import { useState } from "react";
import {
  Bot,
  Send,
  LockKeyhole,
  CalendarDays,
  Clock3,
  ShieldCheck,
  Sparkles,
  ArrowDown,
} from "lucide-react";
import { api } from "./api";
import "./App.css";

function CustomerChat({ onAdminLoginClick }) {
  const [message, setMessage] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      text: "Hello! I'm your AI receptionist. I can help you find available appointment slots and request a booking. How can I help?",
    },
  ]);

  const [conversationHistory, setConversationHistory] = useState([]);

  async function sendMessage(event) {
    event.preventDefault();

    const text = message.trim();
    if (!text || chatLoading) return;

    setChatMessages((previous) => [
      ...previous,
      { role: "user", text },
    ]);

    setMessage("");
    setChatLoading(true);

    try {
      const result = await api.chatWithAgent(
        text,
        conversationHistory
      );

      const reply =
        result.reply || "I couldn't generate a response.";

      setChatMessages((previous) => [
        ...previous,
        { role: "assistant", text: reply },
      ]);

      setConversationHistory((previous) =>
        [
          ...previous,
          { role: "user", content: text },
          { role: "assistant", content: reply },
        ].slice(-20)
      );
    } catch (error) {
      setChatMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text:
            error.message ||
            "Something went wrong. Please try again.",
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  function useSuggestion(text) {
    setMessage(text);
  }

  return (
    <main className="reception-page">
      <header className="reception-navbar">
        <a className="reception-brand" href="#" aria-label="ReceptionAI home">
          <span className="reception-brand-icon">
            <Bot size={23} />
          </span>
          <span>
            Reception<span className="brand-ai">AI</span>
          </span>
        </a>

        <div className="reception-nav-right">
          <span className="nav-status">
            <span className="status-dot" />
            AI Assistant
          </span>

          <button
            type="button"
            className="admin-login-button"
            onClick={onAdminLoginClick}
          >
            <LockKeyhole size={15} />
            Admin Login
          </button>
        </div>
      </header>

      <section className="reception-hero">
        <span className="hero-eyebrow">
          <Sparkles size={14} />
          YOUR PERSONAL AI RECEPTIONIST
        </span>

        <h1>
          Appointments, made <span>simple.</span>
        </h1>

        <p className="hero-description">
          Ask questions, explore available time slots, and request
          your appointment — all through a simple conversation.
        </p>
      </section>

      <section className="reception-features">
        <article className="feature-card">
          <span className="feature-icon">
            <CalendarDays size={19} />
          </span>
          <div>
            <h3>Find appointments</h3>
            <p>Explore available time slots.</p>
          </div>
        </article>

        <article className="feature-card">
          <span className="feature-icon">
            <Clock3 size={19} />
          </span>
          <div>
            <h3>Request a booking</h3>
            <p>Submit your preferred time.</p>
          </div>
        </article>

        <article className="feature-card">
          <span className="feature-icon">
            <ShieldCheck size={19} />
          </span>
          <div>
            <h3>Human approval</h3>
            <p>Bookings are reviewed by an admin.</p>
          </div>
        </article>
      </section>

      <section className="reception-chat-section">
        <div className="chat-section-heading">
          <div>
            <h2>Chat with our assistant</h2>
            <p>What can I help you with today?</p>
          </div>

          <span className="powered-label">
            <Sparkles size={14} />
            Gemini AI
          </span>
        </div>

        <div className="reception-chat-panel">
          <div className="reception-chat-header">
            <span className="chat-header-icon">
              <Bot size={22} />
            </span>

            <div className="chat-header-text">
              <h3>AI Receptionist</h3>
              <p>
                <span className="status-dot" />
                Ready to assist you
              </p>
            </div>
          </div>

          <div className="reception-chat-messages">
            {chatMessages.map((chatMessage, index) => (
              <div
                className={`reception-message-row ${chatMessage.role}`}
                key={`${chatMessage.role}-${index}`}
              >
                {chatMessage.role === "assistant" && (
                  <span className="message-avatar">
                    <Bot size={17} />
                  </span>
                )}

                <div className="reception-message-bubble">
                  {chatMessage.text}
                </div>
              </div>
            ))}

            {chatLoading && (
              <div className="reception-message-row assistant">
                <span className="message-avatar">
                  <Bot size={17} />
                </span>
                <div className="reception-message-bubble typing-message">
                  Thinking...
                </div>
              </div>
            )}
          </div>

          {chatMessages.length === 1 && (
            <div className="suggestion-area">
              <p>TRY ASKING</p>
              <div className="suggestion-list">
                <button
                  type="button"
                  onClick={() =>
                    useSuggestion("Show me the available appointment slots")
                  }
                >
                  Show available slots
                  <ArrowDown size={14} />
                </button>

                <button
                  type="button"
                  onClick={() =>
                    useSuggestion("How can I request an appointment?")
                  }
                >
                  How do I book an appointment?
                  <ArrowDown size={14} />
                </button>
              </div>
            </div>
          )}

          <form className="reception-chat-form" onSubmit={sendMessage}>
            <input
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder={
                chatLoading
                  ? "Assistant is responding..."
                  : "Type your message here..."
              }
              aria-label="Your message"
              disabled={chatLoading}
            />

            <button
              type="submit"
              aria-label="Send message"
              disabled={chatLoading || !message.trim()}
            >
              <Send size={18} />
              <span>Send</span>
            </button>
          </form>

          <p className="reception-chat-note">
            <ShieldCheck size={14} />
            Booking requests are not confirmed until approved by an administrator.
          </p>
        </div>
      </section>

      <footer className="reception-footer">
        <span>ReceptionAI</span>
        <span>Simple conversations. Smarter appointments.</span>
      </footer>
    </main>
  );
}

export default CustomerChat;
