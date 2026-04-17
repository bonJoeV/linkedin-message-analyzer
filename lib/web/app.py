"""Flask web dashboard with Commodore 64 aesthetic."""

import logging
from typing import Any, TYPE_CHECKING

try:
    from flask import Flask, jsonify, make_response, render_template_string, request
except ImportError:
    Flask = None

if TYPE_CHECKING:
    from lib.analyzer import LinkedInMessageAnalyzer

logger = logging.getLogger(__name__)

# The classic C64 BASIC screen colors
C64_BG = '#4040E0'
C64_BORDER = '#A0A0FF'
C64_TEXT = '#A0A0FF'
C64_HIGHLIGHT = '#FFFFFF'

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
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            min-height: calc(100vh - 40px);
        }

        .header {
            text-align: center;
            margin-bottom: 24px;
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
            font-size: 1.2em;
            margin-top: 8px;
        }

        .ready-prompt {
            margin-top: 8px;
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
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .stat-box,
        .panel,
        .filters {
            background-color: rgba(0, 0, 0, 0.28);
            border: 2px solid {{ c64_text }};
            padding: 14px;
        }

        .stat-box h3,
        .panel h2,
        .filters h2 {
            color: {{ c64_highlight }};
            font-size: 1.25em;
            margin-bottom: 10px;
            border-bottom: 1px dashed {{ c64_text }};
            padding-bottom: 4px;
        }

        .stat-value {
            font-size: 2.2em;
            color: {{ c64_highlight }};
            text-align: center;
            margin: 8px 0;
        }

        .stat-label {
            text-align: center;
        }

        .filters {
            margin-bottom: 24px;
        }

        .llm-status-panel {
            margin-bottom: 24px;
        }

        .filter-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            align-items: end;
        }

        .filter-control label {
            display: block;
            font-size: 1em;
            margin-bottom: 6px;
            color: {{ c64_highlight }};
        }

        .filter-control select,
        .filter-control input {
            width: 100%;
            background-color: rgba(0, 0, 0, 0.45);
            color: {{ c64_text }};
            border: 2px solid {{ c64_text }};
            padding: 8px;
            font-family: 'VT323', 'Courier New', monospace;
            font-size: 1.05em;
        }

        .checkbox-row {
            display: flex;
            align-items: center;
            gap: 8px;
            padding-bottom: 10px;
        }

        .checkbox-row input {
            width: auto;
        }

        .button-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .actions-row {
            margin-top: 12px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .status-line {
            margin-top: 10px;
            min-height: 1.2em;
            color: {{ c64_highlight }};
        }

        .c64-button {
            background-color: {{ c64_bg }};
            color: {{ c64_text }};
            border: 2px solid {{ c64_text }};
            padding: 10px 16px;
            font-family: 'VT323', 'Courier New', monospace;
            font-size: 1.1em;
            cursor: pointer;
        }

        .c64-button:hover {
            background-color: {{ c64_text }};
            color: {{ c64_bg }};
        }

        .panel-grid {
            display: grid;
            grid-template-columns: 1.1fr 0.9fr 1.2fr;
            gap: 16px;
        }

        .list-panel {
            max-height: 520px;
            overflow-y: auto;
            padding-right: 4px;
        }

        .list-item {
            border: 1px solid {{ c64_text }};
            padding: 10px;
            margin-bottom: 10px;
            cursor: pointer;
            background-color: rgba(0, 0, 0, 0.2);
        }

        .list-item:hover,
        .list-item.active {
            background-color: rgba(255, 255, 255, 0.12);
        }

        .item-title {
            color: {{ c64_highlight }};
            font-size: 1.15em;
        }

        .item-meta {
            margin-top: 6px;
            font-size: 0.95em;
            line-height: 1.2;
        }

        .pill-row {
            margin-top: 8px;
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }

        .pill {
            display: inline-block;
            border: 1px solid {{ c64_text }};
            padding: 2px 8px;
            font-size: 0.9em;
        }

        .pill.reply {
            color: #AAFF66;
            border-color: #AAFF66;
        }

        .pill.ignore {
            color: #FF7777;
            border-color: #FF7777;
        }

        .detail-block {
            margin-bottom: 14px;
            padding-bottom: 10px;
            border-bottom: 1px dashed {{ c64_text }};
        }

        .detail-block:last-child {
            border-bottom: none;
        }

        .detail-label {
            color: {{ c64_highlight }};
        }

        .message-preview {
            margin-top: 6px;
            padding: 8px;
            border: 1px dashed {{ c64_text }};
            background-color: rgba(0, 0, 0, 0.18);
        }

        .footer {
            text-align: center;
            margin-top: 24px;
            padding-top: 14px;
            border-top: 2px solid {{ c64_text }};
        }

        @media (max-width: 1100px) {
            .panel-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="screen">
        <div class="header">
            <h1>**** LINKEDIN INBOX ANALYZER V3 ****</h1>
            <div class="subtitle">THREAD TRIAGE COMMAND CENTER</div>
            <div class="ready-prompt">READY.<span class="cursor"></span></div>
        </div>

        <div class="stats-grid">
            <div class="stat-box">
                <h3>TOTAL MESSAGES</h3>
                <div class="stat-value">{{ stats.total_messages }}</div>
                <div class="stat-label">MESSAGES ANALYZED</div>
            </div>
            <div class="stat-box">
                <h3>THREADS</h3>
                <div class="stat-value">{{ stats.total_threads }}</div>
                <div class="stat-label">CONVERSATIONS TRACKED</div>
            </div>
            <div class="stat-box">
                <h3>NEEDS REPLY</h3>
                <div class="stat-value">{{ stats.needs_reply_count }}</div>
                <div class="stat-label">TRIAGE ITEMS WORTH REVIEW</div>
            </div>
            <div class="stat-box">
                <h3>SAFE TO IGNORE</h3>
                <div class="stat-value">{{ stats.safe_to_ignore_count }}</div>
                <div class="stat-label">LOW-VALUE THREADS</div>
            </div>
        </div>

        <div class="filters">
            <h2>FILTER INBOX</h2>
            <div class="filter-grid">
                <div class="filter-control">
                    <label for="sender-filter">SENDER</label>
                    <select id="sender-filter">
                        <option value="">ALL SENDERS</option>
                        {% for sender in dashboard_data.available_senders %}
                        <option value="{{ sender }}">{{ sender }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="filter-control">
                    <label for="label-filter">LABEL</label>
                    <select id="label-filter">
                        <option value="">ALL LABELS</option>
                        {% for label in dashboard_data.available_labels %}
                        <option value="{{ label }}">{{ label }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="filter-control">
                    <label for="recommendation-filter">RECOMMENDATION</label>
                    <select id="recommendation-filter">
                        <option value="">ALL</option>
                        <option value="needs_reply">needs_reply</option>
                        <option value="safe_to_ignore">safe_to_ignore</option>
                    </select>
                </div>
                <div class="filter-control">
                    <label for="llm-recommendation-filter">LLM RECOMMENDATION</label>
                    <select id="llm-recommendation-filter">
                        <option value="">ALL LLM RECOMMENDATIONS</option>
                        {% for llm_recommendation in dashboard_data.available_llm_recommendations %}
                        <option value="{{ llm_recommendation }}">{{ llm_recommendation }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="filter-control">
                    <label for="llm-intent-filter">LLM INTENT</label>
                    <select id="llm-intent-filter">
                        <option value="">ALL LLM INTENTS</option>
                        {% for llm_intent in dashboard_data.available_llm_intents %}
                        <option value="{{ llm_intent }}">{{ llm_intent }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="filter-control">
                    <label for="score-filter">MIN TRIAGE SCORE</label>
                    <input id="score-filter" type="number" min="0" step="1" value="0">
                </div>
                <div class="filter-control">
                    <label for="sort-filter">SORT BY</label>
                    <select id="sort-filter">
                        <option value="triage">triage</option>
                        <option value="llm_recommendation">llm_recommendation</option>
                        <option value="last_message">last_message</option>
                    </select>
                </div>
                <div class="filter-control checkbox-row">
                    <input id="unanswered-filter" type="checkbox">
                    <label for="unanswered-filter">UNANSWERED ONLY</label>
                </div>
                <div class="filter-control button-row">
                    <button class="c64-button" id="apply-filters">APPLY</button>
                    <button class="c64-button" id="reset-filters">RESET</button>
                    <button class="c64-button" id="export-csv">EXPORT CSV</button>
                    <button class="c64-button" id="export-json">EXPORT JSON</button>
                </div>
            </div>
            <div id="dashboard-status" class="status-line"></div>
        </div>

        <div class="panel llm-status-panel">
            <h2>LLM ANALYSIS</h2>
            {% if dashboard_data.llm.enabled %}
            <div class="detail-block">
                <div><span class="detail-label">Provider:</span> {{ dashboard_data.llm.provider|upper }} ({{ dashboard_data.llm.provider_type }})</div>
                <div><span class="detail-label">Model:</span> {{ dashboard_data.llm.model }}</div>
                <div><span class="detail-label">Filter:</span> {{ dashboard_data.llm.message_filter or 'n/a' }}</div>
                <div><span class="detail-label">Messages:</span> {{ dashboard_data.llm.analyses_completed }} completed / {{ dashboard_data.llm.selected_message_count }} selected</div>
                <div><span class="detail-label">High priority:</span> {{ dashboard_data.llm.high_priority_count }}</div>
                <div><span class="detail-label">Recommended models:</span> {{ dashboard_data.llm.recommended_models | join(', ') }}</div>
            </div>
            {% else %}
            <div class="detail-block">LLM ANALYSIS WAS NOT ENABLED FOR THIS RUN.</div>
            {% endif %}
        </div>

        <div class="panel-grid">
            <div class="panel">
                <h2>THREAD TRIAGE QUEUE</h2>
                <div id="triage-list" class="list-panel"></div>
            </div>

            <div class="panel">
                <h2>SENDER DRILL-DOWN</h2>
                <div id="sender-list" class="list-panel"></div>
            </div>

            <div class="panel">
                <h2>THREAD DETAIL</h2>
                <div id="thread-detail"></div>
            </div>
        </div>

        <div class="footer">
            <p>LOAD"TRIAGE",8,1</p>
            <p>SEARCHING FOR HIGH-SIGNAL REPLIES</p>
            <p>BUILT WITH MASS PASSIVE AGGRESSION</p>
        </div>
    </div>

    <script>
        const dashboardState = {
            triageItems: {{ dashboard_data.triage_items | tojson }},
            senderSummaries: {{ dashboard_data.sender_summaries | tojson }},
            threadDetails: {{ dashboard_data.thread_details | tojson }},
            selectedConversationId: {{ dashboard_data.thread_details[0].conversation_id | tojson if dashboard_data.thread_details else 'null' }},
        };

        const senderFilter = document.getElementById('sender-filter');
        const labelFilter = document.getElementById('label-filter');
        const recommendationFilter = document.getElementById('recommendation-filter');
        const llmRecommendationFilter = document.getElementById('llm-recommendation-filter');
        const llmIntentFilter = document.getElementById('llm-intent-filter');
        const scoreFilter = document.getElementById('score-filter');
        const sortFilter = document.getElementById('sort-filter');
        const unansweredFilter = document.getElementById('unanswered-filter');

        function renderTriageList() {
            const container = document.getElementById('triage-list');
            if (!dashboardState.triageItems.length) {
                container.innerHTML = '<div class="detail-block">NO TRIAGE ITEMS MATCH THE CURRENT FILTERS.</div>';
                return;
            }

            container.innerHTML = dashboardState.triageItems.map((item) => {
                const activeClass = dashboardState.selectedConversationId === item.conversation_id ? 'active' : '';
                const recommendationClass = item.recommendation === 'needs_reply' ? 'reply' : 'ignore';
                const labels = item.labels.length ? item.labels.join(', ') : 'uncategorized';
                const llmRecommendation = item.llm_recommendation ? `LLM ${item.llm_recommendation}` : '';
                const llmIntent = item.llm_intent ? `Intent ${item.llm_intent}` : '';
                const llmPills = [llmRecommendation, llmIntent]
                    .filter(Boolean)
                    .map((value) => `<span class="pill">${value}</span>`)
                    .join('');
                return `
                    <div class="list-item ${activeClass}" data-conversation-id="${item.conversation_id}">
                        <div class="item-title">${item.primary_sender || 'Unknown sender'}</div>
                        <div class="item-meta">Score ${item.triage_score} | ${item.incoming_count} incoming | ${item.conversation_title || 'Untitled conversation'}</div>
                        <div class="pill-row">
                            <span class="pill ${recommendationClass}">${item.recommendation}</span>
                            <span class="pill">${labels}</span>
                            ${llmPills}
                        </div>
                    </div>
                `;
            }).join('');

            container.querySelectorAll('.list-item').forEach((node) => {
                node.addEventListener('click', () => {
                    dashboardState.selectedConversationId = node.dataset.conversationId;
                    renderTriageList();
                    renderThreadDetail();
                });
            });
        }

        function renderSenderList() {
            const container = document.getElementById('sender-list');
            if (!dashboardState.senderSummaries.length) {
                container.innerHTML = '<div class="detail-block">NO SENDERS MATCH THE CURRENT FILTERS.</div>';
                return;
            }

            container.innerHTML = dashboardState.senderSummaries.map((summary) => `
                <div class="list-item" data-sender="${summary.sender}">
                    <div class="item-title">${summary.sender}</div>
                    <div class="item-meta">${summary.conversation_count} threads | ${summary.unanswered_message_count} unanswered messages</div>
                    <div class="pill-row">
                        <span class="pill">last contact ${summary.last_contact || 'n/a'}</span>
                    </div>
                </div>
            `).join('');

            container.querySelectorAll('.list-item').forEach((node) => {
                node.addEventListener('click', () => {
                    senderFilter.value = node.dataset.sender;
                    refreshDashboardData();
                });
            });
        }

        function renderThreadDetail() {
            const container = document.getElementById('thread-detail');
            const thread = dashboardState.threadDetails.find((item) => item.conversation_id === dashboardState.selectedConversationId)
                || dashboardState.threadDetails[0];

            if (!thread) {
                container.innerHTML = '<div class="detail-block">SELECT A THREAD TO SEE DETAILS.</div>';
                return;
            }

            dashboardState.selectedConversationId = thread.conversation_id;
            const recommendationClass = thread.recommendation === 'needs_reply' ? 'reply' : 'ignore';
            const llmMarkup = thread.llm && thread.llm.analysis_count
                ? `
                    <div><span class="detail-label">LLM recommendation:</span> ${thread.llm.recommendation || 'n/a'}</div>
                    <div><span class="detail-label">LLM intent:</span> ${thread.llm.intent || 'n/a'}</div>
                    <div><span class="detail-label">LLM analyses:</span> ${thread.llm.analysis_count}</div>
                    <div><span class="detail-label">LLM high priority count:</span> ${thread.llm.high_priority_count}</div>
                    <div><span class="detail-label">LLM max authenticity:</span> ${thread.llm.max_authenticity_score}</div>
                `
                : '<div><span class="detail-label">LLM:</span> no thread-level LLM signals for this conversation</div>';
            const messageMarkup = thread.messages.map((message) => `
                <div class="message-preview">
                    <div><span class="detail-label">${message.from}</span> | ${message.date || 'Unknown date'} | ${message.folder || 'UNKNOWN'}</div>
                    <div>${message.preview}</div>
                </div>
            `).join('');

            container.innerHTML = `
                <div class="detail-block">
                    <div class="item-title">${thread.primary_sender || 'Unknown sender'}</div>
                    <div class="item-meta">${thread.conversation_title || 'Untitled conversation'}</div>
                    <div class="pill-row">
                        <span class="pill ${recommendationClass}">${thread.recommendation}</span>
                        <span class="pill">score ${thread.triage_score}</span>
                        <span class="pill">${thread.labels.length ? thread.labels.join(', ') : 'uncategorized'}</span>
                    </div>
                </div>
                <div class="detail-block">
                    <div><span class="detail-label">Reason:</span> ${thread.recommendation_reason}</div>
                    <div><span class="detail-label">Participants:</span> ${thread.participants.join(', ') || 'Unknown'}</div>
                    <div><span class="detail-label">Incoming:</span> ${thread.incoming_count}</div>
                    <div><span class="detail-label">Last contact:</span> ${thread.last_message_at || 'Unknown'}</div>
                    ${llmMarkup}
                    <div class="actions-row">
                        <button class="c64-button" id="copy-thread-summary">COPY SUMMARY</button>
                        <button class="c64-button" id="copy-latest-preview">COPY LATEST</button>
                    </div>
                </div>
                <div class="detail-block">
                    <div class="detail-label">MESSAGE PREVIEWS</div>
                    ${messageMarkup || '<div class="message-preview">NO MESSAGE PREVIEWS AVAILABLE.</div>'}
                </div>
            `;

            document.getElementById('copy-thread-summary').addEventListener('click', async () => {
                const summary = buildThreadSummary(thread);
                await copyToClipboard(summary, 'THREAD SUMMARY COPIED.');
            });
            document.getElementById('copy-latest-preview').addEventListener('click', async () => {
                const latest = thread.messages[thread.messages.length - 1]?.preview || '';
                await copyToClipboard(latest || 'No preview available.', 'LATEST MESSAGE COPIED.');
            });
        }

        function buildFilterParams() {
            const params = new URLSearchParams();
            if (senderFilter.value) params.set('sender', senderFilter.value);
            if (labelFilter.value) params.set('label', labelFilter.value);
            if (recommendationFilter.value) params.set('recommendation', recommendationFilter.value);
            if (llmRecommendationFilter.value) params.set('llm_recommendation', llmRecommendationFilter.value);
            if (llmIntentFilter.value) params.set('llm_intent', llmIntentFilter.value);
            if (scoreFilter.value && Number(scoreFilter.value) > 0) params.set('min_score', scoreFilter.value);
            if (sortFilter.value && sortFilter.value !== 'triage') params.set('sort_by', sortFilter.value);
            if (unansweredFilter.checked) params.set('unanswered_only', 'true');
            return params;
        }

        function buildThreadSummary(thread) {
            const latest = thread.messages[thread.messages.length - 1]?.preview || 'No preview available.';
            return [
                `Sender: ${thread.primary_sender || 'Unknown sender'}`,
                `Conversation: ${thread.conversation_title || 'Untitled conversation'}`,
                `Recommendation: ${thread.recommendation}`,
                `Reason: ${thread.recommendation_reason}`,
                `Score: ${thread.triage_score}`,
                `Labels: ${thread.labels.length ? thread.labels.join(', ') : 'uncategorized'}`,
                `LLM recommendation: ${thread.llm?.recommendation || 'n/a'}`,
                `LLM intent: ${thread.llm?.intent || 'n/a'}`,
                `Last contact: ${thread.last_message_at || 'Unknown'}`,
                `Latest preview: ${latest}`,
            ].join('\n');
        }

        async function copyToClipboard(text, statusText) {
            try {
                await navigator.clipboard.writeText(text);
                setStatus(statusText);
            } catch {
                const fallback = document.createElement('textarea');
                fallback.value = text;
                document.body.appendChild(fallback);
                fallback.select();
                document.execCommand('copy');
                document.body.removeChild(fallback);
                setStatus(statusText);
            }
        }

        function setStatus(message) {
            document.getElementById('dashboard-status').textContent = message;
        }

        async function refreshDashboardData() {
            const params = buildFilterParams();

            const response = await fetch(`/api/dashboard-data?${params.toString()}`);
            const payload = await response.json();

            dashboardState.triageItems = payload.triage_items;
            dashboardState.senderSummaries = payload.sender_summaries;
            dashboardState.threadDetails = payload.thread_details;

            const selectedStillVisible = dashboardState.threadDetails.some(
                (item) => item.conversation_id === dashboardState.selectedConversationId,
            );
            if (!selectedStillVisible) {
                dashboardState.selectedConversationId = dashboardState.threadDetails[0]?.conversation_id || null;
            }

            renderTriageList();
            renderSenderList();
            renderThreadDetail();
        }

        document.getElementById('apply-filters').addEventListener('click', refreshDashboardData);
        document.getElementById('export-csv').addEventListener('click', () => {
            window.location.href = `/api/export?format=csv&${buildFilterParams().toString()}`;
        });
        document.getElementById('export-json').addEventListener('click', () => {
            window.location.href = `/api/export?format=json&${buildFilterParams().toString()}`;
        });
        document.getElementById('reset-filters').addEventListener('click', () => {
            senderFilter.value = '';
            labelFilter.value = '';
            recommendationFilter.value = '';
            llmRecommendationFilter.value = '';
            llmIntentFilter.value = '';
            scoreFilter.value = '0';
            sortFilter.value = 'triage';
            unansweredFilter.checked = false;
            setStatus('FILTERS RESET.');
            refreshDashboardData();
        });

        renderTriageList();
        renderSenderList();
        renderThreadDetail();
    </script>
</body>
</html>
'''


def _build_filter_kwargs() -> dict[str, Any]:
    """Build dashboard filter kwargs from the current request."""
    min_score_raw = request.args.get('min_score')
    return {
        'sender': request.args.get('sender') or None,
        'labels': _parse_labels(request.args.getlist('label')),
        'min_triage_score': int(min_score_raw) if min_score_raw not in (None, '') else None,
        'unanswered_only': _parse_bool(request.args.get('unanswered_only')),
        'recommendation': request.args.get('recommendation') or None,
        'llm_recommendation': request.args.get('llm_recommendation') or None,
        'llm_intent': request.args.get('llm_intent') or None,
        'sort_by': request.args.get('sort_by') or 'triage',
    }


def _parse_bool(value: str | None) -> bool:
    """Parse a truthy query-string value."""
    return bool(value and value.lower() in {'1', 'true', 'yes', 'on'})


def _parse_labels(raw_labels: list[str]) -> list[str]:
    """Normalize label query parameters."""
    labels: list[str] = []
    for raw_label in raw_labels:
        labels.extend(
            part.strip()
            for part in raw_label.split(',')
            if part.strip()
        )
    return labels


def _build_stats(analyzer: 'LinkedInMessageAnalyzer') -> dict[str, Any]:
    """Build summary stats for the dashboard header."""
    triage_items = analyzer.get_thread_triage_queue(include_responded=True)
    return {
        'total_messages': len(analyzer.messages),
        'total_threads': len(analyzer.get_conversation_threads()),
        'needs_reply_count': sum(1 for item in triage_items if item.get('recommendation') == 'needs_reply'),
        'safe_to_ignore_count': sum(1 for item in triage_items if item.get('recommendation') == 'safe_to_ignore'),
    }


def _serialize_sender_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """Serialize sender summaries for JSON or template use."""
    return {
        'sender': summary.get('sender', ''),
        'conversation_count': summary.get('conversation_count', 0),
        'unanswered_message_count': summary.get('unanswered_message_count', 0),
        'last_contact': summary['last_contact'].strftime('%Y-%m-%d') if summary.get('last_contact') else None,
    }


def _serialize_thread_detail(thread: dict[str, Any], triage_item: dict[str, Any]) -> dict[str, Any]:
    """Serialize a thread and its triage metadata for the dashboard."""
    messages = []
    for message in thread.get('messages', [])[-5:]:
        preview = (message.get('content', '') or '')[:160]
        messages.append({
            'from': message.get('from', 'Unknown'),
            'date': message['date'].strftime('%Y-%m-%d %H:%M') if message.get('date') else None,
            'folder': message.get('folder', ''),
            'preview': preview,
        })

    return {
        'conversation_id': thread.get('conversation_id', ''),
        'conversation_title': thread.get('conversation_title', ''),
        'primary_sender': thread.get('primary_sender', ''),
        'participants': thread.get('participants', []),
        'incoming_count': thread.get('incoming_count', 0),
        'message_count': thread.get('message_count', 0),
        'last_message_at': thread['last_message_at'].strftime('%Y-%m-%d %H:%M') if thread.get('last_message_at') else None,
        'triage_score': triage_item.get('triage_score', 0),
        'labels': triage_item.get('labels', []),
        'recommendation': triage_item.get('recommendation', 'safe_to_ignore'),
        'recommendation_reason': triage_item.get('recommendation_reason', ''),
        'llm': {
            'recommendation': triage_item.get('llm_recommendation', ''),
            'intent': triage_item.get('llm_intent', ''),
            'analysis_count': triage_item.get('llm_analysis_count', 0),
            'high_priority_count': triage_item.get('llm_high_priority_count', 0),
            'max_authenticity_score': triage_item.get('llm_max_authenticity_score', 0),
        },
        'messages': messages,
    }


def _build_dashboard_payload(
    analyzer: 'LinkedInMessageAnalyzer',
    *,
    sender: str | None = None,
    labels: list[str] | None = None,
    min_triage_score: int | None = None,
    unanswered_only: bool = False,
    recommendation: str | None = None,
    llm_recommendation: str | None = None,
    llm_intent: str | None = None,
    sort_by: str = 'triage',
) -> dict[str, Any]:
    """Build filtered dashboard data for the web UI and API."""
    triage_items = analyzer.get_filtered_thread_triage_queue(
        labels=labels,
        min_triage_score=min_triage_score,
        unanswered_only=unanswered_only,
        recommendation=recommendation,
        sender=sender,
        llm_recommendation=llm_recommendation,
        llm_intent=llm_intent,
        sort_by=sort_by,
    )
    conversation_threads = analyzer.get_conversation_threads()
    triage_lookup = {item['conversation_id']: item for item in triage_items}
    filtered_ids = [item['conversation_id'] for item in triage_items]
    filtered_sender_names = {item.get('primary_sender', '') for item in triage_items if item.get('primary_sender')}

    sender_summaries = [
        _serialize_sender_summary(summary)
        for summary in analyzer.get_sender_summaries()
        if summary.get('sender') in filtered_sender_names
    ]

    thread_details = [
        _serialize_thread_detail(conversation_threads[conversation_id], triage_lookup[conversation_id])
        for conversation_id in filtered_ids
        if conversation_id in conversation_threads
    ]

    available_labels = sorted({
        label
        for item in analyzer.get_thread_triage_queue(include_responded=True)
        for label in item.get('labels', [])
    })
    available_senders = sorted({
        summary.get('sender', '')
        for summary in analyzer.get_sender_summaries()
        if summary.get('sender')
    })
    thread_llm_signals = analyzer.get_thread_llm_signals()
    available_llm_recommendations = sorted({
        signal.get('primary_recommendation', '')
        for signal in thread_llm_signals.values()
        if signal.get('primary_recommendation')
    })
    available_llm_intents = sorted({
        signal.get('primary_intent', '')
        for signal in thread_llm_signals.values()
        if signal.get('primary_intent')
    })

    return {
        'filters': {
            'sender': sender,
            'labels': labels or [],
            'min_triage_score': min_triage_score,
            'unanswered_only': unanswered_only,
            'recommendation': recommendation,
            'llm_recommendation': llm_recommendation,
            'llm_intent': llm_intent,
            'sort_by': sort_by,
        },
        'llm': analyzer.get_llm_run_info(),
        'triage_items': triage_items,
        'sender_summaries': sender_summaries,
        'thread_details': thread_details,
        'available_labels': available_labels,
        'available_senders': available_senders,
        'available_llm_recommendations': available_llm_recommendations,
        'available_llm_intents': available_llm_intents,
    }


def create_app(analyzer: 'LinkedInMessageAnalyzer') -> 'Flask':
    """Create Flask application with analyzer data."""
    if Flask is None:
        raise ImportError('Flask not installed. Run: pip install flask')

    app = Flask(__name__)
    app.config['analyzer'] = analyzer

    @app.route('/')
    def index():
        dashboard_data = _build_dashboard_payload(analyzer)
        return render_template_string(
            C64_HTML_TEMPLATE,
            stats=_build_stats(analyzer),
            dashboard_data=dashboard_data,
            c64_bg=C64_BG,
            c64_border=C64_BORDER,
            c64_text=C64_TEXT,
            c64_highlight=C64_HIGHLIGHT,
        )

    @app.route('/api/stats')
    def api_stats():
        return jsonify(_build_stats(app.config['analyzer']))

    @app.route('/api/dashboard-data')
    def api_dashboard_data():
        payload = _build_dashboard_payload(app.config['analyzer'], **_build_filter_kwargs())
        return jsonify(payload)

    @app.route('/api/export')
    def api_export():
        export_format = (request.args.get('format') or 'csv').lower()
        filter_kwargs = _build_filter_kwargs()

        if export_format == 'json':
            from lib.reporters import JSONReporter

            payload = JSONReporter(**filter_kwargs).generate(app.config['analyzer'])
            response = make_response(payload)
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            response.headers['Content-Disposition'] = 'attachment; filename=thread-triage-export.json'
            return response

        from lib.reporters import CSVReporter

        payload = CSVReporter(**filter_kwargs).generate(app.config['analyzer'])
        response = make_response(payload)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename=thread-triage-export.csv'
        return response

    return app


def run_dashboard(
    analyzer: 'LinkedInMessageAnalyzer',
    port: int = 6502,
    debug: bool = False,
) -> None:
    """Run the web dashboard."""
    app = create_app(analyzer)

    print(f"""
**** LINKEDIN INBOX ANALYZER V3 ****

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
