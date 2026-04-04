from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE_NAME = "top_github_scraper"
REPO_ROOT = Path(__file__).resolve().parent.parent
HTML_ROOT = REPO_ROOT / "html"
DOCS_ROOT = HTML_ROOT / PACKAGE_NAME
TEMPLATE_ROOT = REPO_ROOT / "docs" / "pdoc_templates"
ASSET_ROOT = HTML_ROOT / "assets"
TEMP_ROOT = HTML_ROOT / ".pdoc-build"


def run_pdoc() -> None:
    cmd = [
        sys.executable,
        "-m",
        "pdoc",
        "--template-directory",
        str(TEMPLATE_ROOT),
        "--output-directory",
        str(TEMP_ROOT),
        PACKAGE_NAME,
    ]
    subprocess.run(cmd, cwd=REPO_ROOT, check=True)


def reset_output_dirs() -> None:
    shutil.rmtree(TEMP_ROOT, ignore_errors=True)
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)


def move_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def normalize_output() -> None:
    shutil.rmtree(DOCS_ROOT, ignore_errors=True)
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)

    root_candidates = [
        TEMP_ROOT / PACKAGE_NAME / "index.html",
        TEMP_ROOT / f"{PACKAGE_NAME}.html",
        TEMP_ROOT / "index.html",
    ]
    for candidate in root_candidates:
        if move_if_exists(candidate, DOCS_ROOT / "index.html"):
            break
    else:
        raise FileNotFoundError("Unable to find the generated package landing page.")

    module_names = sorted(
        path.stem for path in (REPO_ROOT / PACKAGE_NAME).glob("*.py") if path.name != "__init__.py"
    )
    for module_name in module_names:
        candidates = [
            TEMP_ROOT / PACKAGE_NAME / f"{module_name}.html",
            TEMP_ROOT / f"{PACKAGE_NAME}.{module_name}.html",
            TEMP_ROOT / f"{module_name}.html",
        ]
        for candidate in candidates:
            if move_if_exists(candidate, DOCS_ROOT / f"{module_name}.html"):
                break
        else:
            raise FileNotFoundError(f"Unable to find the generated page for module {module_name!r}.")


def write_root_redirect() -> None:
    index_path = HTML_ROOT / "index.html"
    index_path.write_text(
        """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0; url=./top_github_scraper/index.html">
    <title>top_github_scraper docs</title>
</head>
</html>
""",
        encoding="utf-8",
    )


def main() -> None:
    reset_output_dirs()
    run_pdoc()
    normalize_output()
    write_root_redirect()
    shutil.rmtree(TEMP_ROOT, ignore_errors=True)


if __name__ == "__main__":
    main()
