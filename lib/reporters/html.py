"""HTML Report Generator for LinkedIn Message Analyzer.

Generates a beautiful, shareable HTML report with:
- Interactive charts (pure SVG, no dependencies)
- Category breakdowns
- Hall of Shame for worst offenders
- Quotable stats section
"""

import html
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.analyzer import LinkedInMessageAnalyzer


class HTMLReporter:
    """Generate interactive HTML reports."""

    def __init__(self, analyzer: "LinkedInMessageAnalyzer"):
        self.analyzer = analyzer

    def generate(self, output_path: str | None = None) -> str:
        """Generate HTML report.

        Args:
            output_path: Optional path to save the report

        Returns:
            HTML string
        """
        html_content = self._build_html()

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

        return html_content

    def _build_html(self) -> str:
        """Build the complete HTML document."""
        stats = self._gather_stats()

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LinkedIn Message Analysis Report</title>
    <style>
{self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>LinkedIn Message Analysis</h1>
            <p class="subtitle">A deep dive into your inbox chaos</p>
            <p class="date">Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </header>

        <section class="summary-cards">
            <div class="card total">
                <div class="card-value">{stats['total_messages']}</div>
                <div class="card-label">Total Messages</div>
            </div>
            <div class="card requests">
                <div class="card-value">{stats['time_requests']}</div>
                <div class="card-label">Time Requests</div>
                <div class="card-subtitle">"Quick 15-min calls"</div>
            </div>
            <div class="card advisors">
                <div class="card-value">{stats['financial_advisors']}</div>
                <div class="card-label">Financial Advisors</div>
                <div class="card-subtitle">Worried about your retirement</div>
            </div>
            <div class="card recruiters">
                <div class="card-value">{stats['recruiters']}</div>
                <div class="card-label">Recruiters</div>
                <div class="card-subtitle">"Exciting opportunities"</div>
            </div>
        </section>

        <section class="chart-section">
            <h2>Message Breakdown</h2>
            <div class="chart-container">
                {self._generate_pie_chart(stats)}
            </div>
        </section>

        <section class="metrics">
            <h2>Audacity Metrics</h2>
            <div class="metric-grid">
                <div class="metric">
                    <span class="metric-value">{stats['total_time_requested']}</span>
                    <span class="metric-label">Total minutes requested</span>
                    <span class="metric-note">({stats['total_time_requested'] // 60} hours of your life)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{stats['flattery_count']}</span>
                    <span class="metric-label">Flattery attempts</span>
                    <span class="metric-note">"Your impressive background..."</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{stats['template_count']}</span>
                    <span class="metric-label">Obvious templates</span>
                    <span class="metric-note">Copy-paste detected</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{stats['ai_generated']}</span>
                    <span class="metric-label">AI-generated messages</span>
                    <span class="metric-note">"I hope this finds you well"</span>
                </div>
            </div>
        </section>

        {self._generate_llm_section(stats)}

        {self._generate_hall_of_shame(stats)}

        {self._generate_weekly_breakdown(stats)}

        <section class="quotable">
            <h2>Share-Worthy Stats</h2>
            <div class="quote-box">
                <p>In the past {stats['weeks_analyzed']} weeks, I received:</p>
                <ul>
                    <li><strong>{stats['time_requests']}</strong> requests for my time</li>
                    <li><strong>{stats['financial_advisors']}</strong> financial advisors worried about my retirement</li>
                    <li><strong>{stats['recruiters']}</strong> recruiters with "exciting opportunities"</li>
                    <li><strong>{stats['total_time_requested']} minutes</strong> of calls I didn't take</li>
                </ul>
                <p class="hashtag">#LinkedInLunatics #InboxZero #ActualData</p>
            </div>
        </section>

        <footer>
            <p>Generated by <a href="https://github.com/yourusername/linkedin-message-analyzer">LinkedIn Message Analyzer</a></p>
            <p class="disclaimer">Because your inbox deserves data-driven therapy.</p>
        </footer>
    </div>

    <script>
{self._get_js()}
    </script>
</body>
</html>"""

    def _gather_stats(self) -> dict:
        """Gather statistics from the analyzer."""
        a = self.analyzer

        # Count messages by category
        total_time = sum(
            tr.get('estimated_minutes', 15)
            for tr in getattr(a, 'time_requests', [])
        )

        # Count flattery and templates
        flattery_count = a.get_flattery_summary().get('messages_with_flattery', 0)
        template_count = len(getattr(a, 'template_messages', []))

        # AI generated count
        ai_count = len(getattr(a, 'ai_generated_messages', []))

        # Get repeat offenders
        sender_counts: dict[str, int] = {}
        for msg in getattr(a, 'messages', []):
            sender = msg.get('from', 'Unknown')
            sender_counts[sender] = sender_counts.get(sender, 0) + 1

        repeat_offenders = [
            (sender, count) for sender, count in sender_counts.items()
            if count > 2
        ]
        repeat_offenders.sort(key=lambda x: x[1], reverse=True)

        weeks_analyzed = 0
        if getattr(a, 'date_range', None):
            days = max((a.date_range[1] - a.date_range[0]).days + 1, 1)
            weeks_analyzed = max(1, (days + 6) // 7)

        return {
            'total_messages': len(getattr(a, 'messages', [])),
            'time_requests': len(getattr(a, 'time_requests', [])),
            'financial_advisors': len(getattr(a, 'financial_advisor_messages', [])),
            'recruiters': len(getattr(a, 'recruiter_messages', [])),
            'franchise_consultants': len(getattr(a, 'franchise_consultant_messages', [])),
            'expert_networks': len(getattr(a, 'expert_network_messages', [])),
            'total_time_requested': total_time,
            'flattery_count': flattery_count,
            'template_count': template_count,
            'ai_generated': ai_count,
            'weeks_analyzed': weeks_analyzed,
            'repeat_offenders': repeat_offenders[:10],
            'sales_pitches': len(a.get_high_priority_messages()) if getattr(a, 'llm_analyses', None) else 0,
            'llm': a.get_llm_run_info(),
        }

    def _generate_llm_section(self, stats: dict) -> str:
        """Generate a report section summarizing the active LLM run."""
        llm = stats.get('llm', {})
        if not llm.get('enabled'):
            return ''

        recommendation_items = ''.join(
            f'<li><strong>{html.escape(name)}</strong>: {count}</li>'
            for name, count in sorted(llm.get('recommendations', {}).items())
        ) or '<li><strong>n/a</strong>: no completed analyses</li>'
        intent_items = ''.join(
            f'<li><strong>{html.escape(name)}</strong>: {count}</li>'
            for name, count in sorted(llm.get('intents', {}).items())
        ) or '<li><strong>n/a</strong>: no completed analyses</li>'
        recommended_models = ', '.join(llm.get('recommended_models', [])) or 'n/a'

        return f'''
        <section class="quotable">
            <h2>LLM Analysis Run</h2>
            <div class="quote-box">
                <p><strong>Provider:</strong> {html.escape(str(llm.get('provider', 'unknown')).upper())} ({html.escape(str(llm.get('provider_type', 'unknown')))})</p>
                <p><strong>Model:</strong> {html.escape(str(llm.get('model', 'unknown')))} | <strong>Default:</strong> {html.escape(str(llm.get('default_model', 'unknown')))}</p>
                <p><strong>Filter:</strong> {html.escape(str(llm.get('message_filter', 'n/a')))} | <strong>Requested max:</strong> {llm.get('max_messages', 0)} | <strong>Selected:</strong> {llm.get('selected_message_count', 0)}</p>
                <p><strong>Completed:</strong> {llm.get('analyses_completed', 0)} | <strong>Failed:</strong> {llm.get('analyses_failed', 0)} | <strong>High priority:</strong> {llm.get('high_priority_count', 0)}</p>
                <p><strong>Recommended models:</strong> {html.escape(recommended_models)}</p>
                <div class="metric-grid">
                    <div class="metric">
                        <span class="metric-label">Recommendations</span>
                        <ul>
                            {recommendation_items}
                        </ul>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Detected intents</span>
                        <ul>
                            {intent_items}
                        </ul>
                    </div>
                </div>
            </div>
        </section>
        '''

    def _generate_pie_chart(self, stats: dict) -> str:
        """Generate an SVG pie chart."""
        categories = [
            ('Time Requests', stats['time_requests'], '#FF6B6B'),
            ('Financial Advisors', stats['financial_advisors'], '#4ECDC4'),
            ('Recruiters', stats['recruiters'], '#45B7D1'),
            ('Franchise', stats['franchise_consultants'], '#96CEB4'),
            ('Expert Networks', stats['expert_networks'], '#FFEAA7'),
            ('Sales Pitches', stats['sales_pitches'], '#DDA0DD'),
            ('AI Generated', stats['ai_generated'], '#98D8C8'),
        ]

        # Filter out zero values
        categories = [(name, val, color) for name, val, color in categories if val > 0]

        if not categories:
            return '<p class="no-data">No categorized messages found.</p>'

        total = sum(val for _, val, _ in categories)
        if total == 0:
            return '<p class="no-data">No categorized messages found.</p>'

        # Build SVG pie chart
        svg_parts = ['<svg viewBox="0 0 400 300" class="pie-chart">']

        # Pie chart
        cx, cy, r = 120, 150, 100
        start_angle = 0

        for name, value, color in categories:
            if value == 0:
                continue
            percentage = value / total
            end_angle = start_angle + percentage * 360

            # Calculate arc
            start_rad = start_angle * 3.14159 / 180
            end_rad = end_angle * 3.14159 / 180

            x1 = cx + r * __import__('math').cos(start_rad)
            y1 = cy + r * __import__('math').sin(start_rad)
            x2 = cx + r * __import__('math').cos(end_rad)
            y2 = cy + r * __import__('math').sin(end_rad)

            large_arc = 1 if percentage > 0.5 else 0

            path = f'M {cx},{cy} L {x1},{y1} A {r},{r} 0 {large_arc},1 {x2},{y2} Z'
            svg_parts.append(
                f'<path d="{path}" fill="{color}" stroke="white" stroke-width="2">'
                f'<title>{name}: {value} ({percentage*100:.1f}%)</title></path>'
            )

            start_angle = end_angle

        # Legend
        legend_x = 260
        legend_y = 50
        for i, (name, value, color) in enumerate(categories):
            y_pos = legend_y + i * 30
            svg_parts.append(f'<rect x="{legend_x}" y="{y_pos}" width="20" height="20" fill="{color}"/>')
            svg_parts.append(
                f'<text x="{legend_x + 28}" y="{y_pos + 15}" class="legend-text">'
                f'{html.escape(name)} ({value})</text>'
            )

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def _generate_hall_of_shame(self, stats: dict) -> str:
        """Generate the Hall of Shame section."""
        offenders = stats.get('repeat_offenders', [])

        if not offenders:
            return ''

        rows = []
        for i, (sender, count) in enumerate(offenders[:5], 1):
            medal = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][i-1] if i <= 5 else f'{i}.'
            rows.append(f'''
                <tr>
                    <td class="rank">{medal}</td>
                    <td class="sender">{html.escape(sender)}</td>
                    <td class="count">{count} messages</td>
                    <td class="persistence">{"Relentless" if count > 5 else "Persistent" if count > 3 else "Trying"}</td>
                </tr>
            ''')

        return f'''
        <section class="hall-of-shame">
            <h2>Hall of Shame</h2>
            <p class="section-subtitle">The most persistent senders who just won't quit</p>
            <table class="shame-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Sender</th>
                        <th>Messages</th>
                        <th>Persistence Level</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </section>
        '''

    def _generate_weekly_breakdown(self, stats: dict) -> str:
        """Generate weekly breakdown bar chart."""
        weekly = self.analyzer.get_weekly_summary().get('time_requests_by_week', {})

        if not weekly:
            return ''

        bars = []
        max_count = max((bucket.get('count', 0) for bucket in weekly.values()), default=1)

        for week, bucket in sorted(weekly.items())[-8:]:  # Last 8 weeks
            count = bucket.get('count', 0)
            height = (count / max_count) * 150 if max_count > 0 else 0
            bars.append(f'''
                <div class="bar-wrapper">
                    <div class="bar" style="height: {height}px">
                        <span class="bar-value">{count}</span>
                    </div>
                    <span class="bar-label">{week}</span>
                </div>
            ''')

        return f'''
        <section class="weekly-breakdown">
            <h2>Weekly Trend</h2>
            <div class="bar-chart">
                {''.join(bars)}
            </div>
        </section>
        '''

    def _get_css(self) -> str:
        """Return embedded CSS."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }

        header {
            text-align: center;
            margin-bottom: 50px;
        }

        h1 {
            font-size: 2.5rem;
            color: #fff;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            font-size: 1.2rem;
            color: #888;
            margin-bottom: 5px;
        }

        .date {
            font-size: 0.9rem;
            color: #666;
        }

        h2 {
            font-size: 1.5rem;
            color: #fff;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #333;
        }

        /* Summary Cards */
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 50px;
        }

        .card {
            background: #1e1e30;
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 1px solid #333;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .card-value {
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .card.total .card-value { color: #667eea; }
        .card.requests .card-value { color: #FF6B6B; }
        .card.advisors .card-value { color: #4ECDC4; }
        .card.recruiters .card-value { color: #45B7D1; }

        .card-label {
            font-size: 1rem;
            color: #aaa;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .card-subtitle {
            font-size: 0.8rem;
            color: #666;
            font-style: italic;
            margin-top: 5px;
        }

        /* Chart Section */
        .chart-section {
            background: #1e1e30;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 50px;
            border: 1px solid #333;
        }

        .chart-container {
            display: flex;
            justify-content: center;
        }

        .pie-chart {
            max-width: 100%;
            height: auto;
        }

        .legend-text {
            font-size: 14px;
            fill: #e0e0e0;
        }

        .no-data {
            text-align: center;
            color: #666;
            padding: 40px;
        }

        /* Metrics Grid */
        .metrics {
            margin-bottom: 50px;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }

        .metric {
            background: #1e1e30;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }

        .metric-value {
            display: block;
            font-size: 2rem;
            font-weight: bold;
            color: #fff;
        }

        .metric-label {
            display: block;
            color: #aaa;
            margin-top: 5px;
        }

        .metric-note {
            display: block;
            font-size: 0.8rem;
            color: #666;
            font-style: italic;
            margin-top: 5px;
        }

        .metric ul {
            list-style: none;
            margin-top: 12px;
            padding-left: 0;
        }

        .metric li {
            margin-bottom: 8px;
        }

        /* Hall of Shame */
        .hall-of-shame {
            background: #1e1e30;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 50px;
            border: 1px solid #333;
        }

        .section-subtitle {
            color: #888;
            margin-bottom: 20px;
            font-style: italic;
        }

        .shame-table {
            width: 100%;
            border-collapse: collapse;
        }

        .shame-table th,
        .shame-table td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #333;
        }

        .shame-table th {
            color: #667eea;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 1px;
        }

        .shame-table .rank {
            font-size: 1.5rem;
            width: 60px;
        }

        .shame-table .sender {
            color: #fff;
        }

        .shame-table .count {
            color: #FF6B6B;
        }

        .shame-table .persistence {
            color: #888;
            font-style: italic;
        }

        /* Weekly Breakdown */
        .weekly-breakdown {
            background: #1e1e30;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 50px;
            border: 1px solid #333;
        }

        .bar-chart {
            display: flex;
            justify-content: space-around;
            align-items: flex-end;
            height: 200px;
            padding: 20px;
        }

        .bar-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
        }

        .bar {
            width: 40px;
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            border-radius: 5px 5px 0 0;
            position: relative;
            min-height: 10px;
        }

        .bar-value {
            position: absolute;
            top: -25px;
            width: 100%;
            text-align: center;
            color: #fff;
            font-size: 0.9rem;
        }

        .bar-label {
            margin-top: 10px;
            font-size: 0.8rem;
            color: #888;
        }

        /* Quotable Section */
        .quotable {
            margin-bottom: 50px;
        }

        .quote-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 30px;
            color: #fff;
        }

        .quote-box ul {
            margin: 20px 0;
            padding-left: 20px;
        }

        .quote-box li {
            margin: 10px 0;
        }

        .hashtag {
            margin-top: 20px;
            font-size: 0.9rem;
            opacity: 0.8;
        }

        /* Footer */
        footer {
            text-align: center;
            padding: 30px;
            color: #666;
        }

        footer a {
            color: #667eea;
            text-decoration: none;
        }

        footer a:hover {
            text-decoration: underline;
        }

        .disclaimer {
            font-style: italic;
            margin-top: 10px;
            font-size: 0.9rem;
        }

        /* Responsive */
        @media (max-width: 768px) {
            h1 { font-size: 1.8rem; }
            .card-value { font-size: 2rem; }
            .metric-value { font-size: 1.5rem; }
            .bar { width: 25px; }
        }
        """

    def _get_js(self) -> str:
        """Return embedded JavaScript for interactivity."""
        return """
        // Add hover effects and tooltips
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.cursor = 'pointer';
            });
        });

        // Animate numbers on scroll
        const animateValue = (element, start, end, duration) => {
            let startTimestamp = null;
            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                element.textContent = Math.floor(progress * (end - start) + start);
                if (progress < 1) {
                    window.requestAnimationFrame(step);
                }
            };
            window.requestAnimationFrame(step);
        };

        // Intersection Observer for animations
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('section').forEach(section => {
            observer.observe(section);
        });
        """


def generate_html_report(analyzer: "LinkedInMessageAnalyzer", output_path: str | None = None) -> str:
    """Convenience function to generate HTML report.

    Args:
        analyzer: LinkedInMessageAnalyzer instance
        output_path: Optional path to save the report

    Returns:
        HTML string
    """
    reporter = HTMLReporter(analyzer)
    return reporter.generate(output_path)
