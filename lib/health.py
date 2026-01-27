"""Network health score calculator for LinkedIn inbox quality."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.analyzer import LinkedInMessageAnalyzer


@dataclass
class HealthScore:
    """Overall network health score.

    Attributes:
        overall: Total score 0-100 (higher is better)
        spam_ratio: Ratio of spam to total (0-1, lower is better)
        engagement_quality: Quality of interactions (0-100)
        connection_value: Value of connections messaging you (0-100)
        breakdown: Score breakdown by category
        recommendations: Actionable improvement suggestions
        grade: Letter grade (A, B, C, D, F)
    """

    overall: float
    spam_ratio: float
    engagement_quality: float
    connection_value: float
    breakdown: dict[str, float]
    recommendations: list[str]
    grade: str


class NetworkHealthAnalyzer:
    """Calculates network health metrics based on inbox analysis.

    The health score reflects the quality of your LinkedIn network
    based on who's messaging you and what they're asking for.

    Higher scores indicate more genuine connections and fewer
    automated/spam messages.
    """

    # Score weights
    SPAM_WEIGHT = 40       # 40% of score from spam ratio
    ENGAGEMENT_WEIGHT = 30  # 30% from engagement quality
    CONNECTION_WEIGHT = 30  # 30% from connection value

    def __init__(self, analyzer: 'LinkedInMessageAnalyzer') -> None:
        """Initialize with a LinkedInMessageAnalyzer.

        Args:
            analyzer: Analyzer with loaded and analyzed messages
        """
        self.analyzer = analyzer

    def calculate_health_score(self) -> HealthScore:
        """Calculate overall network health score.

        Returns:
            HealthScore with all metrics and recommendations
        """
        total_messages = len(self.analyzer.messages)

        if total_messages == 0:
            return HealthScore(
                overall=0,
                spam_ratio=0,
                engagement_quality=0,
                connection_value=0,
                breakdown={},
                recommendations=["No messages to analyze"],
                grade="N/A",
            )

        # Calculate component scores
        spam_ratio = self._calculate_spam_ratio()
        spam_score = (1 - spam_ratio) * 100  # Invert so higher is better

        engagement_quality = self._calculate_engagement_quality()
        connection_value = self._calculate_connection_value()

        # Weighted overall score
        overall = (
            spam_score * (self.SPAM_WEIGHT / 100) +
            engagement_quality * (self.ENGAGEMENT_WEIGHT / 100) +
            connection_value * (self.CONNECTION_WEIGHT / 100)
        )

        # Build breakdown
        breakdown = {
            'spam_free': round(spam_score, 1),
            'engagement': round(engagement_quality, 1),
            'connection_value': round(connection_value, 1),
            'ai_generated_pct': round(len(self.analyzer.ai_generated_messages) / total_messages * 100, 1),
            'template_pct': round(len(self.analyzer.template_messages) / total_messages * 100, 1),
            'genuine_pct': round(self._estimate_genuine_percentage(), 1),
        }

        # Generate recommendations
        recommendations = self._generate_recommendations(
            spam_ratio, engagement_quality, connection_value, breakdown
        )

        # Assign grade
        grade = self._score_to_grade(overall)

        return HealthScore(
            overall=round(overall, 1),
            spam_ratio=round(spam_ratio, 3),
            engagement_quality=round(engagement_quality, 1),
            connection_value=round(connection_value, 1),
            breakdown=breakdown,
            recommendations=recommendations,
            grade=grade,
        )

    def _calculate_spam_ratio(self) -> float:
        """Calculate ratio of spam/low-quality messages.

        Spam categories include:
        - AI-generated messages
        - Template messages
        - Fake personalization
        - Obvious sales pitches

        Returns:
            Ratio 0-1 (lower is better)
        """
        total = len(self.analyzer.messages)
        if total == 0:
            return 0

        # Count spam indicators (messages can be in multiple categories)
        spam_messages = set()

        for msg in self.analyzer.ai_generated_messages:
            spam_messages.add(msg.get('conversation_id'))

        for msg in self.analyzer.template_messages:
            spam_messages.add(msg.get('conversation_id'))

        for msg in self.analyzer.fake_personalization_messages:
            spam_messages.add(msg.get('conversation_id'))

        # Also count high-flattery messages (often manipulative)
        for msg in self.analyzer.flattery_scores:
            if msg.get('score', 0) >= 8:  # High flattery threshold
                spam_messages.add(msg.get('conversation_id'))

        return len(spam_messages) / total

    def _calculate_engagement_quality(self) -> float:
        """Calculate quality of engagement based on message patterns.

        Higher scores for:
        - Two-way conversations
        - Reasonable response rates
        - Genuine personalization

        Returns:
            Score 0-100
        """
        total = len(self.analyzer.messages)
        if total == 0:
            return 0

        score = 50  # Start at baseline

        # Bonus for conversations with responses
        conversations_with_response = len(self.analyzer.my_responses)
        if total > 0:
            response_rate = conversations_with_response / total
            score += response_rate * 30  # Up to +30 for high response rate

        # Penalty for repeat offenders (persistent unwanted contact)
        repeat_offender_ratio = len(self.analyzer.repeat_offenders) / max(total, 1)
        score -= repeat_offender_ratio * 20  # Up to -20 for many repeat offenders

        # Bonus for messages without time requests
        time_request_ratio = len(self.analyzer.time_requests) / total
        score += (1 - time_request_ratio) * 10  # Up to +10 if few time requests

        return max(0, min(100, score))

    def _calculate_connection_value(self) -> float:
        """Calculate value of connections based on who messages you.

        Higher scores for:
        - Fewer FAs, franchise consultants, MLM
        - More recruiting (potential opportunities)
        - Fewer crypto/MLM pitches

        Returns:
            Score 0-100
        """
        total = len(self.analyzer.messages)
        if total == 0:
            return 0

        score = 70  # Start with decent baseline

        # Heavy penalty for MLM/crypto (lowest quality)
        mlm_ratio = len(self.analyzer.mlm_messages) / total
        crypto_ratio = len(self.analyzer.crypto_hustler_messages) / total
        score -= (mlm_ratio + crypto_ratio) * 50  # Up to -50

        # Moderate penalty for FAs and franchise consultants
        fa_ratio = len(self.analyzer.financial_advisor_messages) / total
        franchise_ratio = len(self.analyzer.franchise_consultant_messages) / total
        score -= (fa_ratio + franchise_ratio) * 20  # Up to -20

        # Slight bonus for legitimate recruiters (potential job opportunities)
        recruiter_ratio = len(self.analyzer.recruiter_messages) / total
        if recruiter_ratio < 0.3:  # Some recruiters are fine
            score += recruiter_ratio * 10  # Up to +3
        else:
            score -= (recruiter_ratio - 0.3) * 10  # Penalty if too many

        return max(0, min(100, score))

    def _estimate_genuine_percentage(self) -> float:
        """Estimate percentage of genuine/quality messages.

        Returns:
            Percentage 0-100
        """
        total = len(self.analyzer.messages)
        if total == 0:
            return 0

        # Count likely non-genuine messages
        low_quality = set()

        for msg in self.analyzer.ai_generated_messages:
            low_quality.add(msg.get('conversation_id'))
        for msg in self.analyzer.template_messages:
            low_quality.add(msg.get('conversation_id'))
        for msg in self.analyzer.fake_personalization_messages:
            low_quality.add(msg.get('conversation_id'))
        for msg in self.analyzer.financial_advisor_messages:
            low_quality.add(msg.get('conversation_id'))
        for msg in self.analyzer.mlm_messages:
            low_quality.add(msg.get('conversation_id'))
        for msg in self.analyzer.crypto_hustler_messages:
            low_quality.add(msg.get('conversation_id'))

        genuine_count = total - len(low_quality)
        return (genuine_count / total) * 100

    def _generate_recommendations(
        self,
        spam_ratio: float,
        engagement_quality: float,
        connection_value: float,
        breakdown: dict[str, float],
    ) -> list[str]:
        """Generate actionable recommendations.

        Args:
            spam_ratio: Calculated spam ratio
            engagement_quality: Engagement score
            connection_value: Connection value score
            breakdown: Score breakdown dict

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Spam-related
        if spam_ratio > 0.5:
            recommendations.append(
                "Over 50% of messages appear automated or templated. "
                "Consider adjusting your LinkedIn visibility settings."
            )

        if breakdown.get('ai_generated_pct', 0) > 30:
            recommendations.append(
                "High volume of AI-generated messages detected. "
                "Your profile may be attracting mass outreach campaigns."
            )

        # Engagement-related
        if engagement_quality < 40:
            recommendations.append(
                "Low engagement quality. Most messages are one-way solicitations. "
                "Consider being more selective about connection requests."
            )

        if len(self.analyzer.repeat_offenders) > 10:
            recommendations.append(
                f"You have {len(self.analyzer.repeat_offenders)} repeat offenders. "
                "Consider using LinkedIn's message filtering or blocking persistent senders."
            )

        # Connection value-related
        if connection_value < 50:
            recommendations.append(
                "Low connection value score. Your network may benefit from "
                "pruning low-quality connections or adjusting who can message you."
            )

        fa_count = len(self.analyzer.financial_advisor_messages)
        if fa_count > 20:
            recommendations.append(
                f"You've received {fa_count} financial advisor messages. "
                "Consider updating your profile to be less attractive to FA outreach."
            )

        # Positive feedback if doing well
        if spam_ratio < 0.2 and engagement_quality > 70:
            recommendations.append(
                "Your inbox is healthier than most! Keep being selective "
                "about connections to maintain this quality."
            )

        if not recommendations:
            recommendations.append(
                "Your network health is reasonable. No urgent actions needed."
            )

        return recommendations

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade.

        Args:
            score: Score 0-100

        Returns:
            Letter grade string
        """
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def generate_health_report(self) -> str:
        """Generate a formatted health report.

        Returns:
            Formatted report string
        """
        health = self.calculate_health_score()

        lines = [
            "=" * 60,
            "NETWORK HEALTH SCORE",
            "=" * 60,
            "",
            f"Overall Score: {health.overall}/100 (Grade: {health.grade})",
            "",
            "COMPONENT SCORES:",
            f"   Spam-Free Score: {health.breakdown['spam_free']}/100",
            f"   Engagement Quality: {health.engagement_quality}/100",
            f"   Connection Value: {health.connection_value}/100",
            "",
            "INBOX COMPOSITION:",
            f"   Estimated Genuine Messages: {health.breakdown['genuine_pct']}%",
            f"   AI-Generated Messages: {health.breakdown['ai_generated_pct']}%",
            f"   Template Messages: {health.breakdown['template_pct']}%",
            f"   Spam Ratio: {health.spam_ratio * 100:.1f}%",
            "",
            "RECOMMENDATIONS:",
        ]

        for rec in health.recommendations:
            # Wrap long recommendations
            words = rec.split()
            current_line = "   - "
            for word in words:
                if len(current_line) + len(word) + 1 > 70:
                    lines.append(current_line)
                    current_line = "     " + word
                else:
                    current_line += (" " if current_line.strip() else "") + word
            if current_line.strip():
                lines.append(current_line)

        lines.extend(["", "=" * 60])

        return "\n".join(lines)
