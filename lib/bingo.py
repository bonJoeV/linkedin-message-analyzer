"""LinkedIn Bingo Card Generator.

Generate bingo cards based on common LinkedIn message patterns.
Perfect for meetings, doom-scrolling sessions, or coping with your inbox.

"Just need 5 in a row to win... or lose, depending on your perspective."
"""

import random
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.analyzer import LinkedInMessageAnalyzer


# Bingo squares organized by category
BINGO_SQUARES = {
    "time_vampires": [
        "Quick 15-min call",
        "Pick your brain",
        "Coffee chat request",
        "Jump on a call",
        "Circle back",
        "Touch base",
        "Sync up",
        "30 minutes of your time",
        "At your earliest convenience",
        "Would love to connect",
    ],
    "flattery": [
        "Impressive background",
        "Your expertise",
        "Thought leader",
        "Impressive journey",
        "Your experience resonates",
        "Clearly passionate",
        "Someone of your caliber",
        "Truly inspired by",
        "Remarkable achievements",
        "Outstanding work",
    ],
    "ai_generated": [
        "Hope this finds you well",
        "Reaching out because",
        "In today's fast-paced",
        "Synergy",
        "Leverage",
        "Scalable solution",
        "Game-changer",
        "Paradigm shift",
        "Moving the needle",
        "Actionable insights",
    ],
    "sales_tactics": [
        "Quick demo",
        "Free trial",
        "No obligation",
        "Limited time offer",
        "Boost your ROI",
        "Transform your workflow",
        "Pain points",
        "Decision maker",
        "Next steps",
        "Value proposition",
    ],
    "recruiter_classics": [
        "Exciting opportunity",
        "Perfect fit",
        "Competitive compensation",
        "Growing team",
        "Can't share company name yet",
        "Stealth startup",
        "Series A/B/C funded",
        "Disruptive technology",
        "Industry leader",
        "Culture fit",
    ],
    "financial_advisors": [
        "Retirement planning",
        "Wealth management",
        "Financial future",
        "Investment strategy",
        "Tax optimization",
        "Asset allocation",
        "Portfolio review",
        "Comprehensive planning",
        "Fiduciary duty",
        "Risk assessment",
    ],
    "linkedin_lunatics": [
        "Agree?",
        "Thoughts?",
        "I'm humbled",
        "Blessed to announce",
        "Big news",
        "Excited to share",
        "After years of",
        "Unpopular opinion",
        "Hot take",
        "Rise and grind",
    ],
    "mlm_crypto": [
        "Passive income",
        "Financial freedom",
        "Be your own boss",
        "Work from anywhere",
        "Ground floor opportunity",
        "To the moon",
        "Diamond hands",
        "Web3 revolution",
        "NFT collection",
        "DM for details",
    ],
    "podcast_promo": [
        "Would love to have you on",
        "Our audience would love",
        "Share your story",
        "Quick interview",
        "Growing podcast",
        "Engaged listeners",
        "Episode about",
        "Your journey would inspire",
        "Top-rated show",
        "Apple Podcasts",
    ],
}

# Fun center square options
CENTER_SQUARES = [
    "FREE SPACE\n(You've earned it)",
    "EXISTENTIAL\nDREAD",
    "INBOX\nZERO\n(LOL)",
    "COPING\nMECHANISM",
    "WHY DO I\nHAVE LINKEDIN",
    "PREMIUM\nWASTE",
    "JUST\nSURVIVING",
]


class BingoCard:
    """A single bingo card."""

    def __init__(self, squares: list[str], center: str = "FREE SPACE"):
        """Initialize a bingo card.

        Args:
            squares: 24 squares (5x5 minus center)
            center: Center square text
        """
        if len(squares) != 24:
            raise ValueError("Bingo card needs exactly 24 squares (plus center)")
        self.squares = squares
        self.center = center
        self.marked: set[int] = {12}  # Center is always marked

    def mark(self, index: int) -> None:
        """Mark a square."""
        if 0 <= index < 25:
            self.marked.add(index)

    def check_win(self) -> list[str]:
        """Check for winning lines.

        Returns:
            List of winning line descriptions
        """
        wins = []

        # Check rows
        for row in range(5):
            start = row * 5
            if all(i in self.marked for i in range(start, start + 5)):
                wins.append(f"Row {row + 1}")

        # Check columns
        for col in range(5):
            if all(col + row * 5 in self.marked for row in range(5)):
                wins.append(f"Column {col + 1}")

        # Check diagonals
        if all(i * 6 in self.marked for i in range(5)):  # Top-left to bottom-right
            wins.append("Diagonal (\\)")
        if all((i + 1) * 4 in self.marked for i in range(5)):  # Top-right to bottom-left
            wins.append("Diagonal (/)")

        return wins

    def get_grid(self) -> list[list[str]]:
        """Get the card as a 5x5 grid."""
        grid = []
        for row in range(5):
            row_squares = []
            for col in range(5):
                idx = row * 5 + col
                if idx == 12:  # Center
                    row_squares.append(self.center)
                elif idx < 12:
                    row_squares.append(self.squares[idx])
                else:
                    row_squares.append(self.squares[idx - 1])
            grid.append(row_squares)
        return grid


class BingoGenerator:
    """Generate LinkedIn Bingo cards."""

    def __init__(self, analyzer: "LinkedInMessageAnalyzer | None" = None):
        """Initialize generator.

        Args:
            analyzer: Optional analyzer to personalize cards based on your inbox
        """
        self.analyzer = analyzer

    def generate_card(self, theme: str | None = None) -> BingoCard:
        """Generate a random bingo card.

        Args:
            theme: Optional theme to focus on (e.g., 'recruiter', 'sales')

        Returns:
            BingoCard instance
        """
        if theme and theme in BINGO_SQUARES:
            # Use theme category plus random others
            squares = list(BINGO_SQUARES[theme])
            other_categories = [k for k in BINGO_SQUARES if k != theme]
            for cat in random.sample(other_categories, min(3, len(other_categories))):
                squares.extend(random.sample(BINGO_SQUARES[cat], 5))
        else:
            # Mix from all categories
            squares = []
            for category in BINGO_SQUARES.values():
                squares.extend(random.sample(category, min(3, len(category))))

        # Shuffle and pick 24
        random.shuffle(squares)
        selected = squares[:24]

        center = random.choice(CENTER_SQUARES)

        return BingoCard(selected, center)

    def generate_html(self, card: BingoCard, title: str = "LinkedIn Bingo") -> str:
        """Generate an HTML bingo card.

        Args:
            card: BingoCard instance
            title: Card title

        Returns:
            HTML string
        """
        grid = card.get_grid()

        cells = []
        for row_idx, row in enumerate(grid):
            for col_idx, square in enumerate(row):
                idx = row_idx * 5 + col_idx
                marked_class = "marked" if idx in card.marked else ""
                center_class = "center" if idx == 12 else ""
                cells.append(
                    f'<td class="cell {marked_class} {center_class}" '
                    f'data-index="{idx}" onclick="toggleCell(this)">'
                    f'{square}</td>'
                )

        rows_html = []
        for i in range(0, 25, 5):
            rows_html.append(f'<tr>{"".join(cells[i:i+5])}</tr>')

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0077B5 0%, #004471 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        h1 {{
            color: white;
            margin-bottom: 10px;
            font-size: 2.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .subtitle {{
            color: rgba(255,255,255,0.8);
            margin-bottom: 20px;
            font-style: italic;
        }}

        .card {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}

        table {{
            border-collapse: collapse;
        }}

        .header {{
            background: #0077B5;
            color: white;
            font-weight: bold;
            font-size: 1.5rem;
            padding: 15px;
            text-align: center;
        }}

        .cell {{
            width: 120px;
            height: 100px;
            border: 2px solid #ddd;
            text-align: center;
            vertical-align: middle;
            padding: 8px;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s ease;
            background: white;
        }}

        .cell:hover {{
            background: #f0f0f0;
            transform: scale(1.02);
        }}

        .cell.marked {{
            background: linear-gradient(135deg, #00A0DC 0%, #0077B5 100%);
            color: white;
            font-weight: bold;
        }}

        .cell.center {{
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
            color: #333;
            font-weight: bold;
            font-size: 0.9rem;
        }}

        .cell.center.marked {{
            background: linear-gradient(135deg, #00A0DC 0%, #0077B5 100%);
        }}

        .controls {{
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }}

        button {{
            padding: 12px 24px;
            font-size: 1rem;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .btn-primary {{
            background: #0077B5;
            color: white;
        }}

        .btn-primary:hover {{
            background: #005885;
            transform: translateY(-2px);
        }}

        .btn-secondary {{
            background: #ddd;
            color: #333;
        }}

        .btn-secondary:hover {{
            background: #ccc;
        }}

        .win-message {{
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            z-index: 1000;
            animation: bounce 0.5s ease;
        }}

        @keyframes bounce {{
            0%, 100% {{ transform: translate(-50%, -50%) scale(1); }}
            50% {{ transform: translate(-50%, -50%) scale(1.1); }}
        }}

        .win-message h2 {{
            font-size: 2rem;
            margin-bottom: 10px;
        }}

        .win-message p {{
            font-size: 1.2rem;
            color: #555;
        }}

        .footer {{
            margin-top: 20px;
            color: rgba(255,255,255,0.7);
            font-size: 0.9rem;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .controls, .footer {{
                display: none;
            }}
            .cell {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
        }}
    </style>
</head>
<body>
    <h1>LinkedIn Bingo</h1>
    <p class="subtitle">Click squares as you spot them in your inbox!</p>

    <div class="card">
        <table>
            <tr>
                <td class="header">L</td>
                <td class="header">I</td>
                <td class="header">N</td>
                <td class="header">K</td>
                <td class="header">D</td>
            </tr>
            {''.join(rows_html)}
        </table>
    </div>

    <div class="controls">
        <button class="btn-primary" onclick="newCard()">New Card</button>
        <button class="btn-secondary" onclick="resetCard()">Reset</button>
        <button class="btn-secondary" onclick="window.print()">Print</button>
    </div>

    <div class="win-message" id="winMessage">
        <h2>BINGO!</h2>
        <p>You've experienced peak LinkedIn.</p>
        <p style="margin-top: 15px; font-size: 0.9rem;">Congratulations? Condolences?</p>
        <button class="btn-primary" style="margin-top: 20px;" onclick="closeWin()">Continue Suffering</button>
    </div>

    <p class="footer">Generated: {datetime.now().strftime('%B %d, %Y')}</p>

    <script>
        const markedCells = new Set([12]); // Center always marked

        function toggleCell(cell) {{
            const index = parseInt(cell.dataset.index);
            if (index === 12) return; // Can't unmark center

            if (markedCells.has(index)) {{
                markedCells.delete(index);
                cell.classList.remove('marked');
            }} else {{
                markedCells.add(index);
                cell.classList.add('marked');
                checkWin();
            }}
        }}

        function checkWin() {{
            // Check rows
            for (let row = 0; row < 5; row++) {{
                let hasRow = true;
                for (let col = 0; col < 5; col++) {{
                    if (!markedCells.has(row * 5 + col)) hasRow = false;
                }}
                if (hasRow) return showWin();
            }}

            // Check columns
            for (let col = 0; col < 5; col++) {{
                let hasCol = true;
                for (let row = 0; row < 5; row++) {{
                    if (!markedCells.has(row * 5 + col)) hasCol = false;
                }}
                if (hasCol) return showWin();
            }}

            // Check diagonals
            let hasDiag1 = true, hasDiag2 = true;
            for (let i = 0; i < 5; i++) {{
                if (!markedCells.has(i * 6)) hasDiag1 = false;
                if (!markedCells.has((i + 1) * 4)) hasDiag2 = false;
            }}
            if (hasDiag1 || hasDiag2) return showWin();
        }}

        function showWin() {{
            document.getElementById('winMessage').style.display = 'block';
        }}

        function closeWin() {{
            document.getElementById('winMessage').style.display = 'none';
        }}

        function resetCard() {{
            markedCells.clear();
            markedCells.add(12);
            document.querySelectorAll('.cell').forEach(cell => {{
                if (parseInt(cell.dataset.index) !== 12) {{
                    cell.classList.remove('marked');
                }}
            }});
            closeWin();
        }}

        function newCard() {{
            window.location.reload();
        }}
    </script>
</body>
</html>"""

    def generate_text(self, card: BingoCard) -> str:
        """Generate a text/ASCII bingo card.

        Args:
            card: BingoCard instance

        Returns:
            ASCII art bingo card
        """
        grid = card.get_grid()
        width = 20

        lines = []
        lines.append("=" * (width * 5 + 6))
        lines.append("|" + "|".join(f"{c:^{width}}" for c in "LINKD") + "|")
        lines.append("=" * (width * 5 + 6))

        for row in grid:
            # Wrap long text
            wrapped_rows = []
            for cell in row:
                words = cell.split()
                lines_for_cell = []
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 <= width - 2:
                        current_line += (" " if current_line else "") + word
                    else:
                        if current_line:
                            lines_for_cell.append(current_line)
                        current_line = word
                if current_line:
                    lines_for_cell.append(current_line)
                wrapped_rows.append(lines_for_cell)

            max_lines = max(len(wr) for wr in wrapped_rows)
            for i in range(max(max_lines, 3)):
                row_str = "|"
                for wr in wrapped_rows:
                    if i < len(wr):
                        row_str += f"{wr[i]:^{width}}|"
                    else:
                        row_str += " " * width + "|"
                lines.append(row_str)
            lines.append("-" * (width * 5 + 6))

        return "\n".join(lines)


def generate_bingo_card(
    output_path: str | None = None,
    theme: str | None = None,
    format: str = "html"
) -> str:
    """Convenience function to generate a bingo card.

    Args:
        output_path: Optional path to save the card
        theme: Optional theme (recruiter, sales, ai_generated, etc.)
        format: Output format ('html' or 'text')

    Returns:
        Card content as string
    """
    generator = BingoGenerator()
    card = generator.generate_card(theme)

    if format == "html":
        content = generator.generate_html(card)
    else:
        content = generator.generate_text(card)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return content
