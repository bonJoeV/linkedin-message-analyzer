#!/usr/bin/env python3
"""
LLM Provider Test Runner

Runs the LinkedIn Message Analyzer through each LLM provider one at a time,
with proper rate limit handling (429 backoff) and outputs to separate files.

Usage:
    python run_llm_tests.py messages.csv --keys my-keys.txt
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime


def parse_keys_file(keys_file: str) -> dict[str, str]:
    """Parse the keys file with format 'provider | key'.

    Args:
        keys_file: Path to the keys file

    Returns:
        Dict mapping provider name to API key
    """
    keys = {}
    with open(keys_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '|' in line:
                provider, key = line.split('|', 1)
                keys[provider.strip().lower()] = key.strip()
    return keys


def get_env_var_for_provider(provider: str) -> str:
    """Get the environment variable name for a provider."""
    env_vars = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'gemini': 'GOOGLE_API_KEY',
        'groq': 'GROQ_API_KEY',
        'mistral': 'MISTRAL_API_KEY',
        'ollama': None,  # No key needed
    }
    return env_vars.get(provider)


def run_analyzer(
    messages_csv: str,
    output_file: str,
    provider: str | None = None,
    api_key: str | None = None,
    max_retries: int = 5,
    initial_backoff: float = 2.0,
) -> tuple[bool, str]:
    """Run the analyzer with optional LLM provider.

    Args:
        messages_csv: Path to messages CSV
        output_file: Path for output file
        provider: LLM provider name (None for no LLM)
        api_key: API key for the provider
        max_retries: Maximum retry attempts for rate limits
        initial_backoff: Initial backoff time in seconds

    Returns:
        Tuple of (success, error_message)
    """
    # Build command
    cmd = [
        sys.executable,
        'linkedin_message_analyzer.py',
        messages_csv,
    ]

    if provider:
        cmd.extend(['--llm', provider])
        cmd.extend(['--llm-max', '10'])  # Limit for testing

    # Add analysis options to show time requests prominently
    cmd.extend(['--post-stats'])  # Include time request stats

    # Setup environment with API key
    env = os.environ.copy()
    if provider and api_key:
        env_var = get_env_var_for_provider(provider)
        if env_var:
            env[env_var] = api_key

    # Run with retry logic for rate limits
    backoff = initial_backoff
    last_error = ""

    for attempt in range(max_retries + 1):
        try:
            print(f"  Attempt {attempt + 1}/{max_retries + 1}...")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=300,  # 5 minute timeout
            )

            # Check for rate limit indicators in stderr
            stderr_lower = result.stderr.lower() if result.stderr else ""
            stdout_lower = result.stdout.lower() if result.stdout else ""
            combined = stderr_lower + stdout_lower

            # Detect rate limiting
            rate_limited = any(indicator in combined for indicator in [
                '429',
                'rate limit',
                'rate_limit',
                'too many requests',
                'quota exceeded',
                'resource exhausted',
                'overloaded',
            ])

            if rate_limited and attempt < max_retries:
                print(f"  Rate limited! Backing off for {backoff:.1f}s...")
                time.sleep(backoff)
                backoff *= 2  # Exponential backoff
                last_error = "Rate limited"
                continue

            # Write output to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"{'=' * 60}\n")
                f.write(f"LinkedIn Message Analyzer Output\n")
                f.write(f"Provider: {provider or 'None (baseline)'}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"{'=' * 60}\n\n")

                if result.stdout:
                    f.write("=== STDOUT ===\n")
                    f.write(result.stdout)
                    f.write("\n")

                if result.stderr:
                    f.write("\n=== STDERR ===\n")
                    f.write(result.stderr)

                f.write(f"\n\nExit code: {result.returncode}\n")

            if result.returncode != 0:
                return False, f"Exit code {result.returncode}"

            return True, ""

        except subprocess.TimeoutExpired:
            last_error = "Timeout (5 minutes)"
            if attempt < max_retries:
                print(f"  Timeout! Retrying in {backoff:.1f}s...")
                time.sleep(backoff)
                backoff *= 2
                continue
        except Exception as e:
            last_error = str(e)
            break

    # Write error output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"{'=' * 60}\n")
        f.write(f"ERROR - Provider: {provider or 'None (baseline)'}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"{'=' * 60}\n\n")
        f.write(f"Failed after {max_retries + 1} attempts\n")
        f.write(f"Last error: {last_error}\n")

    return False, last_error


def main():
    parser = argparse.ArgumentParser(
        description='Run LinkedIn Message Analyzer through all LLM providers'
    )
    parser.add_argument(
        'messages_csv',
        help='Path to LinkedIn messages.csv'
    )
    parser.add_argument(
        '--keys',
        default='my-keys.txt',
        help='Path to keys file (format: provider | key)'
    )
    parser.add_argument(
        '--output-dir',
        default='.',
        help='Directory for output files'
    )
    parser.add_argument(
        '--providers',
        nargs='+',
        help='Specific providers to test (default: all from keys file)'
    )
    parser.add_argument(
        '--skip-baseline',
        action='store_true',
        help='Skip the no-LLM baseline test'
    )

    args = parser.parse_args()

    # Validate inputs
    if not Path(args.messages_csv).exists():
        print(f"Error: Messages file not found: {args.messages_csv}")
        return 1

    if not Path(args.keys).exists():
        print(f"Error: Keys file not found: {args.keys}")
        return 1

    # Parse keys
    keys = parse_keys_file(args.keys)
    print(f"\nFound {len(keys)} providers in keys file: {', '.join(keys.keys())}")

    # Determine which providers to test
    if args.providers:
        providers_to_test = [p.lower() for p in args.providers]
    else:
        providers_to_test = list(keys.keys())

    # Create output directory if needed
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    # First, run baseline (no LLM)
    if not args.skip_baseline:
        print("\n" + "=" * 60)
        print("Running BASELINE (no LLM)")
        print("=" * 60)

        output_file = output_dir / "output_baseline.txt"
        success, error = run_analyzer(
            args.messages_csv,
            str(output_file),
            provider=None,
            api_key=None,
        )

        status = "OK" if success else f"FAILED: {error}"
        results.append(("baseline", success, error))
        print(f"  Result: {status}")
        print(f"  Output: {output_file}")

    # Run each provider
    for provider in providers_to_test:
        print("\n" + "=" * 60)
        print(f"Running {provider.upper()}")
        print("=" * 60)

        api_key = keys.get(provider)
        if not api_key:
            print(f"  SKIPPED: No API key found for {provider}")
            results.append((provider, False, "No API key"))
            continue

        output_file = output_dir / f"output_{provider}.txt"
        success, error = run_analyzer(
            args.messages_csv,
            str(output_file),
            provider=provider,
            api_key=api_key,
        )

        status = "OK" if success else f"FAILED: {error}"
        results.append((provider, success, error))
        print(f"  Result: {status}")
        print(f"  Output: {output_file}")

        # Small delay between providers to be nice to APIs
        if provider != providers_to_test[-1]:
            print("  Waiting 2s before next provider...")
            time.sleep(2)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for provider, success, error in results:
        status = "OK" if success else f"FAILED ({error})"
        print(f"  {provider:15} {status}")

    succeeded = sum(1 for _, s, _ in results if s)
    total = len(results)
    print(f"\n  {succeeded}/{total} providers succeeded")

    # List output files
    print("\nOutput files:")
    for provider, success, _ in results:
        output_file = output_dir / f"output_{provider}.txt"
        print(f"  {output_file}")

    return 0 if all(s for _, s, _ in results) else 1


if __name__ == '__main__':
    sys.exit(main())
