import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { fetchMe } from "../services/authService";
import { useAuthStore } from "../store/useAuthStore";

// Phase 12 — Authentication.
// Google/GitHub redirect here (via the backend) with ?token=<jwt>.
// This page's only job is to store that token and land on /account —
// there's nothing for the person to look at, so it just shows a brief
// "Signing you in…" state.
export default function AuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const logIn = useAuthStore((s) => s.logIn);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setError("Missing login token. Please try logging in again.");
      return;
    }

    useAuthStore.setState({ token });
    fetchMe()
      .then((user) => {
        logIn(token, user);
        navigate("/account", { replace: true });
      })
      .catch(() => {
        useAuthStore.setState({ token: null });
        setError("Couldn't complete login. Please try again.");
      });
  }, [searchParams, navigate, logIn]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6">
      {error ? (
        <p className="text-red-400 text-sm bg-red-400/10 border border-red-400/30 rounded-lg px-4 py-3">
          {error}
        </p>
      ) : (
        <p className="text-scimly-muted text-sm">Signing you in…</p>
      )}
    </div>
  );
}
