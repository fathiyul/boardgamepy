"""Load DixiQuote situation cards from markdown file."""

import re
from pathlib import Path


def load_situations(file_path: str | None = None) -> list[str]:
    """
    Load situation cards from the markdown file.

    Args:
        file_path: Path to the situation deck markdown file.
                   If None, uses the default file in the same directory.

    Returns:
        List of situation strings.
    """
    if file_path is None:
        file_path = str(Path(__file__).parent / "dixiquote_situation_deck_revised_80_cards.md")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract numbered situations using regex
    # Pattern: number followed by a period, then the situation text
    pattern = r"^\d+\.\s+(.+)$"
    situations = []

    for line in content.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            situations.append(match.group(1).strip())

    return situations


if __name__ == "__main__":
    # Test loading
    situations = load_situations()
    print(f"Loaded {len(situations)} situations")
    print("\nFirst 3 situations:")
    for i, sit in enumerate(situations[:3], 1):
        print(f"{i}. {sit}")
