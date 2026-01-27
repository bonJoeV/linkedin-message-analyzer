"""Sender Anonymization Utility.

Provides configurable anonymization of sender names for privacy.
Useful when sharing reports without exposing actual names.

Modes:
- 'initials': Use initials + unique hash (e.g., "JD-7f3a")
- 'hash': Use only hash identifier (e.g., "sender-7f3a8b2c")
- 'sequential': Use sequential IDs (e.g., "Person-001")
"""

import hashlib
from typing import Literal


AnonymizationMode = Literal['initials', 'hash', 'sequential', 'none']


class Anonymizer:
    """Anonymize sender names consistently throughout analysis."""

    def __init__(
        self,
        mode: AnonymizationMode = 'initials',
        salt: str = '',
        hash_length: int = 4,
    ):
        """Initialize the anonymizer.

        Args:
            mode: Anonymization mode
            salt: Optional salt for hash (for different anonymizations of same data)
            hash_length: Length of hash suffix (default 4 characters)
        """
        self.mode = mode
        self.salt = salt
        self.hash_length = hash_length
        self._name_map: dict[str, str] = {}
        self._sequential_counter = 0

    def anonymize(self, name: str) -> str:
        """Anonymize a sender name.

        Args:
            name: Original name

        Returns:
            Anonymized name (consistent for same input)
        """
        if self.mode == 'none' or not name:
            return name

        # Return cached result if already processed
        if name in self._name_map:
            return self._name_map[name]

        # Generate anonymized name based on mode
        if self.mode == 'initials':
            anon_name = self._anonymize_initials(name)
        elif self.mode == 'hash':
            anon_name = self._anonymize_hash(name)
        elif self.mode == 'sequential':
            anon_name = self._anonymize_sequential(name)
        else:
            anon_name = name

        self._name_map[name] = anon_name
        return anon_name

    def _get_hash(self, name: str) -> str:
        """Generate consistent hash for a name."""
        data = f"{name}{self.salt}".encode('utf-8')
        full_hash = hashlib.sha256(data).hexdigest()
        return full_hash[:self.hash_length]

    def _get_initials(self, name: str) -> str:
        """Extract initials from a name."""
        parts = name.strip().split()
        if not parts:
            return '??'

        initials = ''
        for part in parts[:3]:  # Max 3 parts
            if part:
                # Handle special cases like O'Brien, McDonald
                cleaned = ''.join(c for c in part if c.isalpha())
                if cleaned:
                    initials += cleaned[0].upper()

        return initials or '??'

    def _anonymize_initials(self, name: str) -> str:
        """Anonymize using initials + hash."""
        initials = self._get_initials(name)
        hash_suffix = self._get_hash(name)
        return f"{initials}-{hash_suffix}"

    def _anonymize_hash(self, name: str) -> str:
        """Anonymize using only hash."""
        hash_val = self._get_hash(name)
        return f"sender-{hash_val}"

    def _anonymize_sequential(self, name: str) -> str:
        """Anonymize using sequential numbers."""
        self._sequential_counter += 1
        return f"Person-{self._sequential_counter:03d}"

    def anonymize_message(self, message: dict) -> dict:
        """Anonymize sender-related fields in a message dict.

        Args:
            message: Message dictionary

        Returns:
            New dict with anonymized fields
        """
        anon_msg = message.copy()

        # Anonymize 'from' field
        if 'from' in anon_msg:
            anon_msg['from'] = self.anonymize(anon_msg['from'])

        # Anonymize conversation title if it looks like a name
        if 'conversation_title' in anon_msg:
            title = anon_msg['conversation_title']
            # Only anonymize if it looks like a person's name (not a group chat)
            if title and not any(x in title.lower() for x in ['group', 'chat', 'team']):
                anon_msg['conversation_title'] = self.anonymize(title)

        # Remove sender URL (contains real profile info)
        if 'sender_url' in anon_msg:
            anon_msg['sender_url'] = '[anonymized]'

        return anon_msg

    def get_mapping(self) -> dict[str, str]:
        """Get the name-to-anonymized mapping.

        Useful if you need to reverse lookup (kept private).

        Returns:
            Dictionary mapping original names to anonymized versions
        """
        return self._name_map.copy()

    def reset(self) -> None:
        """Reset the anonymizer state."""
        self._name_map.clear()
        self._sequential_counter = 0


# Global default instance
_default_anonymizer: Anonymizer | None = None


def get_anonymizer() -> Anonymizer | None:
    """Get the current global anonymizer instance."""
    return _default_anonymizer


def set_anonymizer(anonymizer: Anonymizer | None) -> None:
    """Set the global anonymizer instance."""
    global _default_anonymizer
    _default_anonymizer = anonymizer


def anonymize_name(name: str) -> str:
    """Anonymize a name using the global anonymizer.

    If no anonymizer is set, returns the original name.

    Args:
        name: Original name

    Returns:
        Anonymized name (or original if no anonymizer)
    """
    if _default_anonymizer:
        return _default_anonymizer.anonymize(name)
    return name
