from pathlib import Path
import subprocess
import tomllib


def test_public_readme_sets_legal_and_safety_boundaries() -> None:
    readme = Path(__file__).parents[2] / "README.md"
    text = readme.read_text(encoding="utf-8")
    assert "# Ezra Plays Pokémon" in text
    assert "legally obtained" in text
    assert "does not include ROMs or save files" in text
    assert "FireRed" in text
    assert "local" in text.lower()
    for heading in (
        "## What it is",
        "## Status",
        "## Legal and safety boundary",
        "## Current capability",
        "## Roadmap",
        "## Quick start for developers",
        "## Contributing",
    ):
        assert heading in text


def test_public_project_metadata_and_bug_form_are_complete() -> None:
    root = Path(__file__).parents[2]
    metadata = tomllib.loads((root / "farm-toolbox" / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    assert project["description"] == "Local, safety-first Pokémon automation foundations"
    assert project["readme"] == "README.md"
    assert project["license"] == {"text": "MIT"}

    issue_form = (root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text(encoding="utf-8")
    for field in (
        "toolbox_version",
        "operating_system",
        "python_version",
        "pokebot_emulator_version",
        "sanitized_logs",
        "expected_behavior",
        "actual_behavior",
        "no_game_assets",
        "no ROM, save, state, or copyrighted screenshot is attached",
    ):
        assert field in issue_form


def test_game_asset_ignore_rules_cover_roms_and_preserve_bridge_source() -> None:
    root = Path(__file__).parents[2]
    ignore_rules = (root / ".gitignore").read_text(encoding="utf-8")
    for rule in (
        ".env",
        "*.gba",
        "*.gbc",
        "*.gb",
        "*.sav",
        "*.ss1",
        "*.state",
        "*.log",
        "farm-toolbox/integrations/pokebot/__pycache__/",
        "farm-toolbox/.coverage",
    ):
        assert rule in ignore_rules.splitlines()

    for candidate in (
        "arbitrary/legal-copy.gba",
        "arbitrary/legal-copy.gbc",
        "arbitrary/legal-copy.gb",
    ):
        result = subprocess.run(
            ["git", "check-ignore", "-q", "--", candidate],
            cwd=root,
            check=False,
        )
        assert result.returncode == 0

    bridge = subprocess.run(
        ["git", "check-ignore", "-q", "--", "farm-toolbox/integrations/pokebot/ezra_bridge.py"],
        cwd=root,
        check=False,
    )
    assert bridge.returncode == 1
