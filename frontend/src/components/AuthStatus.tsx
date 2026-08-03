import { Link } from "react-router-dom";
import { useAuthStore } from "../store/useAuthStore";

// Phase 12 — Authentication.
// Dropped into every page's header: shows "Log in" when nobody's
// signed in, or the account name + a link to /account when they are.
export default function AuthStatus() {
  const user = useAuthStore((s) => s.user);

  if (!user) {
    return (
      <Link to="/login" className="text-scimly-primary text-sm hover:underline">
        Log in
      </Link>
    );
  }

  return (
    <Link
      to="/account"
      className="flex items-center gap-2 text-sm text-scimly-muted hover:text-scimly-text"
      title="Account"
    >
      {user.avatar_url ? (
        <img src={user.avatar_url} alt="" className="w-6 h-6 rounded-full" />
      ) : (
        <span className="w-6 h-6 rounded-full bg-scimly-primary/20 text-scimly-primary flex items-center justify-center text-xs font-medium">
          {(user.name || user.email || "?").charAt(0).toUpperCase()}
        </span>
      )}
      <span className="max-w-[10rem] truncate">{user.name || user.email}</span>
    </Link>
  );
}
