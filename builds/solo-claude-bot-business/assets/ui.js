"use strict";
// DOM wiring only -- all real logic lives in app.js and is tested
// there directly with no DOM involved. This file just renders state
// and handles events.
(function () {
  const fmtMoney = (n) => "$" + Math.round(n).toLocaleString("en-US");
  const fmtRate = (n) => "$" + n.toFixed(2);

  let state = window.SCBB.loadState(window.localStorage);

  function persist() {
    window.SCBB.saveState(window.localStorage, state);
  }

  // ---------------- Offer Calculator ----------------
  function renderOffer() {
    const o = state.offer;
    document.getElementById("niche-baseline").value = o.nicheBaseline;
    document.getElementById("multiplier").value = o.multiplier;
    document.getElementById("multiplier-value").textContent = o.multiplier + "x";
    document.getElementById("upfront-ratio").value = o.upfrontRatio;
    document.getElementById("hours-per-month").value = o.hoursPerMonth;

    try {
      const result = window.SCBB.computeOffer(o);
      document.getElementById("result-monthly").textContent = fmtMoney(result.recommendedMonthly);
      document.getElementById("result-upfront").textContent = fmtMoney(result.suggestedUpfront);
      document.getElementById("result-hourly").textContent = fmtRate(result.effectiveHourlyRate);
      document.getElementById("result-hourly-basis").textContent =
        "based on " + o.hoursPerMonth + " hours/month -- change this and the rate updates";
      document.getElementById("result-first-year").textContent = fmtMoney(result.firstYearValue);
      document.getElementById("offer-error").textContent = "";
    } catch (e) {
      document.getElementById("offer-error").textContent = e.message;
    }
  }

  function wireOffer() {
    ["niche-baseline", "multiplier", "upfront-ratio", "hours-per-month"].forEach((id) => {
      document.getElementById(id).addEventListener("input", (ev) => {
        const key = { "niche-baseline": "nicheBaseline", multiplier: "multiplier", "upfront-ratio": "upfrontRatio", "hours-per-month": "hoursPerMonth" }[id];
        state.offer[key] = Number(ev.target.value);
        persist();
        renderOffer();
      });
    });
  }

  // ---------------- Client Pipeline ----------------
  function renderPipeline() {
    const summary = window.SCBB.pipelineSummary(state.contacts);
    document.getElementById("call-goal-progress").textContent =
      summary.calledOrFurther + " / " + window.SCBB.CALL_GOAL + " contacted";
    document.getElementById("call-goal-bar").style.width = Math.round(summary.callGoalProgress * 100) + "%";
    document.getElementById("case-studies-started").textContent = summary.caseStudiesStarted;
    document.getElementById("total-referrals").textContent =
      summary.totalReferrals + " / " + summary.referralGoal;

    const list = document.getElementById("contact-list");
    list.innerHTML = "";
    state.contacts.forEach((c) => {
      const row = document.createElement("div");
      row.className = "contact-row";
      row.setAttribute("data-id", c.id);
      const statusOptions = window.SCBB.CONTACT_STATUSES.map(
        (s) => `<option value="${s}" ${s === c.status ? "selected" : ""}>${s}</option>`
      ).join("");
      row.innerHTML = `
        <span class="contact-name">${c.name}</span>
        <select class="contact-status">${statusOptions}</select>
        <input type="number" class="contact-referrals" min="0" value="${c.referrals}" title="referrals from this contact">
        <button class="contact-remove" title="remove">&times;</button>
      `;
      list.appendChild(row);

      row.querySelector(".contact-status").addEventListener("change", (ev) => {
        c.status = ev.target.value;
        persist();
        renderPipeline();
      });
      row.querySelector(".contact-referrals").addEventListener("input", (ev) => {
        c.referrals = Math.max(0, Number(ev.target.value) || 0);
        persist();
        renderPipeline();
      });
      row.querySelector(".contact-remove").addEventListener("click", () => {
        state.contacts = state.contacts.filter((x) => x.id !== c.id);
        persist();
        renderPipeline();
      });
    });
  }

  function wirePipeline() {
    document.getElementById("add-contact-form").addEventListener("submit", (ev) => {
      ev.preventDefault();
      const input = document.getElementById("new-contact-name");
      const name = input.value.trim();
      const errEl = document.getElementById("contact-error");
      if (!name) {
        errEl.textContent = "Enter a name first.";
        return;
      }
      try {
        state.contacts.push(window.SCBB.makeContact({ name }));
        input.value = "";
        errEl.textContent = "";
        persist();
        renderPipeline();
      } catch (e) {
        errEl.textContent = e.message;
      }
    });
  }

  // ---------------- Build Stack Checklist ----------------
  function renderChecklist() {
    const cl = state.checklist;
    document.getElementById("research-done").checked = cl.researchDone;
    document.getElementById("research-notes").value = cl.researchNotes;
    document.getElementById("design-done").checked = cl.designDone;
    document.getElementById("design-tool").value = cl.designTool;
    window.SCBB.STACK_CATEGORIES.forEach((cat) => {
      document.getElementById("stack-" + cat + "-tool").value = cl.stack[cat].tool;
      document.getElementById("stack-" + cat + "-docs").checked = cl.stack[cat].docsRead;
    });
    document.getElementById("build-done").checked = cl.buildDone;

    const progress = window.SCBB.checklistProgress(cl);
    document.getElementById("checklist-progress").textContent =
      progress.completedSteps + " / " + progress.totalSteps + " steps complete (" +
      progress.stackDone + "/" + progress.stackTotal + " stack tools set up)";
    document.getElementById("checklist-bar").style.width =
      Math.round((progress.completedSteps / progress.totalSteps) * 100) + "%";
  }

  function wireChecklist() {
    document.getElementById("research-done").addEventListener("change", (ev) => {
      state.checklist.researchDone = ev.target.checked;
      persist();
      renderChecklist();
    });
    document.getElementById("research-notes").addEventListener("input", (ev) => {
      state.checklist.researchNotes = ev.target.value;
      persist();
    });
    document.getElementById("design-done").addEventListener("change", (ev) => {
      state.checklist.designDone = ev.target.checked;
      persist();
      renderChecklist();
    });
    document.getElementById("design-tool").addEventListener("input", (ev) => {
      state.checklist.designTool = ev.target.value;
      persist();
    });
    window.SCBB.STACK_CATEGORIES.forEach((cat) => {
      document.getElementById("stack-" + cat + "-tool").addEventListener("input", (ev) => {
        state.checklist.stack[cat].tool = ev.target.value;
        persist();
        renderChecklist();
      });
      document.getElementById("stack-" + cat + "-docs").addEventListener("change", (ev) => {
        state.checklist.stack[cat].docsRead = ev.target.checked;
        persist();
        renderChecklist();
      });
    });
    document.getElementById("build-done").addEventListener("change", (ev) => {
      state.checklist.buildDone = ev.target.checked;
      persist();
      renderChecklist();
    });
  }

  function renderAll() {
    renderOffer();
    renderPipeline();
    renderChecklist();
  }

  document.addEventListener("DOMContentLoaded", () => {
    wireOffer();
    wirePipeline();
    wireChecklist();
    renderAll();
  });
})();
