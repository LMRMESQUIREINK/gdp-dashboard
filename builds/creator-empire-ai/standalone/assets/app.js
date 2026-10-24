(function () {
  "use strict";

  // ---------------------------------------------------------------
  // The 6-suite / 18-app library. Only the Phase 1 six apps are
  // "live" (wired to real logic below) -- the other twelve are
  // listed honestly as planned, matching design-rules.md's rule
  // against implying a finished 18-app library.
  // ---------------------------------------------------------------
  var SUITES = [
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

  function renderSuites() {
    var grid = document.getElementById("suite-grid");
    grid.innerHTML = "";
    SUITES.forEach(function (suite) {
      var liveCount = suite.apps.filter(function (a) { return a.live; }).length;
      var card = document.createElement("div");
      card.className = "suite-card";
      var appsHtml = suite.apps.map(function (a) {
        return "<li>" + a.name + "<span class='status-tag " +
          (a.live ? "status-live" : "status-planned") + "'>" +
          (a.live ? "LIVE" : "PLANNED") + "</span></li>";
      }).join("");
      card.innerHTML =
        "<h3><span class='suite-num'>" + suite.num + "</span>" + suite.name +
        " <span style='margin-left:auto;color:var(--ink2);font-size:0.72rem'>" +
        liveCount + "/3 live</span></h3>" +
        "<ul class='suite-apps'>" + appsHtml + "</ul>";
      grid.appendChild(card);
    });
  }

  // ---------------------------------------------------------------
  // Template-based local generation. No AI API call -- this is the
  // Standalone Edition's whole point (per the source plan: "offline
  // creative templates", "structured creative drafts locally").
  // ---------------------------------------------------------------
  function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

  var HOOK_TEMPLATES = [
    function (b) { return "What if " + b.product + " could give " + b.audience + " " + b.benefit + " in under a minute?"; },
    function (b) { return "Stop scrolling if you're " + b.audience + " and tired of waiting for " + b.benefit + "."; },
    function (b) { return "Nobody tells " + b.audience + " this about " + b.product + "..."; },
    function (b) { return b.brand + " didn't just make " + b.product + " -- they made " + b.benefit + " actually happen."; },
    function (b) { return "The real reason " + b.audience + " switch to " + b.product + " (it's not what you think)."; },
    function (b) { return "3 seconds in, you'll know why " + b.audience + " can't stop talking about " + b.product + "."; },
  ];

  function generateHooks(brief) {
    var shuffled = HOOK_TEMPLATES.slice().sort(function () { return Math.random() - 0.5; });
    return shuffled.slice(0, 5).map(function (fn) { return fn(brief); });
  }

  function generateScript(brief, hook) {
    return [
      { part: "Hook", text: hook },
      { part: "Problem", text: "Most " + brief.audience + " struggle to get " + brief.benefit + " without giving up their routine." },
      { part: "Agitate", text: "Every option out there either takes too long, costs too much, or just doesn't work for " + brief.audience + "." },
      { part: "Solution / Demo", text: brief.brand + "'s " + brief.product + " is built for exactly that -- here's what it looks like in your hands." },
      { part: "Proof", text: "Real customers report " + brief.benefit + " within the first few uses -- shown here as a drafted claim, not a verified statistic." },
      { part: "Offer", text: "Right now, " + brief.product + " comes with a starter bundle so you can try it risk-free." },
      { part: "CTA", text: "Tap below to get your " + brief.product + " and start today." },
    ];
  }

  function generateStoryboard(durationSec, brief) {
    durationSec = Number(durationSec);
    var template;
    if (durationSec <= 15) {
      template = [
        { pct: [0, 0.33], label: "Opening hook", desc: "Tight close-up, " + brief.product + " in frame, smooth push-in." },
        { pct: [0.33, 0.73], label: "Product reveal", desc: "Beat-matched jump cuts across " + brief.brand + "'s " + brief.product + "." },
        { pct: [0.73, 1], label: "CTA", desc: "Brand lockup, logo, call to action." },
      ];
    } else if (durationSec <= 40) {
      template = [
        { pct: [0, 0.125], label: "Opening hook", desc: "Soft lighting, intimate camera push, smooth keys." },
        { pct: [0.125, 0.3], label: "Product reveal", desc: "Beat-matched jump cuts showing " + brief.product + "." },
        { pct: [0.3, 0.625], label: "The drop / lifestyle montage", desc: "Higher-energy whip pans, " + brief.audience + " using " + brief.product + " in real life." },
        { pct: [0.625, 1], label: "Product hero and CTA", desc: "Hero shot, brand lockup, " + brief.brand + " call to action." },
      ];
    } else {
      template = [
        { pct: [0, 0.1], label: "Opening hook", desc: "Soft lighting, intimate camera push." },
        { pct: [0.1, 0.25], label: "Problem setup", desc: "Relatable moment: " + brief.audience + " facing the problem " + brief.product + " solves." },
        { pct: [0.25, 0.45], label: "Product reveal", desc: "Beat-matched jump cuts, clean product shots." },
        { pct: [0.45, 0.75], label: "The drop / lifestyle montage", desc: "Higher-energy whip pans and real-life use." },
        { pct: [0.75, 0.9], label: "Proof moment", desc: "A quick, honest result beat -- drafted claim, not a verified stat." },
        { pct: [0.9, 1], label: "Product hero and CTA", desc: "Hero shot, brand lockup, " + brief.brand + " call to action." },
      ];
    }
    return template.map(function (scene) {
      var startSec = Math.round(scene.pct[0] * durationSec);
      var endSec = Math.round(scene.pct[1] * durationSec);
      return { start: startSec, end: endSec, label: scene.label, desc: scene.desc };
    });
  }

  function timeLabel(scene) {
    function fmt(s) { return String(s).padStart(2, "0"); }
    return fmt(scene.start) + "–" + fmt(scene.end) + "s";
  }

  function generateBeatMap(introGenre, dropGenre, transitionPct, durationSec) {
    return {
      intro_genre: introGenre,
      drop_genre: dropGenre,
      transition_second: Math.round((transitionPct / 100) * Number(durationSec)),
      transition_pct: transitionPct,
    };
  }

  var AD_ANGLES = [
    function (b) { return { audience: "Content creators and social media marketers", hook: "What if one product photo could become an entire " + b.benefit + " campaign?" }; },
    function (b) { return { audience: "Agencies and freelance marketers", hook: "Your client needs five ads of " + b.product + " by Friday. Where do you start?" }; },
    function (b) { return { audience: b.audience, hook: "Stop switching between tools just to launch one " + b.brand + " campaign." }; },
  ];

  function generateAds(brief) {
    return AD_ANGLES.map(function (fn) { return fn(brief); });
  }

  // ---------------------------------------------------------------
  // App state + wiring
  // ---------------------------------------------------------------
  var state = {
    step: 1,
    brief: null,
    hooks: [],
    selectedHook: null,
    script: [],
    storyboard: [],
    beatMap: null,
    ads: [],
    imageDataUrl: null,
  };

  function readBrief() {
    return {
      brand: document.getElementById("f-brand").value.trim() || "Your Brand",
      product: document.getElementById("f-product").value.trim() || "your product",
      audience: document.getElementById("f-audience").value.trim() || "your audience",
      benefit: document.getElementById("f-benefit").value.trim() || "the outcome they want",
      duration: document.getElementById("f-duration").value,
      ratio: document.getElementById("f-ratio").value,
    };
  }

  function goToStep(n) {
    for (var i = 1; i <= 7; i++) {
      var panel = document.getElementById("panel-" + i);
      if (panel) panel.hidden = (i !== n);
    }
    state.step = n;
    renderStepper();
  }

  function renderStepper() {
    var names = ["Basics", "Hooks", "Script", "Storyboard", "Music", "Ads", "Export"];
    var nav = document.getElementById("stepper");
    nav.innerHTML = "";
    names.forEach(function (name, idx) {
      var n = idx + 1;
      var pill = document.createElement("button");
      pill.type = "button";
      pill.className = "step-pill" + (n === state.step ? " active" : "") + (n < state.step ? " done" : "");
      pill.textContent = n + " · " + name;
      pill.addEventListener("click", function () {
        if (n <= state.step || n === state.step + 1) goToStep(n);
      });
      nav.appendChild(pill);
    });
  }

  function renderHooks() {
    var list = document.getElementById("hook-list");
    list.innerHTML = "";
    state.hooks.forEach(function (hook, idx) {
      var card = document.createElement("div");
      card.className = "pick-card" + (state.selectedHook === hook ? " selected" : "");
      card.innerHTML =
        "<div><span class='label'>Option " + (idx + 1) + "</span><p>" + hook + "</p></div>" +
        "<span class='pick-radio'></span>";
      card.addEventListener("click", function () {
        state.selectedHook = hook;
        renderHooks();
        document.getElementById("btn-to-3").disabled = false;
      });
      list.appendChild(card);
    });
  }

  function renderScript() {
    var wrap = document.getElementById("script-parts");
    wrap.innerHTML = "";
    state.script.forEach(function (part, idx) {
      var div = document.createElement("div");
      div.className = "script-part";
      div.innerHTML =
        "<div class='part-name'>" + part.part + "</div>" +
        "<textarea data-idx='" + idx + "'>" + part.text + "</textarea>";
      wrap.appendChild(div);
    });
    wrap.querySelectorAll("textarea").forEach(function (ta) {
      ta.addEventListener("input", function () {
        state.script[Number(ta.dataset.idx)].text = ta.value;
      });
    });
  }

  function renderStoryboard() {
    var wrap = document.getElementById("storyboard");
    wrap.innerHTML = "";
    state.storyboard.forEach(function (scene, idx) {
      var div = document.createElement("div");
      div.className = "scene-card";
      div.innerHTML =
        "<div class='scene-time'>" + timeLabel(scene) + "</div>" +
        "<div class='scene-fields'>" +
        "<input data-idx='" + idx + "' data-field='label' value='" + scene.label.replace(/'/g, "&#39;") + "'>" +
        "<input data-idx='" + idx + "' data-field='desc' value='" + scene.desc.replace(/'/g, "&#39;") + "'>" +
        "</div>";
      wrap.appendChild(div);
    });
    wrap.querySelectorAll("input").forEach(function (inp) {
      inp.addEventListener("input", function () {
        state.storyboard[Number(inp.dataset.idx)][inp.dataset.field] = inp.value;
      });
    });
  }

  function renderBeatMap() {
    var wrap = document.getElementById("beat-map");
    var bm = state.beatMap;
    var pct = bm.transition_pct;
    wrap.innerHTML =
      "<div class='beat-seg intro' style='width:" + pct + "%'>" + bm.intro_genre + "</div>" +
      "<div class='beat-seg drop' style='left:" + pct + "%;right:0'>" + bm.drop_genre + " drop</div>" +
      "<div class='beat-marker' style='left:" + pct + "%'></div>";
    document.getElementById("f-transition-pct-out").textContent =
      "transition at " + bm.transition_second + "s (" + pct + "%)";
  }

  function recomputeBeatMap() {
    var brief = state.brief || readBrief();
    state.beatMap = generateBeatMap(
      document.getElementById("f-genre-intro").value,
      document.getElementById("f-genre-drop").value,
      Number(document.getElementById("f-transition-pct").value),
      brief.duration
    );
    renderBeatMap();
  }

  function renderAds() {
    var list = document.getElementById("ad-list");
    list.innerHTML = "";
    state.ads.forEach(function (ad, idx) {
      var div = document.createElement("div");
      div.className = "pick-card";
      div.style.cursor = "default";
      div.innerHTML =
        "<div><span class='label'>Ad " + String.fromCharCode(65 + idx) + " · " + ad.audience + "</span>" +
        "<p>" + ad.hook + "</p></div>";
      list.appendChild(div);
    });
  }

  function buildCampaignObject() {
    var brief = state.brief;
    return {
      project_id: (crypto && crypto.randomUUID) ? crypto.randomUUID() : ("local-" + Date.now()),
      brand: brief.brand,
      product: brief.product,
      audience: brief.audience,
      benefit: brief.benefit,
      duration_seconds: Number(brief.duration),
      aspect_ratio: brief.ratio,
      music: {
        intro: state.beatMap.intro_genre,
        drop: state.beatMap.drop_genre,
        transition_second: state.beatMap.transition_second,
      },
      modules: {
        hooks: state.hooks,
        selected_hook: state.selectedHook,
        sales_script: state.script,
        storyboard: state.storyboard,
        beat_map: state.beatMap,
        ad_creatives: state.ads,
      },
      status: "draft",
      generated_at: new Date().toISOString(),
      edition: "standalone",
    };
  }

  function renderExport() {
    document.getElementById("json-view").textContent =
      JSON.stringify(buildCampaignObject(), null, 2);
  }

  function download(filename, content, mime) {
    var blob = new Blob([content], { type: mime });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function campaignToMarkdown(c) {
    var md = "# " + c.brand + " — " + c.product + "\n\n";
    md += "Audience: " + c.audience + "  \nBenefit: " + c.benefit + "  \n";
    md += "Duration: " + c.duration_seconds + "s · " + c.aspect_ratio + "\n\n";
    md += "## Selected hook\n" + c.modules.selected_hook + "\n\n";
    md += "## Script\n";
    c.modules.sales_script.forEach(function (p) { md += "**" + p.part + "**: " + p.text + "\n\n"; });
    md += "## Storyboard\n";
    c.modules.storyboard.forEach(function (s) { md += "- " + timeLabel(s) + " — **" + s.label + "** — " + s.desc + "\n"; });
    md += "\n## Beat map\n" + c.music.intro + " intro → " + c.music.drop + " drop at " + c.music.transition_second + "s\n\n";
    md += "## Ad creatives\n";
    c.modules.ad_creatives.forEach(function (ad, i) { md += (i + 1) + ". (" + ad.audience + ") " + ad.hook + "\n"; });
    return md;
  }

  // ---------------------------------------------------------------
  // Wiring
  // ---------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", function () {
    renderSuites();
    renderStepper();

    document.getElementById("f-image").addEventListener("change", function (e) {
      var file = e.target.files[0];
      if (!file) return;
      var reader = new FileReader();
      reader.onload = function () {
        state.imageDataUrl = reader.result;
        var preview = document.getElementById("image-preview");
        preview.hidden = false;
        document.getElementById("image-preview-img").src = reader.result;
      };
      reader.readAsDataURL(file);
    });

    document.getElementById("btn-to-2").addEventListener("click", function () {
      state.brief = readBrief();
      state.hooks = generateHooks(state.brief);
      state.selectedHook = null;
      renderHooks();
      document.getElementById("btn-to-3").disabled = true;
      goToStep(2);
    });

    document.getElementById("btn-regen-hooks").addEventListener("click", function () {
      state.hooks = generateHooks(state.brief);
      state.selectedHook = null;
      renderHooks();
      document.getElementById("btn-to-3").disabled = true;
    });

    document.getElementById("btn-back-1").addEventListener("click", function () { goToStep(1); });

    document.getElementById("btn-to-3").addEventListener("click", function () {
      state.script = generateScript(state.brief, state.selectedHook);
      renderScript();
      goToStep(3);
    });

    document.getElementById("btn-back-2").addEventListener("click", function () { goToStep(2); });

    document.getElementById("btn-to-4").addEventListener("click", function () {
      state.storyboard = generateStoryboard(state.brief.duration, state.brief);
      renderStoryboard();
      goToStep(4);
    });

    document.getElementById("btn-back-3").addEventListener("click", function () { goToStep(3); });

    document.getElementById("btn-to-5").addEventListener("click", function () {
      recomputeBeatMap();
      goToStep(5);
    });

    ["f-genre-intro", "f-genre-drop", "f-transition-pct"].forEach(function (id) {
      document.getElementById(id).addEventListener("input", recomputeBeatMap);
    });

    document.getElementById("btn-back-4").addEventListener("click", function () { goToStep(4); });

    document.getElementById("btn-to-6").addEventListener("click", function () {
      state.ads = generateAds(state.brief);
      renderAds();
      goToStep(6);
    });

    document.getElementById("btn-back-5").addEventListener("click", function () { goToStep(5); });

    document.getElementById("btn-to-export").addEventListener("click", function () {
      renderExport();
      goToStep(7);
    });

    document.getElementById("btn-back-6").addEventListener("click", function () { goToStep(6); });

    document.getElementById("btn-save-local").addEventListener("click", function () {
      try {
        var saved = JSON.parse(localStorage.getItem("creator-empire-projects") || "[]");
        saved.push(buildCampaignObject());
        localStorage.setItem("creator-empire-projects", JSON.stringify(saved));
        alert("Saved to this browser (" + saved.length + " project(s) total). Nothing left this device.");
      } catch (err) {
        alert("Could not save locally: " + err.message);
      }
    });

    document.getElementById("btn-export-json").addEventListener("click", function () {
      download("campaign.json", JSON.stringify(buildCampaignObject(), null, 2), "application/json");
    });

    document.getElementById("btn-export-md").addEventListener("click", function () {
      download("campaign-brief.md", campaignToMarkdown(buildCampaignObject()), "text/markdown");
    });
  });

  // Exposed for the real (non-DOM) test suite.
  window.__CreatorEmpire = {
    SUITES: SUITES,
    generateHooks: generateHooks,
    generateScript: generateScript,
    generateStoryboard: generateStoryboard,
    generateBeatMap: generateBeatMap,
    generateAds: generateAds,
    timeLabel: timeLabel,
    campaignToMarkdown: campaignToMarkdown,
  };
})();
