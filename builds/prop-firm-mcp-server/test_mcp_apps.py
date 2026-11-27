"""Real end-to-end test for this server's MCP Apps extension support
(SEP-1865, `_meta.ui.resourceUri`/`visibility`) -- spawns the server as a
real subprocess over stdio and drives it with a genuine
`mcp.ClientSession`, same convention as test_client.py and
test_http_client.py.

What this proves, and the one thing it deliberately doesn't:
  - The SERVER's half of the contract: the right tool carries the right
    `_meta.ui` metadata, the ui:// resource exists with the exact
    required MIME type and real HTML content, and the app-only tool is
    genuinely callable even though it's absent from the model's list.
  - NOT the HOST's half: no live MCP-Apps-compatible host (Claude.ai,
    ChatGPT, VS Code) exists in this sandbox to render the resource in a
    sandboxed iframe or deliver postMessage traffic for real. The two
    MUST rules the real spec assigns to hosts (filter tools/list by
    visibility; reject tools/call from an "app" caller for a tool
    lacking "app" in its visibility) are enforced here by
    `host_shim.py` -- a minimal, faithful stand-in built and tested
    specifically because probing the real `mcp` SDK first showed it
    does NOT enforce either rule itself.

Run with:
    python3.13 test_mcp_apps.py
"""
from __future__ import annotations

import asyncio
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from prop_firm_mcp_server.host_shim import HostRejection, call_tool_as, filter_tools_for_model
from prop_firm_mcp_server.ui_resources import COMPARE_SIZES_DASHBOARD_URI

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


def _text(result) -> str:
    return "".join(c.text for c in result.content if hasattr(c, "text"))


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "prop_firm_mcp_server.server"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            raw = (await session.list_tools()).tools
            by_name = {t.name: t for t in raw}

            # ── §5.1 Resource Discovery: _meta.ui.resourceUri on the tool ──
            print("=== tool/resource metadata ===")
            cmp_tool = by_name.get("prop_firm_compare_sizes")
            check("prop_firm_compare_sizes registered", cmp_tool is not None)
            cmp_meta = (cmp_tool.meta or {}) if cmp_tool else {}
            check(
                "compare_sizes links to the real ui:// resource via _meta.ui.resourceUri",
                cmp_meta.get("ui", {}).get("resourceUri") == COMPARE_SIZES_DASHBOARD_URI,
                detail=str(cmp_meta),
            )
            check(
                "compare_sizes visibility defaults/declares ['model', 'app']",
                cmp_meta.get("ui", {}).get("visibility") == ["model", "app"],
                detail=str(cmp_meta),
            )

            refresh_tool = by_name.get("prop_firm_refresh_compare_sizes")
            check("prop_firm_refresh_compare_sizes registered on the raw server", refresh_tool is not None)
            refresh_meta = (refresh_tool.meta or {}) if refresh_tool else {}
            check(
                "refresh tool is declared app-only (visibility: ['app'])",
                refresh_meta.get("ui", {}).get("visibility") == ["app"],
                detail=str(refresh_meta),
            )

            # ── Host-side enforcement (host_shim.py) ──────────────────
            print("\n=== host-side visibility enforcement ===")
            model_visible = filter_tools_for_model(raw)
            model_names = {t.name for t in model_visible}
            check(
                "model-visible tool list excludes the app-only refresh tool",
                "prop_firm_refresh_compare_sizes" not in model_names,
                detail=str(model_names),
            )
            check(
                "model-visible tool list still includes all four original + compare_sizes",
                model_names
                == {
                    "prop_firm_size_check",
                    "prop_firm_session_report",
                    "prop_firm_pass_probability",
                    "prop_firm_compare_sizes",
                },
                detail=str(model_names),
            )

            # The spec's second MUST: a model-attributed call to an
            # app-only tool must be REJECTED by the host, even though
            # the raw mcp.ClientSession.call_tool() would happily run it
            # (confirmed directly against the installed SDK before
            # writing this shim).
            compare_args_model = {
                "tier": "50K",
                "symbol": "ES",
                "current_balance": 51_200.0,
                "high_water_mark": 51_500.0,
                "days_remaining": 10,
                "scenarios": [
                    {"contracts": 1, "avg_daily_pnl": 150.0, "daily_pnl_std": 300.0},
                    {"contracts": 2, "avg_daily_pnl": 300.0, "daily_pnl_std": 600.0},
                ],
            }
            # Every tool here takes one positional `args` wrapping the
            # whole Pydantic model, per this server's own established
            # convention (confirmed against test_client.py).
            compare_args = {"args": compare_args_model}

            rejected = False
            try:
                await call_tool_as(session, raw, "model", "prop_firm_refresh_compare_sizes", compare_args)
            except HostRejection:
                rejected = True
            check("host rejects a model-attributed call to the app-only tool", rejected)

            # And the same tool genuinely works for an "app" caller --
            # proving the rejection above is about the caller's role,
            # not a broken tool.
            app_result = await call_tool_as(session, raw, "app", "prop_firm_refresh_compare_sizes", compare_args)
            check("app-attributed call to the same app-only tool succeeds", not app_result.is_error)

            # And a normal, model-visible tool is callable by a
            # model-attributed caller with no rejection.
            normal_result = await call_tool_as(session, raw, "model", "prop_firm_compare_sizes", compare_args)
            check("model-attributed call to the visible compare_sizes tool succeeds", not normal_result.is_error)

            # ── §4 Content Requirements: the ui:// resource itself ────
            print("\n=== ui:// resource content ===")
            resource_result = await session.read_resource(COMPARE_SIZES_DASHBOARD_URI)
            contents = resource_result.contents
            check("exactly one content block returned", len(contents) == 1, detail=str(len(contents)))
            block = contents[0]
            check(
                "MIME type is exactly 'text/html;profile=mcp-app' (spec §Content Requirements)",
                block.mime_type == "text/html;profile=mcp-app",
                detail=str(getattr(block, "mime_type", None)),
            )
            html = block.text
            check("content is a real HTML5 document", html.strip().startswith("<!DOCTYPE html>"))
            check(
                "content wires the two-way contract (receives postMessage, calls back via callServerTool)",
                "addEventListener(\"message\"" in html and "callServerTool" in html,
            )
            check(
                "the App's own callback names the real app-only tool, not a placeholder",
                "prop_firm_refresh_compare_sizes" in html,
            )

            # resources/list is allowed (not required) to omit a
            # tool-discovered UI resource per spec; check the server's
            # actual current behavior rather than assume either way.
            listed = (await session.list_resources()).resources
            listed_uris = {r.uri for r in listed}
            is_listed = str(COMPARE_SIZES_DASHBOARD_URI) in {str(u) for u in listed_uris}
            print(
                f"  [INFO] resources/list {'includes' if is_listed else 'omits'} the UI resource "
                f"(spec permits either; this server's actual behavior is informational, not a pass/fail check)"
            )

            # ── Numeric cross-check: the app-only tool's real output ──
            # matches a direct call to the same already-proven
            # run_compare_sizes(), same discipline as test_client.py's
            # own comparisons against the underlying functions/classes.
            print("\n=== numeric cross-check ===")
            import json

            from prop_firm_mcp_server.tools import CompareSizesInput, run_compare_sizes

            direct = run_compare_sizes(CompareSizesInput(**compare_args_model))
            via_app = json.loads(_text(app_result))
            check(
                "app-only tool's full comparison matches a direct run_compare_sizes() call exactly",
                via_app["comparison"] == direct["comparison"],
                detail=f"direct={direct['comparison']} via_app={via_app['comparison']}",
            )

    print(f"\n{'ALL PASSED' if not FAILURES else f'{len(FAILURES)} FAILURE(S): ' + ', '.join(FAILURES)}")
    if FAILURES:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
