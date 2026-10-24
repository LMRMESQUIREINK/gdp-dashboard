import { test } from "node:test";
import assert from "node:assert/strict";
import { campaignToMarkdown } from "../lib/exportCampaign";
import { emptyCampaign } from "../lib/campaign";

test("campaignToMarkdown contains the real campaign data, not placeholders", () => {
  const campaign = emptyCampaign(
    {
      brand: "Goli Nutrition", product: "ACV gummies", audience: "busy parents",
      benefit: "benefit", duration_seconds: 40, aspect_ratio: "9:16",
    },
    "proj-1",
    "user-1"
  );
  campaign.modules.selected_hook = "What if one product photo could become a campaign?";
  campaign.modules.sales_script = [{ part: "Hook", text: campaign.modules.selected_hook }];
  campaign.modules.storyboard = [{ start: 0, end: 5, label: "Opening hook", desc: "desc" }];
  campaign.modules.beat_map = { intro: "R&B", drop: "Hip-Hop", transition_second: 12 };
  campaign.modules.ad_creatives = [{ audience: "creators", hook: "ad hook" }];

  const md = campaignToMarkdown(campaign);
  assert.match(md, /Goli Nutrition/);
  assert.match(md, /What if one product photo/);
  assert.match(md, /00–05s/);
  assert.match(md, /Hip-Hop/);
  assert.match(md, /ad hook/);
});

test("campaignToMarkdown handles a campaign with no beat map yet, without crashing", () => {
  const campaign = emptyCampaign(
    {
      brand: "b", product: "p", audience: "a", benefit: "ben",
      duration_seconds: 15, aspect_ratio: "1:1",
    },
    "proj-2",
    "user-2"
  );
  const md = campaignToMarkdown(campaign);
  assert.match(md, /none selected/);
  assert.doesNotMatch(md, /undefined/);
});
