import { test } from "node:test";
import assert from "node:assert/strict";
import { validateBrief, emptyCampaign } from "../lib/campaign";

test("validateBrief accepts a well-formed brief", () => {
  const result = validateBrief({
    brand: "Goli Nutrition",
    product: "ACV gummies",
    audience: "busy parents",
    benefit: "a gut-health habit that actually tastes good",
    duration_seconds: 40,
    aspect_ratio: "9:16",
  });
  assert.equal(result.ok, true);
  if (result.ok) {
    assert.equal(result.brief.brand, "Goli Nutrition");
    assert.equal(result.brief.duration_seconds, 40);
  }
});

test("validateBrief trims whitespace from string fields", () => {
  const result = validateBrief({
    brand: "  Goli Nutrition  ",
    product: "ACV gummies",
    audience: "busy parents",
    benefit: "benefit",
    duration_seconds: 15,
    aspect_ratio: "1:1",
  });
  assert.equal(result.ok, true);
  if (result.ok) assert.equal(result.brief.brand, "Goli Nutrition");
});

test("validateBrief rejects a non-object body", () => {
  const result = validateBrief("not an object");
  assert.equal(result.ok, false);
});

test("validateBrief rejects a missing required field", () => {
  const result = validateBrief({
    brand: "Goli Nutrition",
    product: "ACV gummies",
    audience: "",
    benefit: "benefit",
    duration_seconds: 40,
    aspect_ratio: "9:16",
  });
  assert.equal(result.ok, false);
  if (!result.ok) {
    assert.ok(result.errors.some((e) => e.field === "audience"));
  }
});

test("validateBrief rejects an overlong field", () => {
  const result = validateBrief({
    brand: "x".repeat(201),
    product: "p",
    audience: "a",
    benefit: "b",
    duration_seconds: 40,
    aspect_ratio: "9:16",
  });
  assert.equal(result.ok, false);
  if (!result.ok) assert.ok(result.errors.some((e) => e.field === "brand"));
});

test("validateBrief rejects an invalid duration_seconds value", () => {
  const result = validateBrief({
    brand: "b", product: "p", audience: "a", benefit: "ben",
    duration_seconds: 999, aspect_ratio: "9:16",
  });
  assert.equal(result.ok, false);
  if (!result.ok) assert.ok(result.errors.some((e) => e.field === "duration_seconds"));
});

test("validateBrief rejects an invalid aspect_ratio value", () => {
  const result = validateBrief({
    brand: "b", product: "p", audience: "a", benefit: "ben",
    duration_seconds: 40, aspect_ratio: "21:9",
  });
  assert.equal(result.ok, false);
  if (!result.ok) assert.ok(result.errors.some((e) => e.field === "aspect_ratio"));
});

test("validateBrief reports every invalid field, not just the first", () => {
  const result = validateBrief({
    brand: "", product: "", audience: "a", benefit: "b",
    duration_seconds: 7, aspect_ratio: "bad",
  });
  assert.equal(result.ok, false);
  if (!result.ok) {
    const fields = result.errors.map((e) => e.field).sort();
    assert.deepEqual(fields, ["aspect_ratio", "brand", "duration_seconds", "product"]);
  }
});

test("emptyCampaign builds a correctly-shaped draft record", () => {
  const brief = {
    brand: "Goli Nutrition", product: "ACV gummies", audience: "busy parents",
    benefit: "benefit", duration_seconds: 40 as const, aspect_ratio: "9:16" as const,
  };
  const campaign = emptyCampaign(brief, "proj-123", "user-456");
  assert.equal(campaign.project_id, "proj-123");
  assert.equal(campaign.owner_id, "user-456");
  assert.equal(campaign.status, "draft");
  assert.deepEqual(campaign.modules.hooks, []);
  assert.equal(campaign.modules.selected_hook, null);
  assert.equal(campaign.created_at, campaign.updated_at);
});
