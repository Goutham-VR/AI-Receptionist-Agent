import { useState } from "react";
import { Bot, LockKeyhole, Mail } from "lucide-react";
import "./Login.css";

export default function Login({ onLogin }) {
const [email, setEmail] = useState("");
const [password, setPassword] = useState("");
const [loading, setLoading] = useState(false);
const [error, setError] = useState("");

async function handleSubmit(event) {
event.preventDefault();
setError("");
setLoading(true);

try {
  await onLogin({ email: email.trim(), password });
} catch (err) {
  setError(err.message || "Login failed. Please try again.");
} finally {
  setLoading(false);
}

}

return ( <main className="login-page"> <section className="login-card"> <div className="login-brand-icon"> <Bot size={30} /> </div>

    <h1>Welcome back</h1>
    <p className="login-subtitle">
      Sign in to your ReceptionAI workspace.
    </p>

    <form onSubmit={handleSubmit}>
      <label htmlFor="admin-email">Admin email</label>

      <div className="login-input">
        <Mail size={18} />
        <input
          id="admin-email"
          type="email"
          placeholder="admin@example.com"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="username"
          required
        />
      </div>

      <label htmlFor="admin-password">Password</label>

      <div className="login-input">
        <LockKeyhole size={18} />
        <input
          id="admin-password"
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          required
        />
      </div>

      {error && (
        <div className="login-error" role="alert">
          {error}
        </div>
      )}

      <button
        className="login-submit"
        type="submit"
        disabled={loading}
      >
        {loading ? "Signing in..." : "Sign in"}
      </button>
    </form>

    <p className="login-security-note">
      Authorized administrators only.
    </p>
  </section>
</main>

);
}
