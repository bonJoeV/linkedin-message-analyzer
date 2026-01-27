"""Message clustering using embeddings and similarity."""

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.llm.base import LLMProvider
    from lib.types import Message

logger = logging.getLogger(__name__)


@dataclass
class MessageCluster:
    """A cluster of similar messages."""

    cluster_id: int
    label: str  # LLM-generated label
    messages: list[dict] = field(default_factory=list)
    is_template: bool = False  # Likely a mass outreach template
    common_phrases: list[str] = field(default_factory=list)
    sender_count: int = 0
    snark_observation: str = ""  # Witty observation about this cluster


@dataclass
class ClusteringResult:
    """Results from message clustering."""

    clusters: list[MessageCluster]
    template_clusters: list[MessageCluster]  # Clusters that look like templates
    total_messages: int
    unique_clusters: int


class MessageClusterer:
    """Clusters similar messages to find templates and patterns.

    Uses LLM to identify similar messages and detect mass outreach
    campaigns using the same template.
    """

    CLUSTER_PROMPT = '''Analyze these LinkedIn messages and group similar ones together.

Messages to analyze:
{messages}

Instructions:
1. Group messages that appear to be variations of the same template
2. Identify common phrases or patterns
3. Label each group with a descriptive name
4. Flag groups that look like mass outreach templates (same message, different names)

Return ONLY valid JSON:
{{
    "clusters": [
        {{
            "label": "Descriptive cluster name",
            "message_ids": [1, 3, 7],
            "is_template": true,
            "common_phrases": ["phrase 1", "phrase 2"],
            "snark_observation": "Witty observation about this type of message"
        }}
    ]
}}

Guidelines for snark_observation:
- Be witty but not mean
- Point out the absurdity or patterns
- Examples: "The classic 'quick call' that's never quick", "AI wrote this, and it shows"

Return ONLY the JSON, no other text.'''

    LABEL_PROMPT = '''Generate a short, descriptive label for this cluster of similar LinkedIn messages.

Sample messages from the cluster:
{samples}

Common themes:
{themes}

Return a short label (2-5 words) that captures what these messages are about.
Examples: "Financial Advisor Pitches", "Recruiter Vague Opportunities", "Quick Call Requests"

Return ONLY the label, no other text.'''

    def __init__(self, provider: 'LLMProvider'):
        """Initialize clusterer with LLM provider.

        Args:
            provider: Initialized LLM provider instance
        """
        self.provider = provider

    def cluster_messages(
        self,
        messages: list['Message'],
        max_messages: int = 100,
    ) -> ClusteringResult:
        """Cluster similar messages together.

        Args:
            messages: Messages to cluster
            max_messages: Maximum messages to analyze (for cost control)

        Returns:
            ClusteringResult with identified clusters
        """
        # Limit messages for API cost control
        sample = messages[:max_messages]

        # Format messages for prompt
        formatted = []
        for i, msg in enumerate(sample, 1):
            sender = msg.get('from', 'Unknown')
            content = msg.get('content', '')[:300]  # Truncate
            formatted.append(f"[{i}] From {sender}: {content}")

        messages_text = "\n\n".join(formatted)

        prompt = self.CLUSTER_PROMPT.format(messages=messages_text)

        try:
            response = self.provider.complete(prompt, max_tokens=800, temperature=0.2)
            return self._parse_response(response, sample)
        except Exception as e:
            logger.warning(f"Failed to cluster messages: {e}")
            return self._fallback_clustering(sample)

    def find_templates(
        self,
        messages: list['Message'],
        similarity_threshold: float = 0.8,
    ) -> list[MessageCluster]:
        """Find messages that appear to be from the same template.

        Uses text similarity to identify mass outreach campaigns.

        Args:
            messages: Messages to analyze
            similarity_threshold: Minimum similarity to consider template

        Returns:
            List of clusters that appear to be templates
        """
        result = self.cluster_messages(messages)
        return result.template_clusters

    def _parse_response(
        self,
        response: str,
        messages: list['Message'],
    ) -> ClusteringResult:
        """Parse LLM response into ClusteringResult."""
        try:
            # Clean response
            cleaned = response.strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('```')[1]
                if cleaned.startswith('json'):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)

            clusters = []
            template_clusters = []

            for i, cluster_data in enumerate(data.get('clusters', [])):
                message_ids = cluster_data.get('message_ids', [])

                # Get actual messages for this cluster
                cluster_messages = []
                senders = set()
                for msg_id in message_ids:
                    if 1 <= msg_id <= len(messages):
                        msg = messages[msg_id - 1]
                        cluster_messages.append(msg)
                        senders.add(msg.get('from', 'Unknown'))

                cluster = MessageCluster(
                    cluster_id=i,
                    label=cluster_data.get('label', f'Cluster {i + 1}'),
                    messages=cluster_messages,
                    is_template=cluster_data.get('is_template', False),
                    common_phrases=cluster_data.get('common_phrases', []),
                    sender_count=len(senders),
                    snark_observation=cluster_data.get('snark_observation', ''),
                )

                clusters.append(cluster)
                if cluster.is_template:
                    template_clusters.append(cluster)

            return ClusteringResult(
                clusters=clusters,
                template_clusters=template_clusters,
                total_messages=len(messages),
                unique_clusters=len(clusters),
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse clustering response: {e}")
            return self._fallback_clustering(messages)

    def _fallback_clustering(
        self,
        messages: list['Message'],
    ) -> ClusteringResult:
        """Generate fallback result when LLM fails."""
        # Simple fallback: one cluster with all messages
        cluster = MessageCluster(
            cluster_id=0,
            label='All Messages',
            messages=list(messages),
            is_template=False,
            common_phrases=[],
            sender_count=len(set(m.get('from', '') for m in messages)),
            snark_observation='Clustering failed - these need manual review',
        )

        return ClusteringResult(
            clusters=[cluster],
            template_clusters=[],
            total_messages=len(messages),
            unique_clusters=1,
        )

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple word overlap.

        This is a fallback when embeddings aren't available.
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def generate_cluster_report(
        self,
        result: ClusteringResult,
    ) -> str:
        """Generate a formatted clustering report.

        Args:
            result: Clustering result to format

        Returns:
            Formatted string report
        """
        lines = [
            "=" * 60,
            "MESSAGE CLUSTERING (LLM-Powered)",
            "=" * 60,
            f"\n  Total Messages: {result.total_messages}",
            f"  Clusters Found: {result.unique_clusters}",
            f"  Template Campaigns: {len(result.template_clusters)}",
        ]

        # Sort clusters by size
        sorted_clusters = sorted(
            result.clusters,
            key=lambda c: len(c.messages),
            reverse=True,
        )

        for cluster in sorted_clusters:
            template_badge = " 📋 TEMPLATE" if cluster.is_template else ""
            lines.append(f"\n  ╭{'─' * 50}")
            lines.append(f"  │ {cluster.label}{template_badge}")
            lines.append(f"  │ Messages: {len(cluster.messages)} from {cluster.sender_count} senders")

            if cluster.common_phrases:
                lines.append(f"  │ Common phrases:")
                for phrase in cluster.common_phrases[:3]:
                    lines.append(f"  │   • \"{phrase}\"")

            if cluster.snark_observation:
                lines.append(f"  │")
                lines.append(f"  │ 🎯 {cluster.snark_observation}")

            # Show sample senders
            if cluster.messages:
                senders = list(set(m.get('from', 'Unknown') for m in cluster.messages))[:3]
                lines.append(f"  │ Sample senders: {', '.join(senders)}")

            lines.append(f"  ╰{'─' * 50}")

        # Template detection summary
        if result.template_clusters:
            lines.append(f"\n  {'═' * 50}")
            lines.append("  TEMPLATE DETECTION SUMMARY")
            lines.append(f"  {'═' * 50}")
            total_template_msgs = sum(len(c.messages) for c in result.template_clusters)
            lines.append(f"\n  {total_template_msgs} messages appear to be from mass outreach templates")
            lines.append("  These senders are probably messaging hundreds of people with")
            lines.append("  the same script. Your time is worth more than that.")

        return "\n".join(lines)
