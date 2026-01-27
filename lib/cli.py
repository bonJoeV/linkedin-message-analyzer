"""Command-line interface for LinkedIn Message Analyzer."""

import argparse
import logging
import os
import sys

# API key signup URLs for each provider
LLM_PROVIDER_URLS = {
    'openai': 'https://platform.openai.com/api-keys',
    'anthropic': 'https://console.anthropic.com/settings/keys',
    'gemini': 'https://aistudio.google.com/app/apikey',
    'groq': 'https://console.groq.com/keys',
    'mistral': 'https://console.mistral.ai/api-keys/',
    'ollama': 'https://ollama.com/download (local install, no key needed)',
}

from lib.exceptions import (
    FileLoadError,
    InvalidCSVError,
    ConfigurationError,
)
from lib.constants import DEFAULT_WEEKS_BACK
from lib.config import setup_logging, load_config
from lib.profile import UserProfile, INDUSTRY_PRESETS
from lib.llm import LLMAnalyzer
from lib.analyzer import LinkedInMessageAnalyzer
from lib.response_generator import ResponseGenerator, generate_response_for_message
from lib.reporters.html import generate_html_report
from lib.bingo import generate_bingo_card
from lib.anonymizer import Anonymizer, set_anonymizer
from lib.trend import TrendAnalyzer
from lib.health import NetworkHealthAnalyzer
from lib.reverse import ReverseAnalyzer
from lib.comparison import ComparisonAnalyzer

logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description='Analyze LinkedIn messages for time requests and outreach patterns',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s messages.csv
  %(prog)s messages.csv --my-name "John Doe" --verbose
  %(prog)s messages.csv --profile my_profile.json
  %(prog)s messages.csv --industries tech finance --llm openai
  %(prog)s messages.csv --export-json results.json --post-stats

Industry presets: tech, finance, healthcare, real_estate, consulting, sales, marketing, entrepreneur
        """
    )
    parser.add_argument(
        'messages_csv',
        nargs='?',  # Optional for --list-llm-providers
        help='Path to LinkedIn messages.csv export file'
    )
    parser.add_argument(
        '--my-name',
        help='Your name (to filter out your own messages)'
    )
    parser.add_argument(
        '--weeks',
        type=int,
        default=DEFAULT_WEEKS_BACK,
        help=f'Number of weeks to analyze (default: {DEFAULT_WEEKS_BACK})'
    )
    parser.add_argument(
        '--export-json',
        metavar='FILE',
        help='Export results to JSON file'
    )
    parser.add_argument(
        '--export-html',
        metavar='FILE',
        help='Export beautiful HTML report'
    )
    parser.add_argument(
        '--post-stats',
        action='store_true',
        help='Generate quotable stats for LinkedIn post'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose/debug logging'
    )
    parser.add_argument(
        '--log-file',
        metavar='FILE',
        help='Write logs to file'
    )
    parser.add_argument(
        '--config',
        metavar='FILE',
        help='Path to JSON config file with custom patterns (optional)'
    )

    # User profile options
    profile_group = parser.add_argument_group('User Profile Options')
    profile_group.add_argument(
        '--profile',
        metavar='FILE',
        help='Path to JSON user profile file'
    )
    profile_group.add_argument(
        '--industries',
        nargs='+',
        choices=list(INDUSTRY_PRESETS.keys()),
        help='Industry presets to use (e.g., tech finance)'
    )
    profile_group.add_argument(
        '--ignore-senders',
        nargs='+',
        metavar='NAME',
        help='Senders to ignore (e.g., colleagues)'
    )

    # LLM options
    llm_group = parser.add_argument_group('LLM Analysis Options')
    llm_group.add_argument(
        '--llm',
        choices=['openai', 'anthropic', 'ollama', 'gemini', 'groq', 'mistral'],
        help='Enable LLM-powered analysis. Providers: openai, anthropic (API key required), '
             'ollama (local, free), gemini, groq, mistral'
    )
    llm_group.add_argument(
        '--llm-model',
        metavar='MODEL',
        help='LLM model to use (each provider has sensible defaults)'
    )
    llm_group.add_argument(
        '--llm-max',
        type=int,
        default=50,
        metavar='N',
        help='Maximum messages to analyze with LLM (default: 50)'
    )
    llm_group.add_argument(
        '--llm-filter',
        choices=['time_requests', 'suspicious', 'all'],
        default='time_requests',
        help='Which messages to analyze with LLM (default: time_requests)'
    )
    llm_group.add_argument(
        '--ollama-url',
        metavar='URL',
        default='http://localhost:11434',
        help='Ollama server URL (default: http://localhost:11434)'
    )
    llm_group.add_argument(
        '--list-llm-providers',
        action='store_true',
        help='List available LLM providers and exit'
    )

    # Response generator options
    response_group = parser.add_argument_group('Response Generator Options')
    response_group.add_argument(
        '--suggest-responses',
        action='store_true',
        help='Suggest decline responses for detected solicitations'
    )
    response_group.add_argument(
        '--response-tone',
        choices=['polite', 'firm', 'sarcastic', 'honest', 'corporate'],
        default='polite',
        help='Tone for suggested responses (default: polite)'
    )
    response_group.add_argument(
        '--all-tones',
        action='store_true',
        help='Show responses in all available tones'
    )

    # Fun extras
    fun_group = parser.add_argument_group('Fun Extras')
    fun_group.add_argument(
        '--bingo',
        metavar='FILE',
        help='Generate a LinkedIn Bingo card (HTML)'
    )
    fun_group.add_argument(
        '--bingo-theme',
        choices=['recruiter', 'sales', 'ai_generated', 'flattery', 'linkedin_lunatics', 'mlm_crypto'],
        help='Theme for bingo card'
    )

    # Advanced analysis options
    analysis_group = parser.add_argument_group('Advanced Analysis')
    analysis_group.add_argument(
        '--trend',
        action='store_true',
        help='Show trend analysis over time'
    )
    analysis_group.add_argument(
        '--trend-period',
        choices=['weekly', 'monthly'],
        default='weekly',
        help='Trend aggregation period (default: weekly)'
    )
    analysis_group.add_argument(
        '--health-score',
        action='store_true',
        help='Calculate network health score'
    )
    analysis_group.add_argument(
        '--reverse',
        action='store_true',
        help='Analyze your own outreach effectiveness'
    )
    analysis_group.add_argument(
        '--compare',
        metavar='FILE',
        help='Compare with another CSV file'
    )

    # Advanced LLM features
    advanced_llm_group = parser.add_argument_group('Advanced LLM Features (requires --llm)')
    advanced_llm_group.add_argument(
        '--summarize',
        action='store_true',
        help='Summarize conversation threads with LLM'
    )
    advanced_llm_group.add_argument(
        '--summarize-max',
        type=int,
        default=20,
        metavar='N',
        help='Max senders to summarize (default: 20)'
    )
    advanced_llm_group.add_argument(
        '--smart-replies',
        action='store_true',
        help='Generate smart reply suggestions with LLM'
    )
    advanced_llm_group.add_argument(
        '--reply-tone',
        choices=['polite', 'firm', 'playful', 'deadpan', 'corporate_speak'],
        default='polite',
        help='Tone for smart replies (default: polite)'
    )
    advanced_llm_group.add_argument(
        '--cluster',
        action='store_true',
        help='Cluster similar messages to find patterns'
    )
    advanced_llm_group.add_argument(
        '--find-templates',
        action='store_true',
        help='Find messages that look like mass outreach templates'
    )

    # Web dashboard
    web_group = parser.add_argument_group('Web Dashboard')
    web_group.add_argument(
        '--web',
        action='store_true',
        help='Start local web dashboard (C64 style!)'
    )
    web_group.add_argument(
        '--web-port',
        type=int,
        default=6502,
        metavar='PORT',
        help='Port for web dashboard (default: 6502 - the MOS 6502 CPU)'
    )

    # Privacy options
    privacy_group = parser.add_argument_group('Privacy Options')
    privacy_group.add_argument(
        '--anonymize',
        choices=['initials', 'hash', 'sequential'],
        metavar='MODE',
        help='Anonymize sender names. Modes: initials (JD-7f3a), hash (sender-7f3a8b2c), sequential (Person-001)'
    )
    privacy_group.add_argument(
        '--anonymize-salt',
        metavar='STRING',
        default='',
        help='Salt for anonymization (different salt = different anonymized names)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose, log_file=args.log_file)

    # Setup anonymization if requested
    if args.anonymize:
        anonymizer = Anonymizer(
            mode=args.anonymize,
            salt=args.anonymize_salt,
        )
        set_anonymizer(anonymizer)
        logger.info(f"Anonymization enabled: mode={args.anonymize}")

    try:
        # Load custom config if provided
        if args.config:
            logger.info(f"Loading custom config from {args.config}")
            load_config(args.config)

        # Build user profile
        user_profile: UserProfile | None = None
        if args.profile:
            logger.info(f"Loading user profile from {args.profile}")
            user_profile = UserProfile.from_json_file(args.profile)
        elif args.industries or args.my_name or args.ignore_senders:
            user_profile = UserProfile(
                name=args.my_name,
                industries=args.industries or [],
                ignore_senders=args.ignore_senders or [],
            )

        # Handle --list-llm-providers
        if args.list_llm_providers:
            print("\n" + "=" * 60)
            print("AVAILABLE LLM PROVIDERS")
            print("=" * 60)
            for name, info in LLMAnalyzer.get_provider_info().items():
                print(f"\n  {name.upper()}:")
                print(f"    Model: {info['default_model']}")
                if info['requires_api_key']:
                    print(f"    Env var: {info['env_var']}")
                    url = LLM_PROVIDER_URLS.get(name, '')
                    if url:
                        print(f"    Get key: {url}")
                else:
                    print(f"    FREE - No API key required (runs locally)")
                    url = LLM_PROVIDER_URLS.get(name, '')
                    if url:
                        print(f"    Download: {url}")
                install = info['install'].replace('\n', '\n             ')
                print(f"    Install: {install}")
            print("\n" + "-" * 60)
            print("QUICK START:")
            print("-" * 60)
            print("  Free (local):  --llm ollama")
            print("  Fast & cheap:  --llm groq    (set GROQ_API_KEY)")
            print("  Best quality:  --llm anthropic (set ANTHROPIC_API_KEY)")
            print("\nExample:")
            print("  set GROQ_API_KEY=your-key-here")
            print("  python linkedin_message_analyzer.py messages.csv --llm groq --summarize")
            print()
            return 0

        # Require messages_csv for all other operations
        if not args.messages_csv:
            parser.error("messages_csv is required (use --list-llm-providers without a file)")

        # Initialize LLM analyzer if requested
        llm_analyzer: LLMAnalyzer | None = None
        if args.llm:
            # Get provider info for API key handling
            provider_info = LLMAnalyzer.get_provider_info().get(args.llm, {})
            env_var = provider_info.get('env_var', '')
            requires_key = provider_info.get('requires_api_key', True)

            api_key = os.environ.get(env_var) if env_var else None

            if requires_key and not api_key:
                url = LLM_PROVIDER_URLS.get(args.llm, '')
                print(f"\n{'=' * 60}")
                print(f"  ? API KEY NOT FOUND ERROR")
                print(f"{'=' * 60}")
                print(f"\n  Provider '{args.llm}' requires an API key.")
                print(f"\n  To fix this:")
                print(f"  1. Get your API key from: {url}")
                print(f"  2. Set the environment variable:")
                print(f"     Windows:  set {env_var}=your-key-here")
                print(f"     Linux:    export {env_var}=your-key-here")
                print(f"\n  Or use Ollama for FREE local analysis:")
                print(f"     python linkedin_message_analyzer.py messages.csv --llm ollama")
                print(f"\n  Run --list-llm-providers for all options.")
                print()
                logger.warning(f"No API key found for {args.llm}.")
            else:
                # Build provider-specific kwargs
                provider_kwargs = {}
                if args.llm == 'ollama':
                    provider_kwargs['base_url'] = args.ollama_url

                llm_analyzer = LLMAnalyzer(
                    provider=args.llm,
                    api_key=api_key,
                    model=args.llm_model,
                    **provider_kwargs,
                )

        # Create analyzer with profile and LLM
        analyzer = LinkedInMessageAnalyzer(
            args.messages_csv,
            user_profile=user_profile,
            llm_analyzer=llm_analyzer,
        )
        analyzer.load_messages()
        analyzer.run_all_analyses(my_name=args.my_name)

        # Run LLM analysis if configured
        if llm_analyzer:
            analyzer.run_llm_analysis(
                max_messages=args.llm_max,
                message_filter=args.llm_filter,
            )

        analyzer.print_report(weeks_back=args.weeks)

        # Print LLM summary if available
        if analyzer.llm_analyses:
            print(analyzer.get_llm_summary())

            # Show high priority messages
            priority_msgs = analyzer.get_high_priority_messages()
            if priority_msgs:
                print("\n" + "=" * 60)
                print("HIGH PRIORITY MESSAGES (worth responding to)")
                print("=" * 60)
                for msg in priority_msgs[:5]:
                    print(f"\n  From: {msg.get('message_from', 'Unknown')}")
                    print(f"  Intent: {msg.get('intent', 'Unknown')}")
                    print(f"  Authenticity: {msg.get('authenticity_score', '?')}/10")
                    print(f"  Summary: {msg.get('what_they_want', 'N/A')}")

        if args.post_stats:
            print(analyzer.generate_post_stats(weeks_back=args.weeks))

        if args.export_json:
            analyzer.export_to_json(args.export_json)

        if args.export_html:
            generate_html_report(analyzer, args.export_html)
            print(f"\nHTML report saved to: {args.export_html}")

        # Suggest responses if requested
        if args.suggest_responses:
            print("\n" + "=" * 60)
            print("SUGGESTED DECLINE RESPONSES")
            print("=" * 60)

            # Get message types that were detected
            message_types = []
            if analyzer.time_requests:
                message_types.append(("time_request", "Time/Meeting Requests"))
            if analyzer.financial_advisors:
                message_types.append(("financial_advisor", "Financial Advisors"))
            if analyzer.recruiters:
                message_types.append(("recruiter", "Recruiters"))
            if analyzer.sales_pitches:
                message_types.append(("sales_pitch", "Sales Pitches"))
            if hasattr(analyzer, 'ai_generated') and analyzer.ai_generated:
                message_types.append(("ai_generated", "AI-Generated Messages"))
            if hasattr(analyzer, 'franchise_messages') and analyzer.franchise_messages:
                message_types.append(("franchise", "Franchise Offers"))

            if not message_types:
                message_types = [("default", "General Solicitations")]

            for msg_type, label in message_types:
                print(f"\n  [{label}]")
                if args.all_tones:
                    all_responses = ResponseGenerator.get_all_responses(msg_type)
                    for tone, responses in all_responses.items():
                        print(f"\n    {tone.upper()}:")
                        print(f"      \"{responses[0]}\"")
                else:
                    response = ResponseGenerator.get_response(msg_type, args.response_tone)
                    print(f"    ({args.response_tone}): \"{response}\"")

            print("\n  Tip: Use --all-tones to see responses in every tone")
            print("  Tip: Use --response-tone [polite|firm|sarcastic|honest|corporate]")

        # Generate bingo card if requested
        if args.bingo:
            generate_bingo_card(args.bingo, theme=args.bingo_theme)
            print(f"\nBingo card saved to: {args.bingo}")
            print("  Open in a browser to play!")

        # Trend analysis
        if args.trend:
            trend_analyzer = TrendAnalyzer(analyzer)
            print("\n" + trend_analyzer.generate_trend_report(
                period=args.trend_period,
                weeks_back=args.weeks,
            ))

        # Health score
        if args.health_score:
            health_analyzer = NetworkHealthAnalyzer(analyzer)
            print("\n" + health_analyzer.generate_health_report())

        # Reverse mode (analyze own outreach)
        if args.reverse:
            if not args.my_name:
                print("\nWarning: --reverse requires --my-name to identify your messages")
            else:
                reverse_analyzer = ReverseAnalyzer(analyzer)
                print("\n" + reverse_analyzer.generate_reverse_report(args.my_name))

        # Comparison mode
        if args.compare:
            # Load second CSV for comparison
            compare_analyzer = LinkedInMessageAnalyzer(
                args.compare,
                user_profile=user_profile,
            )
            compare_analyzer.load_messages()
            compare_analyzer.run_all_analyses(my_name=args.my_name)

            comparison = ComparisonAnalyzer(
                analyzer, compare_analyzer,
                label_a=args.messages_csv,
                label_b=args.compare,
            )
            print("\n" + comparison.generate_comparison_report())

        # Advanced LLM features (require --llm)
        if llm_analyzer and llm_analyzer._provider:
            # Conversation summarization
            if args.summarize:
                from lib.llm_advanced import ConversationSummarizer
                summarizer = ConversationSummarizer(llm_analyzer._provider)
                summaries = summarizer.summarize_inbox(
                    analyzer.messages,
                    max_senders=args.summarize_max,
                )
                print("\n" + summarizer.generate_summary_report(summaries))

            # Smart reply generation
            if args.smart_replies:
                from lib.llm_advanced import SmartReplyGenerator
                reply_gen = SmartReplyGenerator(llm_analyzer._provider)

                # Get flagged messages to generate replies for
                flagged_msgs = []
                msg_types = []
                if analyzer.time_requests:
                    flagged_msgs.extend(analyzer.time_requests[:5])
                    msg_types.extend(['time_request'] * min(5, len(analyzer.time_requests)))
                if analyzer.financial_advisors:
                    flagged_msgs.extend(analyzer.financial_advisors[:3])
                    msg_types.extend(['financial_advisor'] * min(3, len(analyzer.financial_advisors)))
                if analyzer.sales_pitches:
                    flagged_msgs.extend(analyzer.sales_pitches[:3])
                    msg_types.extend(['sales_pitch'] * min(3, len(analyzer.sales_pitches)))

                if flagged_msgs:
                    replies = reply_gen.batch_generate(
                        flagged_msgs[:10],
                        tone=args.reply_tone,
                        message_types=msg_types[:10],
                    )
                    print("\n" + reply_gen.generate_reply_report(flagged_msgs[:10], replies))
                else:
                    print("\nNo flagged messages to generate replies for.")

            # Message clustering
            if args.cluster or args.find_templates:
                from lib.llm_advanced import MessageClusterer
                clusterer = MessageClusterer(llm_analyzer._provider)
                result = clusterer.cluster_messages(
                    analyzer.messages,
                    max_messages=args.llm_max,
                )
                print("\n" + clusterer.generate_cluster_report(result))

                if args.find_templates and result.template_clusters:
                    print("\n" + "=" * 60)
                    print("DETECTED MASS OUTREACH TEMPLATES")
                    print("=" * 60)
                    for cluster in result.template_clusters:
                        print(f"\n  Template: {cluster.label}")
                        print(f"  Used by {cluster.sender_count} different senders")
                        if cluster.common_phrases:
                            print(f"  Common phrases: {', '.join(cluster.common_phrases[:3])}")

        elif args.summarize or args.smart_replies or args.cluster or args.find_templates:
            print("\nAdvanced LLM features require --llm flag. Example:")
            print("  python linkedin_message_analyzer.py messages.csv --llm openai --summarize")

        # Web dashboard
        if args.web:
            from lib.web import run_dashboard
            run_dashboard(analyzer, port=args.web_port)
            return 0  # Dashboard blocks, so this only runs after Ctrl+C

        return 0

    except FileLoadError as e:
        logger.error(f"Failed to load file: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except InvalidCSVError as e:
        logger.error(f"Invalid CSV format: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
