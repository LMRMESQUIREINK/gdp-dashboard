"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { getBrowserSupabase } from "../../lib/supabaseBrowser";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"sign-in" | "sign-up">("sign-in");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const supabase = getBrowserSupabase();
      const { error: authError } =
        mode === "sign-in"
          ? await supabase.auth.signInWithPassword({ email, password })
          : await supabase.auth.signUp({ email, password });
      if (authError) {
        setError(authError.message);
        return;
      }
      router.push("/campaign/new");
    } catch (err) {
      // getBrowserSupabase() throws readSupabaseEnv()'s configuration
      // error when NEXT_PUBLIC_SUPABASE_URL/_ANON_KEY aren't set -- true
      // in this sandbox, which has no live Supabase project. Surfaced
      // here as a real, visible error rather than a silent failure.
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: "420px", margin: "4rem auto", padding: "0 1.25rem" }}>
      <h1 style={{ fontFamily: "var(--font-display)", fontSize: "1.3rem" }}>
        {mode === "sign-in" ? "Sign in" : "Create an account"}
      </h1>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "1rem", marginTop: "1.5rem" }}>
        <label style={{ display: "grid", gap: "0.4rem", fontSize: "0.82rem", color: "var(--ink2)" }}>
          Email
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label style={{ display: "grid", gap: "0.4rem", fontSize: "0.82rem", color: "var(--ink2)" }}>
          Password
          <input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {error && <div className="error-banner">{error}</div>}
        <button type="submit" className="btn-primary" disabled={busy}>
          {busy ? "Working..." : mode === "sign-in" ? "Sign in" : "Create account"}
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => setMode(mode === "sign-in" ? "sign-up" : "sign-in")}
        >
          {mode === "sign-in" ? "Need an account? Sign up" : "Already have an account? Sign in"}
        </button>
      </form>
    </div>
  );
}
