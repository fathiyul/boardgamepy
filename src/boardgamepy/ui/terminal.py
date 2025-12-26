"""Terminal rendering utilities (ANSI colors, etc.)."""

# ANSI escape codes for terminal styling
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Foreground colors
FG_BLACK = "\033[30m"
FG_RED = "\033[31m"
FG_GREEN = "\033[32m"
FG_YELLOW = "\033[33m"
FG_BLUE = "\033[34m"
FG_MAGENTA = "\033[35m"
FG_CYAN = "\033[36m"
FG_WHITE = "\033[97m"

# Bright foreground colors
FG_BRIGHT_RED = "\033[91m"
FG_BRIGHT_GREEN = "\033[92m"
FG_BRIGHT_YELLOW = "\033[93m"
FG_BRIGHT_BLUE = "\033[94m"
FG_BRIGHT_MAGENTA = "\033[95m"
FG_BRIGHT_CYAN = "\033[96m"
FG_BRIGHT_WHITE = "\033[97m"

# Background colors
BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_GRAY = "\033[100m"  # bright black background


def clear() -> None:
    """Clear screen and move cursor to home."""
    print("\033[2J\033[H", end="")


def render_header(title: str, width: int = 86) -> None:
    """
    Render a retro-style header bar.

    Args:
        title: Title text to display
        width: Total width of header
    """
    border_color = FG_BRIGHT_MAGENTA
    title_color = FG_BRIGHT_CYAN

    print(f"{border_color}╔{'═' * (width - 2)}╗{RESET}")
    inner = title.center(width - 2)
    print(
        f"{border_color}║{RESET}{BOLD}{title_color}{inner}{RESET}{border_color}║{RESET}"
    )
    print(f"{border_color}╚{'═' * (width - 2)}╝{RESET}")


def colorize(text: str, fg: str | None = None, bg: str | None = None, bold: bool = False) -> str:
    """
    Apply ANSI color codes to text.

    Args:
        text: Text to colorize
        fg: Foreground color code
        bg: Background color code
        bold: Whether to make text bold

    Returns:
        Colorized text with ANSI codes
    """
    codes = []
    if bold:
        codes.append(BOLD)
    if fg:
        codes.append(fg)
    if bg:
        codes.append(bg)

    if codes:
        return "".join(codes) + text + RESET
    return text
