import "./App.css";
import { useEffect, useState } from "react";
import { AppShell } from "./layouts/AppShell";
import { getCurrentUser, getAuthToken, login, register, setAuthToken } from "./services/backend";
import type { AuthUser } from "./types/api";

const AUTH_USER_STORAGE_KEY = "local-chat-auth-user";
const AUTH_TOKEN_STORAGE_KEY = "local-chat-auth-token";

function loadStoredUser(): AuthUser | null {
  try {
    const raw = window.localStorage.getItem(AUTH_USER_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as AuthUser;
    if (typeof parsed?.id !== "number" || typeof parsed?.username !== "string") {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export default function App() {
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [registerMode, setRegisterMode] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    if (storedToken) {
      setAuthToken(storedToken);
    }

    const stored = loadStoredUser();
    if (!stored) {
      return;
    }

    void (async () => {
      try {
        const refreshed = await getCurrentUser(stored.id);
        setCurrentUser(refreshed);
        window.localStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(refreshed));
        const refreshedToken = getAuthToken();
        if (refreshedToken) {
          window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, refreshedToken);
        }
      } catch {
        window.localStorage.removeItem(AUTH_USER_STORAGE_KEY);
        window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
        setAuthToken(null);
        setError("Gespeicherte Anmeldung ist ungueltig oder nicht mehr vorhanden. Bitte erneut einloggen.");
      }
    })();
  }, []);

  const handleLogout = () => {
    window.localStorage.removeItem(AUTH_USER_STORAGE_KEY);
    window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    setAuthToken(null);
    setCurrentUser(null);
    setUsername("");
    setPassword("");
    setError(null);
  };

  if (currentUser) {
    return <AppShell currentUser={currentUser} onLogout={handleLogout} />;
  }

  return (
    <main className="auth-screen">
      <form
        className="auth-card"
        aria-label="Anmeldung"
        onSubmit={(event) => {
          event.preventDefault();
          void (async () => {
            setPending(true);
            setError(null);
            try {
              const trimmedName = username.trim();
              const trimmedPassword = password.trim();
              if (!trimmedName || !trimmedPassword) {
                setError("Bitte Benutzername und Passwort eingeben.");
                return;
              }

              const user = registerMode
                ? await register(trimmedName, trimmedPassword)
                : await login(trimmedName, trimmedPassword);

              setCurrentUser(user);
              window.localStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(user));
              const token = getAuthToken();
              if (token) {
                window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
              }
            } catch (apiError) {
              const message = apiError instanceof Error ? apiError.message : "Anmeldung fehlgeschlagen.";
              setError(message);
            } finally {
              setPending(false);
            }
          })();
        }}
      >
        <div className="auth-brand" aria-hidden="true">
          <img src="/kernschmiede-logo.svg" alt="" className="auth-brand__logo" />
          <div className="auth-brand__title">Kernschmiede</div>
          <div className="auth-brand__subtitle">Local AI Workbench</div>
        </div>
        <h1>{registerMode ? "Konto erstellen" : "Anmelden"}</h1>
        <p>Mit deinem Konto anmelden und deinen Namen im Workspace sehen.</p>

        <label className="auth-field">
          <span>Benutzername</span>
          <input
            type="text"
            name="username"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
        </label>

        <label className="auth-field">
          <span>Passwort</span>
          <input
            type="password"
            name="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>

        {error ? <div className="auth-error" role="alert">{error}</div> : null}

        <button
          type="submit"
          className="action-btn action-btn--primary"
          disabled={pending}
        >
          {pending ? "Bitte warten..." : registerMode ? "Konto erstellen" : "Anmelden"}
        </button>

        <button
          type="button"
          className="ghost-btn"
          disabled={pending}
          onClick={() => {
            setRegisterMode((current) => !current);
            setError(null);
          }}
        >
          {registerMode ? "Ich habe bereits ein Konto" : "Neues Konto erstellen"}
        </button>
      </form>
    </main>
  );
}
