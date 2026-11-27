"""MCP Apps UI resources for this server, per the real Agent Plugins...
no — per the real **MCP Apps** extension spec (SEP-1865,
`modelcontextprotocol/ext-apps`, `specification/2026-01-26/apps.mdx`),
read directly from the cloned spec repo rather than guessed from a
secondary article:

  - UI resources use the `ui://` URI scheme and the
    `text/html;profile=mcp-app` MIME type (§ Content Requirements).
  - A tool links to its UI resource via `_meta.ui.resourceUri`, and
    controls who may call it via `_meta.ui.visibility` (§ Resource
    Discovery) — `["model", "app"]` (the default) lets both the agent
    and the running App call the tool; `["app"]` hides it from the
    model's tool list entirely while leaving it callable from inside
    the App view.

This module holds the one UI resource this server ships: a small,
self-contained dashboard for `prop_firm_compare_sizes`'s output. It
implements the spec's two-way contract in real markup/JS --
`window.addEventListener("message", ...)` to receive the host-delivered
tool result, and a `callServerTool` helper that posts a `tools/call`
request back to the host -- even though this sandbox has no live
MCP-Apps-compatible host (Claude.ai, ChatGPT, VS Code) to actually render
it in. What's verified here, and only here, is the SERVER's half of the
contract: the resource exists at the right URI, with the right MIME
type, as valid HTML5, wired to call the right tool names. The HOST's
half (sandboxed iframe, CSP construction, postMessage delivery) is the
spec's job to define and a real host's job to implement -- this server
cannot test that side from inside this sandbox, and does not claim to.
"""

from __future__ import annotations

COMPARE_SIZES_DASHBOARD_URI = "ui://prop-firm-mcp-server/compare-sizes-dashboard"

COMPARE_SIZES_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Compare Sizes</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 0; padding: 16px; background: #111316; color: #E8EAED; }
  h1 { font-size: 16px; margin: 0 0 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #343A42; }
  th { color: #9AA2AC; font-weight: 600; }
  button { margin-top: 12px; padding: 6px 12px; background: #24282E; color: #E8EAED; border: 1px solid #343A42; border-radius: 4px; cursor: pointer; }
  #empty { color: #9AA2AC; font-size: 13px; }
</style>
</head>
<body>
  <h1>Pass-probability comparison across contract sizes</h1>
  <div id="empty">Waiting for data from the host&hellip;</div>
  <table id="table" style="display:none">
    <thead><tr><th>Contracts</th><th>Pass probability</th></tr></thead>
    <tbody id="rows"></tbody>
  </table>
  <button id="refresh">Refresh</button>

<script>
  // Receives the tool result the host delivers after `tools/call`
  // resolves. The real postMessage/JSON-RPC envelope shape is the
  // host's to define per the spec; this listens for the minimal
  // contract any compliant host guarantees -- a message whose payload
  // carries the tool's structured result.
  window.addEventListener("message", (event) => {
    const payload = event.data && event.data.result ? event.data.result : event.data;
    if (!payload || !payload.comparison) return;
    render(payload.comparison);
  });

  function render(scenarios) {
    document.getElementById("empty").style.display = "none";
    const table = document.getElementById("table");
    table.style.display = "";
    const rows = document.getElementById("rows");
    rows.innerHTML = "";
    for (const row of scenarios) {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${row.contracts}</td><td>${(row.pass_probability * 100).toFixed(1)}%</td>`;
      rows.appendChild(tr);
    }
  }

  // Calls back through the host rather than talking to the MCP server
  // directly -- the App never holds a server connection of its own.
  // This is the one app-only tool this server exposes
  // (`_meta.ui.visibility: ["app"]`): hidden from the model's tool
  // list, callable only from here.
  function callServerTool(name, args) {
    window.parent.postMessage({ type: "tools/call", name, arguments: args }, "*");
  }

  document.getElementById("refresh").addEventListener("click", () => {
    callServerTool("prop_firm_refresh_compare_sizes", {});
  });
</script>
</body>
</html>
"""
