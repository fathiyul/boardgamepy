"""Load codenames word list."""

import os

def load_codenames() -> list[str]:
    """Load codenames from file or use fallback list."""
    codenames = []

    # Try to load from file
    try:
        codenames_file = os.path.join(os.path.dirname(__file__), "codenames.txt")
        with open(codenames_file, "r") as f:
            for line in f:
                word = line.strip()
                if word:
                    codenames.append(word)
    except FileNotFoundError:
        pass

    # Fallback list if file not found
    if not codenames:
        codenames = [
            "Ace", "Bar", "Berry", "Bow", "Cap",
            "Chair", "Circle", "Conductor", "Cross", "Dinosaur",
            "Eagle", "Europe", "Extension", "Face", "Fire",
            "Gas", "Grain", "Hammer", "Horn", "Ice",
            "Jack", "Kangaroo", "Lab", "Letter", "Machine",
            "Message", "Motor", "Nail", "Oil", "Pad",
            "Patch", "Pie", "Plot", "Press", "Quartz",
            "Rabbit", "Ring", "Saddle", "Scroll", "Sign",
            "Snake", "Spring", "Stream", "Table", "Temple",
            "Toast", "Triangle", "Umbrella", "Vacuum", "Voice",
            "Wall", "Wind", "Xray", "Yoghurt", "Zebra",
        ]

    return codenames
