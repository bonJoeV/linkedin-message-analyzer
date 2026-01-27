"""Pattern matching system for LinkedIn Message Analyzer.

This module provides an extensible pattern matching system for detecting
various types of LinkedIn messages.

Example - Adding custom patterns:
    >>> from lib.patterns import register_pattern
    >>> register_pattern('my_category', [
    ...     r'\\bmy custom pattern\\b',
    ... ])

Example - Using pattern matchers:
    >>> from lib.patterns import PatternMatcher
    >>> matcher = PatternMatcher(['\\bhello\\b', '\\bworld\\b'])
    >>> matcher.match('hello there')
    ['\\\\bhello\\\\b']
"""

from lib.patterns.base import (
    PatternRegistry,
    PatternMatcher,
    WeightedPatternMatcher,
    get_pattern_registry,
    register_pattern,
)
from lib.patterns.time_requests import (
    TIME_REQUEST_KEYWORDS,
    TIME_ESTIMATES,
)
from lib.patterns.outreach import (
    FINANCIAL_ADVISOR_PATTERNS,
    FRANCHISE_CONSULTANT_PATTERNS,
    EXPERT_NETWORK_PATTERNS,
    ANGEL_INVESTOR_PATTERNS,
    RECRUITER_PATTERNS,
    USER_ROLES,
    PITCH_ROLE_MISMATCHES,
)
from lib.patterns.quality import (
    FAKE_PERSONALIZATION_PATTERNS,
    FLATTERY_PATTERNS,
    TEMPLATE_INDICATORS,
)
from lib.patterns.ai_generated import (
    AI_GENERATED_PATTERNS,
    AI_WEIGHTED_PATTERNS,
    AI_OPENING_PATTERNS,
    AI_BUZZWORD_PATTERNS,
)
from lib.patterns.linkedin_lunatics import (
    HUMBLEBRAG_PATTERNS,
    ENGAGEMENT_BAIT_PATTERNS,
    CRYPTO_HUSTLER_PATTERNS,
    MLM_PATTERNS,
)
from lib.patterns.sales_coaching import (
    SALES_PITCH_PATTERNS,
    COACHING_PATTERNS,
    PODCAST_PATTERNS,
    WEBINAR_PATTERNS,
    PARTNERSHIP_PATTERNS,
    COURSE_SELLER_PATTERNS,
    CONTENT_PROMO_PATTERNS,
    SALES_COACHING_ALL_PATTERNS,
    SALES_COACHING_WEIGHTED,
)

__all__ = [
    # Registry
    'PatternRegistry',
    'PatternMatcher',
    'WeightedPatternMatcher',
    'get_pattern_registry',
    'register_pattern',
    # Time requests
    'TIME_REQUEST_KEYWORDS',
    'TIME_ESTIMATES',
    # Outreach
    'FINANCIAL_ADVISOR_PATTERNS',
    'FRANCHISE_CONSULTANT_PATTERNS',
    'EXPERT_NETWORK_PATTERNS',
    'ANGEL_INVESTOR_PATTERNS',
    'RECRUITER_PATTERNS',
    'USER_ROLES',
    'PITCH_ROLE_MISMATCHES',
    # Quality
    'FAKE_PERSONALIZATION_PATTERNS',
    'FLATTERY_PATTERNS',
    'TEMPLATE_INDICATORS',
    # AI Generated
    'AI_GENERATED_PATTERNS',
    'AI_WEIGHTED_PATTERNS',
    'AI_OPENING_PATTERNS',
    'AI_BUZZWORD_PATTERNS',
    # LinkedIn Lunatics
    'HUMBLEBRAG_PATTERNS',
    'ENGAGEMENT_BAIT_PATTERNS',
    'CRYPTO_HUSTLER_PATTERNS',
    'MLM_PATTERNS',
    # Sales & Coaching
    'SALES_PITCH_PATTERNS',
    'COACHING_PATTERNS',
    'PODCAST_PATTERNS',
    'WEBINAR_PATTERNS',
    'PARTNERSHIP_PATTERNS',
    'COURSE_SELLER_PATTERNS',
    'CONTENT_PROMO_PATTERNS',
    'SALES_COACHING_ALL_PATTERNS',
    'SALES_COACHING_WEIGHTED',
]
