"""Flask web dashboard with Commodore 64 aesthetic."""

import json
import logging
from typing import TYPE_CHECKING

try:
    from flask import Flask, render_template_string, jsonify
except ImportError:
    Flask = None

if TYPE_CHECKING:
    from lib.analyzer import LinkedInMessageAnalyzer

logger = logging.getLogger(__name__)

# Commodore 64 color palette
C64_COLORS = {
    'black': '#000000',
    'white': '#FFFFFF',
    'red': '#880000',
    'cyan': '#AAFFEE',
    'purple': '#CC44CC',
    'green': '#00CC55',
    'blue': '#0000AA',
    'yellow': '#EEEE77',
    'orange': '#DD8855',
    'brown': '#664400',
    'light_red': '#FF7777',
    'dark_grey': '#333333',
    'grey': '#777777',
    'light_green': '#AAFF66',
    'light_blue': '#0088FF',
    'light_grey': '#BBBBBB',
}

# The classic C64 BASIC screen colors
C64_BG = '#4040E0'  # Medium blue background
C64_BORDER = '#A0A0FF'  # Light blue border
C64_TEXT = '#A0A0FF'  # Light blue text
C64_HIGHLIGHT = '#FFFFFF'  # White for emphasis

C64_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LINKEDIN INBOX ANALYZER - C64 EDITION</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background-color: {{ c64_border }};
            font-family: 'VT323', 'Courier New', monospace;
            color: {{ c64_text }};
            min-height: 100vh;
            padding: 20px;
        }

        .screen {
            background-color: {{ c64_bg }};
            border: 4px solid {{ c64_border }};
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            min-height: calc(100vh - 40px);
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid {{ c64_text }};
            padding-bottom: 15px;
        }

        .header h1 {
            font-size: 2.5em;
            color: {{ c64_highlight }};
            text-shadow: 3px 3px 0 #000;
            letter-spacing: 3px;
        }

        .header .subtitle {
            color: {{ c64_text }};
            font-size: 1.2em;
            margin-top: 10px;
        }

        .ready-prompt {
            color: {{ c64_text }};
            margin-top: 10px;
        }

        .cursor {
            display: inline-block;
            width: 12px;
            height: 20px;
            background-color: {{ c64_text }};
            animation: blink 1s step-end infinite;
            vertical-align: middle;
        }

        @keyframes blink {
            50% { opacity: 0; }
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-box {
            background-color: rgba(0, 0, 0, 0.3);
            border: 2px solid {{ c64_text }};
            padding: 15px;
        }

        .stat-box h3 {
            color: {{ c64_highlight }};
            font-size: 1.3em;
            margin-bottom: 10px;
            border-bottom: 1px dashed {{ c64_text }};
            padding-bottom: 5px;
        }

        .stat-value {
            font-size: 2.5em;
            color: {{ c64_highlight }};
            text-align: center;
            margin: 10px 0;
        }

        .stat-label {
            text-align: center;
            color: {{ c64_text }};
        }

        .section {
            margin-bottom: 30px;
        }

        .section h2 {
            color: {{ c64_highlight }};
            font-size: 1.5em;
            margin-bottom: 15px;
            border-bottom: 2px solid {{ c64_text }};
            padding-bottom: 5px;
        }

        .bar-chart {
            margin: 10px 0;
        }

        .bar-row {
            display: flex;
            align-items: center;
            margin: 8px 0;
        }

        .bar-label {
            width: 200px;
            color: {{ c64_text }};
            font-size: 1.1em;
        }

        .bar-container {
            flex-grow: 1;
            height: 25px;
            background-color: rgba(0, 0, 0, 0.3);
            border: 1px solid {{ c64_text }};
            margin: 0 10px;
        }

        .bar-fill {
            height: 100%;
            background-color: {{ c64_text }};
            transition: width 0.5s ease;
        }

        .bar-fill.high { background-color: #FF7777; }
        .bar-fill.medium { background-color: #EEEE77; }
        .bar-fill.low { background-color: #AAFF66; }

        .bar-value {
            width: 60px;
            text-align: right;
            color: {{ c64_highlight }};
            font-size: 1.2em;
        }

        .message-list {
            max-height: 400px;
            overflow-y: auto;
            border: 2px solid {{ c64_text }};
            padding: 10px;
            background-color: rgba(0, 0, 0, 0.3);
        }

        .message-item {
            border-bottom: 1px dashed {{ c64_text }};
            padding: 10px 0;
        }

        .message-item:last-child {
            border-bottom: none;
        }

        .message-sender {
            color: {{ c64_highlight }};
            font-size: 1.2em;
        }

        .message-preview {
            color: {{ c64_text }};
            font-size: 1em;
            margin-top: 5px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .message-tags {
            margin-top: 5px;
        }

        .tag {
            display: inline-block;
            padding: 2px 8px;
            margin-right: 5px;
            font-size: 0.9em;
            border: 1px solid;
        }

        .tag-time { border-color: #FF7777; color: #FF7777; }
        .tag-fa { border-color: #EEEE77; color: #EEEE77; }
        .tag-recruiter { border-color: #AAFF66; color: #AAFF66; }
        .tag-ai { border-color: #CC44CC; color: #CC44CC; }
        .tag-sales { border-color: #DD8855; color: #DD8855; }

        .grade-display {
            text-align: center;
            font-size: 4em;
            padding: 20px;
        }

        .grade-a { color: #AAFF66; }
        .grade-b { color: #AAFFEE; }
        .grade-c { color: #EEEE77; }
        .grade-d { color: #DD8855; }
        .grade-f { color: #FF7777; }

        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 15px;
            border-top: 2px solid {{ c64_text }};
            color: {{ c64_text }};
        }

        .nav-buttons {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 20px 0;
        }

        .c64-button {
            background-color: {{ c64_bg }};
            color: {{ c64_text }};
            border: 2px solid {{ c64_text }};
            padding: 10px 25px;
            font-family: 'VT323', monospace;
            font-size: 1.2em;
            cursor: pointer;
            transition: all 0.2s;
        }

        .c64-button:hover {
            background-color: {{ c64_text }};
            color: {{ c64_bg }};
        }

        .c64-button.active {
            background-color: {{ c64_highlight }};
            color: {{ c64_bg }};
        }

        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 12px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.3);
        }

        ::-webkit-scrollbar-thumb {
            background: {{ c64_text }};
            border: 2px solid {{ c64_bg }};
        }

        .loading {
            text-align: center;
            padding: 50px;
            font-size: 1.5em;
        }

        .loading::after {
            content: '';
            animation: dots 1.5s steps(4, end) infinite;
        }

        @keyframes dots {
            0%, 20% { content: ''; }
            40% { content: '.'; }
            60% { content: '..'; }
            80%, 100% { content: '...'; }
        }
    </style>
</head>
<body>
    <div class="screen">
        <div class="header">
            <h1>**** LINKEDIN INBOX ANALYZER V2 ****</h1>
            <div class="subtitle">COMMODORE 64 BASIC V2.1</div>
            <div class="ready-prompt">READY.<span class="cursor"></span></div>
        </div>

        <div class="stats-grid">
            <div class="stat-box">
                <h3>TOTAL MESSAGES</h3>
                <div class="stat-value">{{ stats.total_messages }}</div>
                <div class="stat-label">MESSAGES ANALYZED</div>
            </div>
            <div class="stat-box">
                <h3>TIME VAMPIRES</h3>
                <div class="stat-value">{{ stats.time_requests }}</div>
                <div class="stat-label">WANTED YOUR TIME</div>
            </div>
            <div class="stat-box">
                <h3>FINANCIAL ADVISORS</h3>
                <div class="stat-value">{{ stats.financial_advisors }}</div>
                <div class="stat-label">CONCERNED ABOUT YOUR MONEY</div>
            </div>
            <div class="stat-box">
                <h3>AI SLOP DETECTED</h3>
                <div class="stat-value">{{ stats.ai_generated }}</div>
                <div class="stat-label">CHATGPT MASTERPIECES</div>
            </div>
        </div>

        <div class="section">
            <h2>AUDACITY METRICS</h2>
            <div class="bar-chart">
                <div class="bar-row">
                    <span class="bar-label">TIME REQUESTS</span>
                    <div class="bar-container">
                        <div class="bar-fill high" style="width: {{ stats.time_pct }}%"></div>
                    </div>
                    <span class="bar-value">{{ stats.time_requests }}</span>
                </div>
                <div class="bar-row">
                    <span class="bar-label">FAKE PERSONALIZATION</span>
                    <div class="bar-container">
                        <div class="bar-fill medium" style="width: {{ stats.fake_personal_pct }}%"></div>
                    </div>
                    <span class="bar-value">{{ stats.fake_personalization }}</span>
                </div>
                <div class="bar-row">
                    <span class="bar-label">RECRUITERS</span>
                    <div class="bar-container">
                        <div class="bar-fill low" style="width: {{ stats.recruiter_pct }}%"></div>
                    </div>
                    <span class="bar-value">{{ stats.recruiters }}</span>
                </div>
                <div class="bar-row">
                    <span class="bar-label">SALES PITCHES</span>
                    <div class="bar-container">
                        <div class="bar-fill medium" style="width: {{ stats.sales_pct }}%"></div>
                    </div>
                    <span class="bar-value">{{ stats.sales_pitches }}</span>
                </div>
            </div>
        </div>

        {% if stats.health_grade %}
        <div class="section">
            <h2>NETWORK HEALTH SCORE</h2>
            <div class="stat-box">
                <div class="grade-display grade-{{ stats.health_grade|lower }}">
                    {{ stats.health_grade }} ({{ stats.health_score }}/100)
                </div>
                <div class="stat-label">{{ stats.health_comment }}</div>
            </div>
        </div>
        {% endif %}

        <div class="section">
            <h2>RECENT OFFENDERS</h2>
            <div class="message-list">
                {% for msg in recent_messages %}
                <div class="message-item">
                    <div class="message-sender">> {{ msg.sender }}</div>
                    <div class="message-preview">{{ msg.preview }}</div>
                    <div class="message-tags">
                        {% for tag in msg.tags %}
                        <span class="tag tag-{{ tag|lower }}">{{ tag }}</span>
                        {% endfor %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="section">
            <h2>HOURS REQUESTED THIS MONTH</h2>
            <div class="stat-box">
                <div class="stat-value">{{ stats.hours_requested }}</div>
                <div class="stat-label">HOURS STRANGERS WANT FROM YOU</div>
            </div>
        </div>

        <div class="footer">
            <p>LOAD"LINKEDIN",8,1</p>
            <p>SEARCHING FOR LINKEDIN</p>
            <p>PRESS PLAY ON TAPE</p>
            <p>&nbsp;</p>
            <p>BUILT WITH MASS PASSIVE AGGRESSION</p>
        </div>
    </div>

    <script>
        // Add some C64 flavor
        console.log(`
**** LINKEDIN INBOX ANALYZER V2 ****
64K RAM SYSTEM  38911 BASIC BYTES FREE

READY.
        `);
    </script>
</body>
</html>
'''


def create_app(analyzer: 'LinkedInMessageAnalyzer') -> 'Flask':
    """Create Flask application with analyzer data.

    Args:
        analyzer: Initialized LinkedInMessageAnalyzer with data

    Returns:
        Configured Flask application
    """
    if Flask is None:
        raise ImportError(
            "Flask not installed. Run: pip install flask"
        )

    app = Flask(__name__)
    app.config['analyzer'] = analyzer

    @app.route('/')
    def index():
        """Render main dashboard."""
        a = app.config['analyzer']

        # Calculate stats
        total = len(a.messages)
        time_reqs = len(a.time_requests) if hasattr(a, 'time_requests') else 0
        fas = len(a.financial_advisors) if hasattr(a, 'financial_advisors') else 0
        ai_gen = len(a.ai_generated) if hasattr(a, 'ai_generated') else 0
        fake_pers = len(a.fake_personalization) if hasattr(a, 'fake_personalization') else 0
        recruiters = len(a.recruiters) if hasattr(a, 'recruiters') else 0
        sales = len(a.sales_pitches) if hasattr(a, 'sales_pitches') else 0

        # Calculate percentages (avoid div by zero)
        max_val = max(time_reqs, fake_pers, recruiters, sales, 1)

        # Get health score if available
        health_grade = None
        health_score = 0
        health_comment = ""
        try:
            from lib.health import NetworkHealthAnalyzer
            health_analyzer = NetworkHealthAnalyzer(a)
            score = health_analyzer.calculate_health_score()
            health_grade = score.grade
            health_score = score.overall_score
            health_comment = score.recommendations[0] if score.recommendations else "Your inbox awaits analysis"
        except Exception:
            pass

        # Calculate hours requested
        hours = 0
        if hasattr(a, 'calculate_audacity_metrics'):
            try:
                metrics = a.calculate_audacity_metrics()
                hours = metrics.get('total_hours_requested', 0)
            except Exception:
                pass

        stats = {
            'total_messages': total,
            'time_requests': time_reqs,
            'financial_advisors': fas,
            'ai_generated': ai_gen,
            'fake_personalization': fake_pers,
            'recruiters': recruiters,
            'sales_pitches': sales,
            'time_pct': min(100, (time_reqs / max_val) * 100) if max_val else 0,
            'fake_personal_pct': min(100, (fake_pers / max_val) * 100) if max_val else 0,
            'recruiter_pct': min(100, (recruiters / max_val) * 100) if max_val else 0,
            'sales_pct': min(100, (sales / max_val) * 100) if max_val else 0,
            'health_grade': health_grade,
            'health_score': health_score,
            'health_comment': health_comment,
            'hours_requested': f"{hours:.1f}",
        }

        # Get recent flagged messages
        recent_messages = []
        flagged = []
        if hasattr(a, 'time_requests'):
            flagged.extend([(m, ['TIME']) for m in a.time_requests[:5]])
        if hasattr(a, 'financial_advisors'):
            flagged.extend([(m, ['FA']) for m in a.financial_advisors[:3]])
        if hasattr(a, 'ai_generated'):
            flagged.extend([(m, ['AI']) for m in a.ai_generated[:3]])

        for msg, tags in flagged[:10]:
            recent_messages.append({
                'sender': msg.get('from', 'Unknown'),
                'preview': (msg.get('content', '')[:80] + '...')
                           if len(msg.get('content', '')) > 80
                           else msg.get('content', ''),
                'tags': tags,
            })

        return render_template_string(
            C64_HTML_TEMPLATE,
            stats=stats,
            recent_messages=recent_messages,
            c64_bg=C64_BG,
            c64_border=C64_BORDER,
            c64_text=C64_TEXT,
            c64_highlight=C64_HIGHLIGHT,
        )

    @app.route('/api/stats')
    def api_stats():
        """Return stats as JSON."""
        a = app.config['analyzer']

        return jsonify({
            'total_messages': len(a.messages),
            'time_requests': len(getattr(a, 'time_requests', [])),
            'financial_advisors': len(getattr(a, 'financial_advisors', [])),
            'ai_generated': len(getattr(a, 'ai_generated', [])),
            'fake_personalization': len(getattr(a, 'fake_personalization', [])),
            'recruiters': len(getattr(a, 'recruiters', [])),
            'sales_pitches': len(getattr(a, 'sales_pitches', [])),
        })

    return app


def run_dashboard(
    analyzer: 'LinkedInMessageAnalyzer',
    port: int = 6502,
    debug: bool = False,
) -> None:
    """Run the web dashboard.

    Args:
        analyzer: Initialized LinkedInMessageAnalyzer with data
        port: Port to run on (default: 8080)
        debug: Enable Flask debug mode
    """
    app = create_app(analyzer)

    print(f"""
**** LINKEDIN INBOX ANALYZER V2 ****

64K RAM SYSTEM  38911 BASIC BYTES FREE

READY.
LOAD"DASHBOARD",8,1

SEARCHING FOR DASHBOARD
LOADING
READY.

RUN

Dashboard starting at http://localhost:{port}
Press Ctrl+C to stop
""")

    app.run(host='0.0.0.0', port=port, debug=debug)
