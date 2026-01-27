"""User profile system for personalized message analysis."""

import json
import logging
import re
from pathlib import Path
from typing import Any

from lib.exceptions import ConfigurationError
from lib.config import validate_user_profile_data

logger = logging.getLogger(__name__)


# Pre-built industry pattern sets
INDUSTRY_PRESETS: dict[str, dict[str, list[str]]] = {
    'tech': {
        'role_keywords': [
            r'\b(software|developer|engineer|architect|devops|sre|data scientist)\b',
            r'\b(product manager|pm|tech lead|cto|vp engineering)\b',
            r'\b(ai|ml|machine learning|cloud|saas|startup)\b',
        ],
        'company_keywords': [
            r'\b(google|meta|amazon|microsoft|apple|netflix|uber|airbnb)\b',
            r'\b(faang|maang|big tech)\b',
        ],
        'pitch_indicators': [
            r'\b(saas|api|sdk|platform|tool|solution)\b',
            r'\b(scale|automate|integrate|streamline)\b',
        ],
    },
    'finance': {
        'role_keywords': [
            r'\b(analyst|trader|banker|portfolio manager|cfo|finance)\b',
            r'\b(private equity|venture capital|hedge fund|investment)\b',
        ],
        'company_keywords': [
            r'\b(goldman|morgan stanley|jpmorgan|blackrock|citadel)\b',
            r'\b(sequoia|andreessen|a16z|benchmark)\b',
        ],
        'pitch_indicators': [
            r'\b(returns|alpha|portfolio|diversification|wealth)\b',
            r'\b(fund|capital|investment opportunity)\b',
        ],
    },
    'healthcare': {
        'role_keywords': [
            r'\b(doctor|physician|nurse|medical director|healthcare)\b',
            r'\b(pharma|biotech|clinical|research)\b',
        ],
        'company_keywords': [
            r'\b(pfizer|johnson|merck|abbvie|unitedhealth)\b',
        ],
        'pitch_indicators': [
            r'\b(clinical trial|fda|patient outcomes|healthcare solution)\b',
        ],
    },
    'real_estate': {
        'role_keywords': [
            r'\b(realtor|broker|property manager|real estate|investor)\b',
            r'\b(commercial|residential|development)\b',
        ],
        'company_keywords': [
            r'\b(keller williams|coldwell banker|re/max|zillow)\b',
        ],
        'pitch_indicators': [
            r'\b(property|listing|investment property|passive income)\b',
            r'\b(cap rate|roi|cash flow|appreciation)\b',
        ],
    },
    'consulting': {
        'role_keywords': [
            r'\b(consultant|partner|principal|director|manager)\b',
            r'\b(strategy|operations|management consulting)\b',
        ],
        'company_keywords': [
            r'\b(mckinsey|bain|bcg|deloitte|accenture|pwc|ey|kpmg)\b',
        ],
        'pitch_indicators': [
            r'\b(transformation|optimization|strategy|advisory)\b',
        ],
    },
    'sales': {
        'role_keywords': [
            r'\b(sales|account executive|ae|sdr|bdr|sales manager)\b',
            r'\b(business development|partnerships|revenue)\b',
        ],
        'company_keywords': [],
        'pitch_indicators': [
            r'\b(demo|trial|pricing|discount|special offer)\b',
            r'\b(quota|pipeline|close|deal)\b',
        ],
    },
    'marketing': {
        'role_keywords': [
            r'\b(marketing|cmo|brand|growth|content|social media)\b',
            r'\b(digital marketing|seo|paid media|demand gen)\b',
        ],
        'company_keywords': [],
        'pitch_indicators': [
            r'\b(campaign|engagement|conversion|roi|analytics)\b',
        ],
    },
    'entrepreneur': {
        'role_keywords': [
            r'\b(founder|ceo|owner|entrepreneur|startup)\b',
            r'\b(bootstrapped|self-funded|series [a-d])\b',
        ],
        'company_keywords': [],
        'pitch_indicators': [
            r'\b(funding|investment|advisor|mentor|accelerator)\b',
            r'\b(scale|growth|traction|product-market fit)\b',
        ],
    },
}


class UserProfile:
    """Configurable user profile for personalized message analysis."""

    def __init__(
        self,
        name: str | None = None,
        roles: list[str] | None = None,
        industries: list[str] | None = None,
        companies: list[str] | None = None,
        interests: list[str] | None = None,
        custom_role_keywords: list[str] | None = None,
        ignore_senders: list[str] | None = None,
    ) -> None:
        """Initialize a user profile.

        Args:
            name: User's name (for filtering own messages)
            roles: List of user's roles (e.g., ["Software Engineer", "Angel Investor"])
            industries: List of industries to use presets from (e.g., ["tech", "finance"])
            companies: Companies the user is associated with
            interests: Topics the user is interested in
            custom_role_keywords: Additional regex patterns for role detection
            ignore_senders: Senders to always ignore (e.g., colleagues)
        """
        self.name = name
        self.roles = roles or []
        self.industries = industries or []
        self.companies = companies or []
        self.interests = interests or []
        self.custom_role_keywords = custom_role_keywords or []
        self.ignore_senders = ignore_senders or []

        # Build combined patterns from industries
        self._role_patterns: list[str] = []
        self._company_patterns: list[str] = []
        self._pitch_patterns: list[str] = []
        self._build_patterns()

    def _build_patterns(self) -> None:
        """Build combined regex patterns from selected industries."""
        for industry in self.industries:
            if industry in INDUSTRY_PRESETS:
                preset = INDUSTRY_PRESETS[industry]
                self._role_patterns.extend(preset.get('role_keywords', []))
                self._company_patterns.extend(preset.get('company_keywords', []))
                self._pitch_patterns.extend(preset.get('pitch_indicators', []))

        # Add custom patterns
        self._role_patterns.extend(self.custom_role_keywords)

        # Add company names as patterns
        for company in self.companies:
            self._company_patterns.append(rf'\b{re.escape(company)}\b')

        logger.debug(f"Built {len(self._role_patterns)} role patterns, "
                     f"{len(self._company_patterns)} company patterns, "
                     f"{len(self._pitch_patterns)} pitch patterns")

    def should_ignore_sender(self, sender: str) -> bool:
        """Check if a sender should be ignored."""
        sender_lower = sender.lower()
        for ignore in self.ignore_senders:
            if ignore.lower() in sender_lower:
                return True
        return False

    def get_role_patterns(self) -> list[str]:
        """Get all role-related patterns."""
        return self._role_patterns

    def get_pitch_patterns(self) -> list[str]:
        """Get all pitch indicator patterns."""
        return self._pitch_patterns

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'UserProfile':
        """Create a UserProfile from a dictionary (e.g., from JSON config).

        Args:
            data: Dictionary containing profile data

        Returns:
            UserProfile instance

        Raises:
            ConfigurationError: If validation fails
        """
        validate_user_profile_data(data)

        # Validate industries against available presets
        industries = data.get('industries', [])
        if industries:
            invalid = [i for i in industries if i not in INDUSTRY_PRESETS]
            if invalid:
                valid_industries = ', '.join(INDUSTRY_PRESETS.keys())
                raise ConfigurationError(
                    f"Invalid industries: {', '.join(invalid)}. "
                    f"Valid options: {valid_industries}"
                )

        return cls(
            name=data.get('name'),
            roles=data.get('roles'),
            industries=industries,
            companies=data.get('companies'),
            interests=data.get('interests'),
            custom_role_keywords=data.get('custom_role_keywords'),
            ignore_senders=data.get('ignore_senders'),
        )

    @classmethod
    def from_json_file(cls, path: str | Path) -> 'UserProfile':
        """Load a UserProfile from a JSON file.

        Args:
            path: Path to the JSON file

        Returns:
            UserProfile instance

        Raises:
            ConfigurationError: If the file is invalid or validation fails
            FileNotFoundError: If the file doesn't exist
        """
        file_path = Path(path)
        if not file_path.exists():
            raise ConfigurationError(f"Profile file not found: {path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in profile file: {e}")

        profile_data = data.get('user_profile', data)
        return cls.from_dict(profile_data)
