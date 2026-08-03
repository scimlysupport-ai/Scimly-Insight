import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerAccount, googleLoginUrl, githubLoginUrl } from "../services/authService";
import { useAuthStore } from "../store/useAuthStore";

export default function Register() {
  const navigate = useNavigate();
  const logIn = useAuthStore((s) => s.logIn);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const { access_token, user } = await registerAccount(email, password, name);
      logIn(access_token, user);
      navigate("/account");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Couldn't create your account. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6">
      <div className="w-full max-w-sm bg-scimly-surface border border-scimly-border rounded-xl p-6">
        <h1 className="font-display text-2xl font-semibold mb-1">Create an account</h1>
        <p className="text-scimly-muted text-sm mb-6">
          Your uploads and dashboards on this browser will move to your new account.
        </p>

        <div className="space-y-2 mb-5">
          <a
            href={googleLoginUrl()}
            className="flex items-center justify-center gap-2 w-full text-sm px-3 py-2 rounded-lg border border-scimly-border text-scimly-text hover:bg-scimly-bg"
          >
            Continue with Google
          </a>
          <a
            href={githubLoginUrl()}
            className="flex items-center justify-center gap-2 w-full text-sm px-3 py-2 rounded-lg border border-scimly-border text-scimly-text hover:bg-scimly-bg"
          >
            Continue with GitHub
          </a>
        </div>

        <div className="flex items-center gap-3 mb-5">
          <div className="h-px bg-scimly-border flex-1" />
          <span className="text-scimly-muted text-xs">or</span>
          <div className="h-px bg-scimly-border flex-1" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="text"
            placeholder="Name (optional)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-scimly-bg border border-scimly-border rounded-lg px-3 py-2 text-sm text-scimly-text"
          />
          <input
            type="email"
            required
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-scimly-bg border border-scimly-border rounded-lg px-3 py-2 text-sm text-scimly-text"
          />
          <input
            type="password"
            required
            minLength={8}
            placeholder="Password (min 8 characters)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-scimly-bg border border-scimly-border rounded-lg px-3 py-2 text-sm text-scimly-text"
          />

          {error && (
            <p className="text-red-400 text-sm bg-red-400/10 border border-red-400/30 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full text-sm px-3 py-2 rounded-lg bg-scimly-primary text-scimly-bg font-medium disabled:opacity-50"
          >
            {submitting ? "Creating account…" : "Sign up"}
          </button>
        </form>

        <p className="text-scimly-muted text-sm mt-5 text-center">
          Already have an account?{" "}
          <Link to="/login" className="text-scimly-primary hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
