// Server component (no hooks, static data) -- the same honest 6-live/
// 12-planned library data as standalone/assets/app.js's SUITES array,
// kept in sync by hand since the two editions are genuinely separate
// codebases (plain JS vs. TypeScript/React); see README.md.
export interface SuiteApp {
  name: string;
  live: boolean;
}

export interface Suite {
  num: string;
  name: string;
  apps: SuiteApp[];
}

export const SUITES: Suite[] = [
  { num: "01", name: "Video Lab", apps: [
    { name: "Hook Generator", live: true },
    { name: "Sales Video Scriptwriter", live: true },
    { name: "Cinematic Storyboard Studio", live: true },
  ]},
  { num: "02", name: "Music Lab", apps: [
    { name: "Music Video Director", live: true },
    { name: "Beat Transition Designer", live: true },
    { name: "Audio Sync Planner", live: false },
  ]},
  { num: "03", name: "Content Lab", apps: [
    { name: "Reels Factory", live: false },
    { name: "Ad Creative Generator", live: true },
    { name: "Social Content Calendar", live: false },
  ]},
  { num: "04", name: "Sales Lab", apps: [
    { name: "Funnel Architect", live: false },
    { name: "VSL Conversion Builder", live: false },
    { name: "Offer & Bonus Engine", live: false },
  ]},
  { num: "05", name: "Automation Lab", apps: [
    { name: "Campaign Launch Manager", live: false },
    { name: "Lead Follow-Up Builder", live: false },
    { name: "Analytics & Optimization", live: false },
  ]},
  { num: "06", name: "Agency Lab", apps: [
    { name: "Client Campaign Portal", live: false },
    { name: "Agency Proposal Generator", live: false },
    { name: "White-Label Workspace", live: false },
  ]},
];

export function SuiteLibrary() {
  return (
    <section style={{ marginTop: "2.25rem" }}>
      <h2 style={{
        fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.12em",
        color: "var(--ink2)", borderBottom: "1px solid var(--rule)", paddingBottom: "0.5rem",
      }}>
        The library &mdash; what&rsquo;s live today vs. planned
      </h2>
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
        gap: "0.75rem", marginTop: "1rem",
      }}>
        {SUITES.map((suite) => {
          const liveCount = suite.apps.filter((a) => a.live).length;
          return (
            <div key={suite.num} style={{
              background: "var(--surface)", border: "1px solid var(--rule)",
              borderRadius: "10px", padding: "0.85rem",
            }}>
              <h3 style={{ fontFamily: "var(--font-display)", fontSize: "0.95rem", margin: "0 0 0.5rem", display: "flex", gap: "0.6rem" }}>
                <span style={{ color: "var(--ember)", fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>{suite.num}</span>
                {suite.name}
                <span style={{ marginLeft: "auto", color: "var(--ink2)", fontSize: "0.72rem" }}>{liveCount}/3 live</span>
              </h3>
              <ul style={{ listStyle: "none", margin: 0, padding: 0, fontSize: "0.82rem" }}>
                {suite.apps.map((app) => (
                  <li key={app.name} className={app.live ? "status-live-row" : "status-planned-row"} style={{
                    display: "flex", justifyContent: "space-between", gap: "0.5rem",
                    padding: "0.3rem 0", color: "var(--ink2)", borderTop: "1px solid var(--rule)",
                  }}>
                    {app.name}
                    <span data-status={app.live ? "live" : "planned"} style={{
                      fontFamily: "var(--font-mono)", fontSize: "0.62rem", letterSpacing: "0.04em",
                      padding: "1px 6px", borderRadius: "4px",
                      color: app.live ? "var(--cyan)" : "var(--ink2)",
                      border: `1px solid ${app.live ? "var(--cyan)" : "var(--rule)"}`,
                    }}>
                      {app.live ? "LIVE" : "PLANNED"}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </section>
  );
}
