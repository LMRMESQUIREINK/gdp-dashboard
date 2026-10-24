"use client";
import { useState } from "react";
import type { CampaignBrief, ScriptPart, StoryboardScene, BeatMap, AdCreative } from "../lib/campaign";
import { generateScript, generateStoryboard, generateBeatMap, generateAds, timeLabel } from "../lib/generators";
import { campaignToMarkdown, downloadFile } from "../lib/exportCampaign";
import { getBrowserSupabase } from "../lib/supabaseBrowser";

const STEP_NAMES = ["Basics", "Hooks", "Script", "Storyboard", "Music", "Ads", "Export"];

export function CampaignWizard() {
  const [step, setStep] = useState(1);

  const [brand, setBrand] = useState("Goli Nutrition");
  const [product, setProduct] = useState("Apple Cider Vinegar gummies");
  const [audience, setAudience] = useState("busy parents who want an easy wellness habit");
  const [benefit, setBenefit] = useState("a gut-health habit that actually tastes good");
  const [duration, setDuration] = useState<"15" | "40" | "60">("40");
  const [ratio, setRatio] = useState<"9:16" | "1:1" | "16:9">("9:16");

  const [hooks, setHooks] = useState<string[]>([]);
  const [hooksLoading, setHooksLoading] = useState(false);
  const [hooksError, setHooksError] = useState<string | null>(null);
  const [selectedHook, setSelectedHook] = useState<string | null>(null);

  const [script, setScript] = useState<ScriptPart[]>([]);
  const [storyboard, setStoryboard] = useState<StoryboardScene[]>([]);

  const [genreIntro, setGenreIntro] = useState("R&B");
  const [genreDrop, setGenreDrop] = useState("Hip-Hop");
  const [transitionPct, setTransitionPct] = useState(30);
  const [beatMap, setBeatMap] = useState<BeatMap | null>(null);

  const [ads, setAds] = useState<AdCreative[]>([]);

  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [saveError, setSaveError] = useState<string | null>(null);

  function currentBrief(): CampaignBrief {
    return { brand, product, audience, benefit, duration_seconds: Number(duration) as 15 | 40 | 60, aspect_ratio: ratio };
  }

  async function handleGenerateHooks() {
    setHooksLoading(true);
    setHooksError(null);
    setSelectedHook(null);
    try {
      const supabase = getBrowserSupabase();
      const { data } = await supabase.auth.getSession();
      const token = data.session?.access_token;
      if (!token) {
        setHooksError("Sign in first -- /api/generate requires an authenticated session.");
        return;
      }
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(currentBrief()),
      });
      const json = (await res.json()) as { hooks?: string[]; error?: string };
      if (!res.ok) {
        setHooksError(json.error ?? `Request failed (${res.status})`);
        return;
      }
      setHooks(json.hooks ?? []);
    } catch (err) {
      // getBrowserSupabase() throws a configuration error when no live
      // Supabase project is configured -- true in this sandbox. Shown
      // as a real error, not swallowed.
      setHooksError(err instanceof Error ? err.message : "Unknown error contacting /api/generate");
    } finally {
      setHooksLoading(false);
    }
  }

  function goToHooks() {
    setStep(2);
    void handleGenerateHooks();
  }

  function pickHook(hook: string) {
    setSelectedHook(hook);
  }

  function goToScript() {
    if (!selectedHook) return;
    setScript(generateScript(currentBrief(), selectedHook));
    setStep(3);
  }

  function goToStoryboard() {
    setStoryboard(generateStoryboard(currentBrief()));
    setStep(4);
  }

  function recomputeBeatMap(intro: string, drop: string, pct: number) {
    setBeatMap(generateBeatMap(intro, drop, pct, Number(duration)));
  }

  function goToMusic() {
    recomputeBeatMap(genreIntro, genreDrop, transitionPct);
    setStep(5);
  }

  function goToAds() {
    setAds(generateAds(currentBrief()));
    setStep(6);
  }

  function buildCampaign() {
    const now = new Date().toISOString();
    return {
      project_id: "local-" + Date.now(),
      owner_id: "",
      ...currentBrief(),
      modules: {
        hooks,
        selected_hook: selectedHook,
        sales_script: script,
        storyboard,
        beat_map: beatMap,
        ad_creatives: ads,
      },
      status: "draft" as const,
      created_at: now,
      updated_at: now,
    };
  }

  async function handleSaveToCloud() {
    setSaveState("saving");
    setSaveError(null);
    try {
      const supabase = getBrowserSupabase();
      const { data: userData } = await supabase.auth.getUser();
      if (!userData?.user) {
        setSaveState("error");
        setSaveError("Sign in first -- saving writes to your own row, protected by row-level security.");
        return;
      }
      const brief = currentBrief();
      const { error } = await supabase.from("projects").insert({
        owner_id: userData.user.id,
        brand: brief.brand,
        product: brief.product,
        audience: brief.audience,
        benefit: brief.benefit,
        duration_seconds: brief.duration_seconds,
        aspect_ratio: brief.aspect_ratio,
        modules: { hooks, selected_hook: selectedHook, sales_script: script, storyboard, beat_map: beatMap, ad_creatives: ads },
        status: "ready",
      });
      if (error) {
        setSaveState("error");
        setSaveError(error.message);
        return;
      }
      setSaveState("saved");
    } catch (err) {
      setSaveState("error");
      setSaveError(err instanceof Error ? err.message : "Unknown error saving to Supabase");
    }
  }

  return (
    <div style={{ maxWidth: "1040px", margin: "0 auto", padding: "0 1.25rem 4rem" }}>
      <nav style={{ display: "flex", gap: "0.5rem", margin: "1.5rem 0", flexWrap: "wrap" }}>
        {STEP_NAMES.map((name, idx) => {
          const n = idx + 1;
          return (
            <button
              key={name}
              type="button"
              className="btn-secondary"
              style={{
                fontSize: "0.72rem", padding: "0.25rem 0.75rem", borderRadius: 999,
                borderColor: n === step ? "var(--ember)" : "var(--rule)",
                color: n < step ? "var(--cyan)" : "var(--ink)",
              }}
              onClick={() => { if (n <= step) setStep(n); }}
            >
              {n} &middot; {name}
            </button>
          );
        })}
      </nav>

      <div style={{
        background: "var(--surface)", border: "1px solid var(--rule)", borderRadius: 12, padding: "1.75rem",
      }}>
        {step === 1 && (
          <div>
            <h2 style={{ fontFamily: "var(--font-display)" }}>01 &middot; Campaign basics</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", marginTop: "1rem" }}>
              <label>Brand / product name
                <input type="text" value={brand} onChange={(e) => setBrand(e.target.value)} />
              </label>
              <label>Product in one phrase
                <input type="text" value={product} onChange={(e) => setProduct(e.target.value)} />
              </label>
              <label>Target audience
                <input type="text" value={audience} onChange={(e) => setAudience(e.target.value)} />
              </label>
              <label>Main benefit / outcome
                <input type="text" value={benefit} onChange={(e) => setBenefit(e.target.value)} />
              </label>
              <label>Campaign duration
                <select value={duration} onChange={(e) => setDuration(e.target.value as "15" | "40" | "60")}>
                  <option value="15">15 seconds</option>
                  <option value="40">40 seconds</option>
                  <option value="60">60 seconds</option>
                </select>
              </label>
              <label>Aspect ratio
                <select value={ratio} onChange={(e) => setRatio(e.target.value as "9:16" | "1:1" | "16:9")}>
                  <option value="9:16">9:16 (Reels/TikTok/Shorts)</option>
                  <option value="1:1">1:1 (Feed)</option>
                  <option value="16:9">16:9 (YouTube)</option>
                </select>
              </label>
            </div>
            <button type="button" className="btn-primary" style={{ marginTop: "1.5rem" }} onClick={goToHooks}>
              Generate hooks &rarr;
            </button>
          </div>
        )}

        {step === 2 && (
          <div>
            <h2 style={{ fontFamily: "var(--font-display)" }}>02 &middot; Hook Generator</h2>
            <p style={{ color: "var(--ink2)", fontSize: "0.88rem" }}>
              Calls the real <code>/api/generate</code> endpoint (OpenAI, server-side key).
            </p>
            <button type="button" className="btn-secondary" onClick={() => void handleGenerateHooks()} disabled={hooksLoading}>
              {hooksLoading ? "Generating..." : "↻ Generate new set"}
            </button>
            {hooksError && <div className="error-banner" style={{ marginTop: "1rem" }}>{hooksError}</div>}
            <div style={{ display: "grid", gap: "0.75rem", marginTop: "1rem" }}>
              {hooks.map((hook) => (
                <div
                  key={hook}
                  onClick={() => pickHook(hook)}
                  style={{
                    background: "var(--elevated)", border: `1px solid ${selectedHook === hook ? "var(--ember)" : "var(--rule)"}`,
                    borderRadius: 10, padding: "1rem", cursor: "pointer",
                  }}
                >
                  {hook}
                </div>
              ))}
            </div>
            <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem" }}>
              <button type="button" className="btn-secondary" onClick={() => setStep(1)}>&larr; Back</button>
              <button type="button" className="btn-primary" disabled={!selectedHook} onClick={goToScript}>
                Build the script &rarr;
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <h2 style={{ fontFamily: "var(--font-display)" }}>03 &middot; Sales Video Scriptwriter</h2>
            <div style={{ display: "grid", gap: "0.75rem", marginTop: "1rem" }}>
              {script.map((part) => (
                <div key={part.part} style={{ background: "var(--elevated)", borderLeft: "3px solid var(--ember)", borderRadius: "0 8px 8px 0", padding: "0.85rem 1rem" }}>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.68rem", color: "var(--ember-bright)", textTransform: "uppercase" }}>{part.part}</div>
                  <div>{part.text}</div>
                </div>
              ))}
            </div>
            <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem" }}>
              <button type="button" className="btn-secondary" onClick={() => setStep(2)}>&larr; Back</button>
              <button type="button" className="btn-primary" onClick={goToStoryboard}>Build the storyboard &rarr;</button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div>
            <h2 style={{ fontFamily: "var(--font-display)" }}>04 &middot; Cinematic Storyboard Studio</h2>
            <div style={{ display: "grid", gap: "0.75rem", marginTop: "1rem" }}>
              {storyboard.map((scene) => (
                <div key={scene.label} style={{ display: "grid", gridTemplateColumns: "90px 1fr", gap: "1rem", background: "var(--elevated)", border: "1px solid var(--rule)", borderRadius: 10, padding: "1rem" }}>
                  <div style={{ fontFamily: "var(--font-mono)", color: "var(--cyan)" }}>{timeLabel(scene)}</div>
                  <div>
                    <strong>{scene.label}</strong>
                    <div style={{ color: "var(--ink2)", fontSize: "0.88rem" }}>{scene.desc}</div>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem" }}>
              <button type="button" className="btn-secondary" onClick={() => setStep(3)}>&larr; Back</button>
              <button type="button" className="btn-primary" onClick={goToMusic}>Pick the music transition &rarr;</button>
            </div>
          </div>
        )}

        {step === 5 && (
          <div>
            <h2 style={{ fontFamily: "var(--font-display)" }}>05 &middot; Music Video Director + Beat Transition Designer</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", marginTop: "1rem" }}>
              <label>Intro genre
                <select value={genreIntro} onChange={(e) => { setGenreIntro(e.target.value); recomputeBeatMap(e.target.value, genreDrop, transitionPct); }}>
                  <option>R&amp;B</option><option>Lo-fi</option><option>Acoustic</option><option>Ambient</option>
                </select>
              </label>
              <label>Drop genre
                <select value={genreDrop} onChange={(e) => { setGenreDrop(e.target.value); recomputeBeatMap(genreIntro, e.target.value, transitionPct); }}>
                  <option>Hip-Hop</option><option>EDM</option><option>Pop</option><option>Afrobeat</option>
                </select>
              </label>
              <label>Transition lands at
                <input
                  type="range" min={20} max={70} value={transitionPct}
                  onChange={(e) => { const v = Number(e.target.value); setTransitionPct(v); recomputeBeatMap(genreIntro, genreDrop, v); }}
                />
              </label>
            </div>
            {beatMap && (
              <p style={{ color: "var(--ink2)", fontSize: "0.85rem" }}>
                transition at {beatMap.transition_second}s ({transitionPct}%)
              </p>
            )}
            <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem" }}>
              <button type="button" className="btn-secondary" onClick={() => setStep(4)}>&larr; Back</button>
              <button type="button" className="btn-primary" onClick={goToAds}>Generate ad creatives &rarr;</button>
            </div>
          </div>
        )}

        {step === 6 && (
          <div>
            <h2 style={{ fontFamily: "var(--font-display)" }}>06 &middot; Ad Creative Generator</h2>
            <div style={{ display: "grid", gap: "0.75rem", marginTop: "1rem" }}>
              {ads.map((ad, i) => (
                <div key={ad.hook} style={{ background: "var(--elevated)", border: "1px solid var(--rule)", borderRadius: 10, padding: "1rem" }}>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.68rem", color: "var(--ink2)", textTransform: "uppercase" }}>
                    Ad {String.fromCharCode(65 + i)} &middot; {ad.audience}
                  </div>
                  <div>{ad.hook}</div>
                </div>
              ))}
            </div>
            <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem" }}>
              <button type="button" className="btn-secondary" onClick={() => setStep(5)}>&larr; Back</button>
              <button type="button" className="btn-primary" onClick={() => setStep(7)}>Export campaign package &rarr;</button>
            </div>
          </div>
        )}

        {step === 7 && (
          <div>
            <h2 style={{ fontFamily: "var(--font-display)" }}>Campaign package</h2>
            <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", margin: "1rem 0" }}>
              <button type="button" className="btn-primary" onClick={() => void handleSaveToCloud()} disabled={saveState === "saving"}>
                {saveState === "saving" ? "Saving..." : "💾 Save to Supabase"}
              </button>
              <button type="button" className="btn-secondary" onClick={() => downloadFile("campaign.json", JSON.stringify(buildCampaign(), null, 2), "application/json")}>
                &#8681; Export campaign.json
              </button>
              <button type="button" className="btn-secondary" onClick={() => downloadFile("campaign-brief.md", campaignToMarkdown(buildCampaign()), "text/markdown")}>
                &#8681; Export campaign-brief.md
              </button>
            </div>
            {saveState === "saved" && <div style={{ color: "var(--cyan)", fontSize: "0.85rem" }}>Saved.</div>}
            {saveState === "error" && saveError && <div className="error-banner">{saveError}</div>}
            <pre style={{
              background: "#0C0810", border: "1px solid var(--rule)", borderRadius: 8, padding: "1rem",
              fontFamily: "var(--font-mono)", fontSize: "0.78rem", color: "var(--ink2)", overflowX: "auto", maxHeight: 420,
            }}>
              {JSON.stringify(buildCampaign(), null, 2)}
            </pre>
            <button type="button" className="btn-secondary" style={{ marginTop: "1rem" }} onClick={() => setStep(6)}>&larr; Back</button>
          </div>
        )}
      </div>
    </div>
  );
}
