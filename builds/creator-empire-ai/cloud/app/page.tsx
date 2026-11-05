import Link from "next/link";
import { SuiteLibrary } from "../components/SuiteLibrary";

export default function HomePage() {
  return (
    <div style={{ maxWidth: "1040px", margin: "0 auto", padding: "0 1.25rem 4rem" }}>
      <header style={{ padding: "1.75rem 0", borderBottom: "1px solid var(--rule)", marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
          <span style={{
            width: 28, height: 28, borderRadius: 6, display: "inline-block",
            background: "linear-gradient(145deg, var(--ember), var(--ember-bright))",
          }} />
          <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.5rem" }}>
            Creator Empire <span style={{ color: "var(--ember)" }}>AI</span>
          </span>
        </div>
        <p style={{ fontFamily: "var(--font-display)", fontSize: "1.05rem", color: "var(--ink2)", margin: "0.5rem 0 0.75rem" }}>
          One product image. One finished campaign.
        </p>
        <span style={{
          display: "inline-block", fontSize: "0.72rem", color: "var(--ink2)",
          background: "var(--surface)", border: "1px solid var(--rule)", borderRadius: "999px",
          padding: "0.15rem 0.75rem",
        }}>
          Cloud Edition &mdash; not deployed in this sandbox, see README.md
        </span>
      </header>

      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
        <Link href="/campaign/new" className="btn-primary" style={{ textDecoration: "none", display: "inline-block" }}>
          Start a campaign &rarr;
        </Link>
        <Link href="/login" className="btn-secondary" style={{ textDecoration: "none", display: "inline-block" }}>
          Sign in
        </Link>
      </div>

      <SuiteLibrary />

      <footer style={{
        marginTop: "3rem", paddingTop: "1.5rem", borderTop: "1px solid var(--rule)",
        fontSize: "0.72rem", color: "var(--ink2)",
      }}>
        This is a reference/demo workflow. Nothing here renders a finished
        video or implies a brand partnership for any example brief used.
        Of the 18 apps in the library above, 6 are real and working; 12
        remain planned. See <code>README.md</code> for what&rsquo;s deployed
        vs. scaffolded in this edition.
      </footer>
    </div>
  );
}
