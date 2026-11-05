import { test } from "node:test";
import assert from "node:assert/strict";
import { generateScript, generateStoryboard, timeLabel, generateBeatMap, generateAds } from "../lib/generators";
import type { CampaignBrief } from "../lib/campaign";

const brief: CampaignBrief = {
  brand: "Goli Nutrition",
  product: "ACV gummies",
  audience: "busy parents",
  benefit: "a gut-health habit that actually tastes good",
  duration_seconds: 40,
  aspect_ratio: "9:16",
};

test("generateScript returns the 7 parts in the documented order", () => {
  const script = generateScript(brief, "a test hook");
  assert.deepEqual(
    script.map((p) => p.part),
    ["Hook", "Problem", "Agitate", "Solution / Demo", "Proof", "Offer", "CTA"]
  );
  assert.equal(script[0]?.text, "a test hook");
});

test("generateStoryboard tiles the full duration with no gaps or overlaps, for every supported length", () => {
  for (const duration of [15, 40, 60] as const) {
    const scenes = generateStoryboard({ ...brief, duration_seconds: duration });
    assert.ok(scenes.length >= 3, `duration ${duration}: expected at least 3 scenes`);
    assert.equal(scenes[0]?.start, 0, `duration ${duration}: first scene should start at 0`);
    assert.equal(
      scenes[scenes.length - 1]?.end,
      duration,
      `duration ${duration}: last scene should end exactly at the duration`
    );
    for (let i = 1; i < scenes.length; i++) {
      assert.equal(
        scenes[i]?.start,
        scenes[i - 1]?.end,
        `duration ${duration}: scene ${i} should start exactly where scene ${i - 1} ends`
      );
    }
  }
});

test("timeLabel zero-pads single-digit seconds", () => {
  assert.equal(timeLabel({ start: 0, end: 5 }), "00–05s");
  assert.equal(timeLabel({ start: 12, end: 25 }), "12–25s");
});

test("generateBeatMap computes the transition second correctly", () => {
  assert.equal(generateBeatMap("R&B", "Hip-Hop", 30, 40).transition_second, 12);
  assert.equal(generateBeatMap("Lo-fi", "EDM", 50, 60).transition_second, 30);
});

test("generateAds returns 3 genuinely distinct ad angles", () => {
  const ads = generateAds(brief);
  assert.equal(ads.length, 3);
  assert.equal(new Set(ads.map((a) => a.hook)).size, 3);
});
