"""Generate and push updated HTML for the ouroboros project page."""
import asyncio
import logging
import re
from pathlib import Path

from .vitals import collect_all

logger = logging.getLogger("ouroboros")

SITE_REPO = Path.home() / "experiments" / "fr0do.github.io"
OUROBOROS_PAGE = SITE_REPO / "ouroboros" / "index.html"
LANDING_PAGE = SITE_REPO / "index.html"


async def _git(
    *args: str, cwd: str | None = None, timeout: int = 30,
) -> tuple[int, str]:
    """Run a git subprocess, return (returncode, stdout). Never raises."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or str(SITE_REPO),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        out = stdout.decode(errors="replace").strip()
        if proc.returncode != 0:
            err = stderr.decode(errors="replace").strip()
            logger.warning("git %s failed (rc=%d): %s", " ".join(args), proc.returncode, err)
        return proc.returncode, out
    except asyncio.TimeoutError:
        try:
            proc.kill()  # type: ignore[possibly-undefined]
        except Exception:
            pass
        return -1, ""
    except Exception as exc:
        logger.debug("page._git failed: %s", exc)
        return -1, ""


def _build_vitals_html(data: dict) -> str:
    """Build the HTML block that goes between VITALS:START and VITALS:END."""
    git = data.get("git", {})
    cb = data.get("codebase", {})
    gh = data.get("github", {})

    commits = git.get("total_commits", 0)
    loc = cb.get("total_loc", 0)
    files = cb.get("total_files", 0)
    handlers = cb.get("handlers", 0)
    services = cb.get("services", 0)
    open_issues = gh.get("open_issues", 0)
    closed_issues = gh.get("closed_issues", 0)
    version = gh.get("latest_release") or "—"

    return (
        '    <div class="metrics-grid" id="vitals">\n'
        '      <div class="metric-card">\n'
        f'        <div class="value" id="v-commits">{commits}</div>\n'
        '        <div class="metric-label">Commits (30d)</div>\n'
        '      </div>\n'
        '      <div class="metric-card">\n'
        f'        <div class="value" id="v-loc">{loc}</div>\n'
        '        <div class="metric-label">Lines of Code</div>\n'
        '      </div>\n'
        '      <div class="metric-card">\n'
        f'        <div class="value" id="v-files">{files}</div>\n'
        '        <div class="metric-label">Python Files</div>\n'
        '      </div>\n'
        '      <div class="metric-card">\n'
        f'        <div class="value" id="v-handlers">{handlers}</div>\n'
        '        <div class="metric-label">Bot Handlers</div>\n'
        '      </div>\n'
        '      <div class="metric-card">\n'
        f'        <div class="value" id="v-services">{services}</div>\n'
        '        <div class="metric-label">Services</div>\n'
        '      </div>\n'
        '      <div class="metric-card">\n'
        f'        <div class="value" id="v-issues-open">{open_issues}</div>\n'
        '        <div class="metric-label">Open Issues</div>\n'
        '      </div>\n'
        '      <div class="metric-card">\n'
        f'        <div class="value" id="v-issues-closed">{closed_issues}</div>\n'
        '        <div class="metric-label">Closed Issues</div>\n'
        '      </div>\n'
        '      <div class="metric-card">\n'
        f'        <div class="value" id="v-version">{version}</div>\n'
        '        <div class="metric-label">Version</div>\n'
        '      </div>\n'
        '    </div>'
    )


def _update_ouroboros_page(html: str, data: dict) -> str:
    """Replace content between VITALS:START and VITALS:END markers."""
    vitals_block = _build_vitals_html(data)
    pattern = r"(<!-- VITALS:START[^>]*-->)\n.*?\n(    <!-- VITALS:END -->)"
    replacement = rf"\1\n{vitals_block}\n\2"
    updated = re.sub(pattern, replacement, html, flags=re.DOTALL)
    return updated


def _update_landing_page(html: str, data: dict) -> str:
    """Update stat divs (stat-commits, stat-loc, stat-issues) on the landing page."""
    git = data.get("git", {})
    cb = data.get("codebase", {})
    gh = data.get("github", {})

    commits = git.get("total_commits", 0)
    loc = cb.get("total_loc", 0)
    closed_issues = gh.get("closed_issues", 0)

    # Replace content of <div class="number" id="stat-commits">...</div>
    html = re.sub(
        r'(<div class="number" id="stat-commits">).*?(</div>)',
        rf"\g<1>{commits}\2",
        html,
    )
    html = re.sub(
        r'(<div class="number" id="stat-loc">).*?(</div>)',
        rf"\g<1>{loc}\2",
        html,
    )
    html = re.sub(
        r'(<div class="number" id="stat-issues">).*?(</div>)',
        rf"\g<1>{closed_issues}\2",
        html,
    )
    return html


async def update_page() -> str:
    """Collect vitals, update HTML files, commit and push. Returns summary."""
    data = await collect_all()
    updated_files: list[str] = []

    # Update ouroboros/index.html
    if OUROBOROS_PAGE.is_file():
        original = OUROBOROS_PAGE.read_text()
        updated = _update_ouroboros_page(original, data)
        if updated != original:
            OUROBOROS_PAGE.write_text(updated)
            updated_files.append("ouroboros/index.html")
    else:
        logger.warning("Ouroboros page not found: %s", OUROBOROS_PAGE)

    # Update landing page index.html
    if LANDING_PAGE.is_file():
        original = LANDING_PAGE.read_text()
        updated = _update_landing_page(original, data)
        if updated != original:
            LANDING_PAGE.write_text(updated)
            updated_files.append("index.html")
    else:
        logger.warning("Landing page not found: %s", LANDING_PAGE)

    if not updated_files:
        return "No changes — pages already up to date."

    # Git add, commit, push
    for f in updated_files:
        await _git("add", f)

    git = data.get("git", {})
    cb = data.get("codebase", {})
    gh = data.get("github", {})
    msg = (
        f"vitals: {git.get('total_commits', '?')} commits, "
        f"{cb.get('total_loc', '?')} LOC, "
        f"{gh.get('open_issues', '?')} open issues"
    )
    rc, _ = await _git("commit", "-m", msg)
    if rc != 0:
        return f"Updated {', '.join(updated_files)} but commit failed."

    rc, out = await _git("push", timeout=60)
    if rc != 0:
        return f"Committed {', '.join(updated_files)} but push failed."

    return f"Updated {', '.join(updated_files)} — pushed.\n{msg}"
