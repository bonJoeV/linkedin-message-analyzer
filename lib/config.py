"""Configuration and logging setup for LinkedIn Message Analyzer."""

import json
import logging
import sys
from pathlib import Path
from typing import Any

from lib.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


LLM_FILTER_CHOICES = {'time_requests', 'suspicious', 'all'}


def setup_logging(verbose: bool = False, log_file: str | None = None) -> None:
    """Configure logging for the application.

    Args:
        verbose: Enable debug-level logging
        log_file: Optional path to log file
    """
    level = logging.DEBUG if verbose else logging.INFO

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def _validate_string_list(data: Any, field_name: str) -> list[str] | None:
    """Validate that a field is a list of strings or None.

    Args:
        data: The data to validate
        field_name: Name of the field (for error messages)

    Returns:
        The validated list or None

    Raises:
        ConfigurationError: If validation fails
    """
    if data is None:
        return None
    if not isinstance(data, list):
        raise ConfigurationError(f"'{field_name}' must be a list, got {type(data).__name__}")
    result: list[str] = []
    for i, item in enumerate(data):
        if not isinstance(item, str):
            raise ConfigurationError(
                f"'{field_name}[{i}]' must be a string, got {type(item).__name__}"
            )
        result.append(item)
    return result


def _validate_weighted_pattern_list(
    data: Any,
    field_name: str,
) -> list[tuple[str, int]] | None:
    """Validate weighted patterns as strings or [pattern, weight] entries."""
    if data is None:
        return None
    if not isinstance(data, list):
        raise ConfigurationError(f"'{field_name}' must be a list, got {type(data).__name__}")

    result: list[tuple[str, int]] = []
    for i, item in enumerate(data):
        if isinstance(item, str):
            result.append((item, 1))
            continue

        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ConfigurationError(
                f"'{field_name}[{i}]' must be a string or [pattern, weight] pair"
            )

        pattern, weight = item
        if not isinstance(pattern, str):
            raise ConfigurationError(
                f"'{field_name}[{i}][0]' must be a string, got {type(pattern).__name__}"
            )
        if not isinstance(weight, int):
            raise ConfigurationError(
                f"'{field_name}[{i}][1]' must be an integer, got {type(weight).__name__}"
            )
        result.append((pattern, weight))

    return result


def validate_llm_config_data(data: Any) -> dict[str, Any]:
    """Validate and normalize LLM config settings."""
    from lib.llm.base import ProviderRegistry
    import lib.llm.providers  # noqa: F401

    if not isinstance(data, dict):
        raise ConfigurationError(f"'llm' must be a dictionary, got {type(data).__name__}")

    normalized = dict(data)
    provider = normalized.get('provider')
    if provider is not None:
        if not isinstance(provider, str):
            raise ConfigurationError(f"'llm.provider' must be a string, got {type(provider).__name__}")
        provider = provider.lower()
        if not ProviderRegistry.is_registered(provider):
            valid = ', '.join(ProviderRegistry.list_providers())
            raise ConfigurationError(
                f"Invalid llm.provider: {provider}. Valid options: {valid}"
            )
        normalized['provider'] = provider

    model = normalized.get('model')
    if model is not None and not isinstance(model, str):
        raise ConfigurationError(f"'llm.model' must be a string, got {type(model).__name__}")

    max_messages = normalized.get('max_messages')
    if max_messages is not None:
        if not isinstance(max_messages, int) or max_messages <= 0:
            raise ConfigurationError("'llm.max_messages' must be a positive integer")

    message_filter = normalized.get('filter')
    if message_filter is not None:
        if not isinstance(message_filter, str):
            raise ConfigurationError(
                f"'llm.filter' must be a string, got {type(message_filter).__name__}"
            )
        if message_filter not in LLM_FILTER_CHOICES:
            raise ConfigurationError(
                f"Invalid llm.filter: {message_filter}. "
                f"Valid options: {', '.join(sorted(LLM_FILTER_CHOICES))}"
            )

    provider_options = normalized.get('provider_options', {})
    if provider_options is None:
        provider_options = {}
    if not isinstance(provider_options, dict):
        raise ConfigurationError(
            f"'llm.provider_options' must be a dictionary, got {type(provider_options).__name__}"
        )

    for key, value in provider_options.items():
        if not isinstance(key, str):
            raise ConfigurationError("'llm.provider_options' keys must be strings")
        if not isinstance(value, (str, int, float, bool)):
            raise ConfigurationError(
                f"'llm.provider_options.{key}' must be a scalar value, got {type(value).__name__}"
            )

    ollama_url = normalized.get('ollama_url')
    if ollama_url is not None:
        if not isinstance(ollama_url, str):
            raise ConfigurationError(
                f"'llm.ollama_url' must be a string, got {type(ollama_url).__name__}"
            )
        provider_options = dict(provider_options)
        provider_options.setdefault('base_url', ollama_url)

    normalized['provider_options'] = provider_options
    return normalized


def validate_user_profile_data(data: Any) -> None:
    """Validate user profile data structure.

    Args:
        data: Dictionary containing user profile data

    Raises:
        ConfigurationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ConfigurationError(f"Profile data must be a dictionary, got {type(data).__name__}")

    # Validate optional string field
    if 'name' in data and data['name'] is not None:
        if not isinstance(data['name'], str):
            raise ConfigurationError(
                f"'name' must be a string, got {type(data['name']).__name__}"
            )

    # Validate optional list[str] fields
    list_fields = ['roles', 'industries', 'companies', 'interests',
                   'custom_role_keywords', 'ignore_senders']
    for field in list_fields:
        if field in data:
            _validate_string_list(data[field], field)


def validate_config_data(data: Any) -> None:
    """Validate configuration file data structure.

    Args:
        data: Dictionary containing configuration data

    Raises:
        ConfigurationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ConfigurationError(f"Config data must be a dictionary, got {type(data).__name__}")

    pattern_fields = [
        'time_request_keywords', 'financial_advisor_patterns',
        'franchise_consultant_patterns', 'expert_network_patterns',
        'angel_investor_patterns', 'recruiter_patterns',
        'fake_personalization_patterns',
    ]

    for field in pattern_fields:
        if field in data:
            _validate_string_list(data[field], field)

    if 'flattery_patterns' in data:
        _validate_weighted_pattern_list(data['flattery_patterns'], 'flattery_patterns')

    if 'user_profile' in data:
        validate_user_profile_data(data['user_profile'])

    if 'llm' in data:
        validate_llm_config_data(data['llm'])


def load_config(config_path: str) -> dict[str, Any]:
    """Load custom patterns from a JSON config file.

    Args:
        config_path: Path to the JSON config file

    Returns:
        Dictionary containing the loaded configuration

    Raises:
        ConfigurationError: If the config file is invalid
    """
    from lib.patterns import get_pattern_registry

    config_file = Path(config_path)
    if not config_file.exists():
        raise ConfigurationError(f"Config file not found: {config_path}")

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in config file: {e}")

    # Validate config structure
    validate_config_data(config)

    # Update pattern registry from config
    registry = get_pattern_registry()

    pattern_mapping = {
        'time_request_keywords': 'time_requests',
        'financial_advisor_patterns': 'financial_advisor',
        'franchise_consultant_patterns': 'franchise_consultant',
        'expert_network_patterns': 'expert_network',
        'angel_investor_patterns': 'angel_investor',
        'recruiter_patterns': 'recruiter',
        'fake_personalization_patterns': 'fake_personalization',
        'flattery_patterns': 'flattery',
    }

    weighted_patterns = _validate_weighted_pattern_list(
        config.get('flattery_patterns'),
        'flattery_patterns',
    )

    for config_key, registry_key in pattern_mapping.items():
        if config_key in config:
            if registry_key == 'flattery' and weighted_patterns is not None:
                registry.register_weighted(registry_key, weighted_patterns)
            else:
                registry.register(registry_key, config[config_key])
            logger.debug(f"Loaded {len(config[config_key])} patterns for {registry_key} from config")

    if 'llm' in config:
        config['llm'] = validate_llm_config_data(config['llm'])

    logger.info(f"Loaded custom patterns from {config_path}")
    return config
