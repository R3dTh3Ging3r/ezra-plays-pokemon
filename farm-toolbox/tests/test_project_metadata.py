from pathlib import Path


def test_public_readme_sets_legal_and_safety_boundaries() -> None:
    readme = Path(__file__).parents[2] / "README.md"
    text = readme.read_text(encoding="utf-8")
    assert "Ezra Plays PokÃƒÂ©mon" in text
    assert "legally obtained" in text
    assert "does not include ROMs or save files" in text
    assert "FireRed" in text
    assert "local" in text.lower()
