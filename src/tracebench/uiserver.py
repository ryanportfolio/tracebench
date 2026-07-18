"""`tracebench ui`: serve the built dashboard plus local run data.

Stdlib-only local server (no new runtime dependencies): stages the runs
directory into a temp site next to the built UI assets and serves the lot.
The same UI build deploys unchanged to GitHub Pages; this server exists so
local runs are one command away from the same view.
"""

from __future__ import annotations

import http.server
import shutil
import tempfile
from functools import partial
from pathlib import Path

from tracebench.uidata import stage_ui_data

UI_DIST = Path(__file__).resolve().parents[2] / "ui" / "dist"


class UIServerError(RuntimeError):
    pass


def build_site(runs_dir: str | Path, site_dir: str | Path, dist_dir: Path = UI_DIST) -> Path:
    site_dir = Path(site_dir)
    if not dist_dir.is_dir() or not (dist_dir / "index.html").is_file():
        raise UIServerError(
            f"UI build not found at {dist_dir} — run: npm --prefix ui install && "
            "npm --prefix ui run build"
        )
    if site_dir.exists():
        shutil.rmtree(site_dir)
    shutil.copytree(dist_dir, site_dir)
    stage_ui_data(runs_dir, site_dir / "data")
    return site_dir


def serve(runs_dir: str | Path, port: int = 8321, dist_dir: Path = UI_DIST) -> None:
    site_dir = build_site(runs_dir, Path(tempfile.mkdtemp(prefix="tracebench-ui-")), dist_dir)
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(site_dir))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"tracebench ui: http://127.0.0.1:{port}/  (Ctrl+C to stop)")
        print(f"serving runs from {runs_dir}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
