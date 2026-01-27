#!/usr/bin/env python3
"""
LinkedIn Message Sample Generator

Generates realistic fake LinkedIn messages for testing the analyzer.
Perfect for demos, testing, and not exposing your actual inbox.

Usage:
    python generate_samples.py --role tech --count 100 --output sample_messages.csv
    python generate_samples.py --role executive --count 200 --chaos-mode
"""

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# =============================================================================
# NAME GENERATORS
# =============================================================================

FIRST_NAMES = [
    "Chad", "Brad", "Tad", "Hunter", "Tyler", "Kyle", "Brock", "Blake", "Chase",
    "Jessica", "Ashley", "Brittany", "Megan", "Lauren", "Samantha", "Nicole",
    "Michael", "David", "James", "Robert", "Jennifer", "Sarah", "Emily", "Rachel",
    "Aiden", "Jayden", "Brayden", "Kayden", "Zayden",  # The -ayden family
    "Rajesh", "Priya", "Wei", "Chen", "Yuki", "Sanjay", "Amit", "Neha",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis",
    "Patel", "Singh", "Kumar", "Shah", "Gupta", "Chen", "Wang", "Liu",
    "O'Brien", "McCarthy", "Sullivan", "Murphy", "Kelly", "Walsh",
    "Goldstein", "Rosenberg", "Cohen", "Shapiro", "Levine",
]

COMPANY_SUFFIXES = ["Solutions", "Partners", "Group", "Consulting", "Advisory", "Capital", "Ventures"]

def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def random_company():
    prefix = random.choice(["Apex", "Summit", "Pinnacle", "Elite", "Prime", "Quantum", "Synergy", "Nexus", "Vertex", "Horizon"])
    suffix = random.choice(COMPANY_SUFFIXES)
    return f"{prefix} {suffix}"

# =============================================================================
# MESSAGE TEMPLATES BY CATEGORY
# =============================================================================

TIME_REQUEST_TEMPLATES = [
    "Hi {name}! I'd love to grab a quick coffee and pick your brain about {topic}. Would you have 15 minutes this week?",
    "Hey {name}, I noticed we're both in {industry}. Would love to connect and learn from your experience. Quick 15-min call?",
    "Hi {name}! I've been following your work and would love to schedule a brief call to discuss potential synergies. How's your calendar looking?",
    "{name}, I'm reaching out because I believe we could have a mutually beneficial conversation. Do you have 30 minutes for a quick Zoom?",
    "Would love to pick your brain about {topic}! Coffee's on me if you're in {city}. Otherwise, happy to do a quick call.",
    "Hi {name}! I know you're busy, but I'd really appreciate just 15 minutes of your time to discuss {topic}. I promise to keep it brief!",
    "I've been admiring your journey in {industry} and would love to connect. Do you have time for a quick chat this week?",
    "Hey! Fellow {role} here. Would love to network and share experiences. Quick virtual coffee sometime?",
]

FINANCIAL_ADVISOR_TEMPLATES = [
    "Hi {name}, as a {role} at {company}, you likely have unique financial planning needs. I specialize in helping professionals like you optimize their wealth strategy. Quick call?",
    "Congratulations on your success at {company}! Have you considered how to protect and grow your wealth? I help {industry} professionals with comprehensive financial planning.",
    "Hi {name}, I noticed you're at {company}. Many of your colleagues have been working with me on their RSU strategies and 401k optimization. Would love to connect!",
    "{name}, as a Certified Financial Planner specializing in tech executives, I've helped many people in your position. 15 minutes could save you thousands in taxes.",
    "I help {industry} professionals like yourself navigate complex compensation packages. Your stock options and RSUs deserve expert attention. Free consultation?",
    "Hi {name}! Your profile shows impressive career growth. Have you thought about retirement planning? I've helped 50+ {role}s at companies like {company}.",
    "With market volatility, now's the time to review your portfolio. I specialize in {industry} executives and offer complimentary reviews.",
]

FRANCHISE_CONSULTANT_TEMPLATES = [
    "Hi {name}! With your background in {industry}, you'd make an excellent franchise owner. Have you ever considered being your own boss?",
    "Tired of the corporate grind? I help successful professionals like you explore franchise ownership. Semi-absentee models available!",
    "{name}, many {role}s are diversifying their income through franchise ownership. I'd love to share some opportunities that might interest you.",
    "Hi! I'm a franchise consultant and I think your {industry} experience would translate perfectly to business ownership. Quick call to explore?",
    "Ready to take control of your future? Franchise ownership could be your path to financial freedom. I work exclusively with high-caliber professionals like yourself.",
    "The corporate world is unpredictable. Have you considered building something of your own? I help {role}s transition to franchise ownership.",
    "Hi {name}! Given recent tech layoffs, many professionals are exploring franchise opportunities. Would you be open to learning more?",
]

RECRUITER_TEMPLATES = [
    "Hi {name}! I have an AMAZING opportunity at a well-funded startup. Your background is a PERFECT fit. Quick call?",
    "{name}, I came across your profile and immediately thought of a {role} position I'm filling at a Fortune 500. Interested?",
    "Hi! I'm recruiting for a {role} role at an exciting company (can't say who yet, but it's BIG). Your experience is exactly what they need!",
    "Your profile stood out to me! I have a fantastic opportunity - fully remote, great comp, equity. Are you open to new opportunities?",
    "Hi {name}! Are you happy in your current role? I have something that might interest you. No pressure, just a quick exploratory chat?",
    "{name}, I'll cut to the chase - I have a {role} opportunity that pays $50k more than your current market rate. 10 minutes?",
    "URGENT: Looking for a {role} for a hot startup. Your background is exactly what my client needs. Can we talk TODAY?",
]

EXPERT_NETWORK_TEMPLATES = [
    "Hi {name}, I'm reaching out from GLG. We have a client interested in your expertise in {topic}. Paid consultation, 1 hour, $500+/hr.",
    "Guidepoint here. A hedge fund client would like to speak with someone with your background in {industry}. Are you available for a paid call?",
    "Hi! I'm from AlphaSights. We're looking for experts in {topic} for a paid consultation. Would you be interested in a 45-60 minute call at competitive rates?",
    "{name}, Third Bridge here. Your experience at {company} would be valuable for one of our clients. $400-600/hr for your time. Interested?",
    "I'm reaching out from Tegus regarding a paid expert consultation in {industry}. Our clients value perspectives from professionals like yourself.",
]

AI_GENERATED_TEMPLATES = [
    "I hope this message finds you well! I wanted to reach out because I came across your profile and was genuinely impressed by your background. I believe there could be some synergy between our work.",
    "I hope this email finds you in good spirits! I've been following your journey in {industry} and I'm truly inspired by your achievements. I wanted to connect and explore potential opportunities for collaboration.",
    "I trust this message reaches you at a good time. I'm reaching out because I believe, in today's fast-paced business environment, networking with thought leaders like yourself is invaluable.",
    "I hope you don't mind me reaching out! Your profile really resonated with me, and I felt compelled to connect. I think we could have a mutually beneficial conversation.",
    "Greetings! I came across your impressive profile and couldn't help but reach out. Your experience in {industry} is truly remarkable, and I believe we share similar professional values.",
    "I wanted to reach out and connect with you because I believe, going forward, there could be some exciting synergies between our respective areas of expertise.",
]

CRYPTO_TEMPLATES = [
    "Hey {name}! Have you looked into Web3? I'm building something revolutionary in the blockchain space. Would love to get your thoughts as a fellow {industry} professional.",
    "GM {name}! I noticed you're in {industry}. We're launching a token that's going to disrupt the entire space. Early investors are seeing 10x returns. WAGMI!",
    "Hi! I'm building a decentralized platform for {industry}. We're doing a seed round and looking for advisors with your background. Interested in getting in on the ground floor?",
    "{name}, the future is Web3. I'm helping {industry} professionals transition into blockchain. Have you considered diversifying into crypto?",
    "Hey! Fellow innovator here. I'm working on an NFT project that could revolutionize {industry}. Would love to connect and share the vision! Diamond hands!",
]

MLM_TEMPLATES = [
    "Hi {name}! I've discovered an incredible opportunity that's transformed my life. I'm now earning passive income from home while spending more time with family. DM me to learn more!",
    "Hey! I noticed you're a {role}. Have you ever thought about building a side income? I've helped dozens of professionals like you achieve financial freedom.",
    "{name}, I used to work 60-hour weeks too. Now I make more working 10 hours from my phone. Curious? I only share this with serious people.",
    "Hi! You seem like someone who's ambitious and driven. I'm building a team of high-performers and think you'd be a perfect fit. No experience needed!",
    "Quick question - are you open to earning extra income without leaving your current job? I have something that might interest you. Serious inquiries only.",
]

SALES_PITCH_TEMPLATES = [
    "Hi {name}! I see you're a {role} at {company}. We help companies like yours increase productivity by 47%. Quick demo?",
    "{name}, I noticed {company} is growing fast. Our platform helps scale teams without the growing pains. 15 minutes for a quick overview?",
    "Hi! Companies like {company} are saving $500k/year with our solution. I'd love to show you how. Free trial included!",
    "Hey {name}! Are you the right person to talk to about {topic} at {company}? If not, who should I reach out to?",
    "{name}, I'll be honest - I'm in sales, but I genuinely think our product could help {company}. 10 minutes to see if there's a fit?",
    "Hi! I've helped 3 other {role}s at companies like {company} this month. They're seeing amazing results. Quick call to see if it makes sense for you?",
]

PODCAST_TEMPLATES = [
    "Hi {name}! I host a podcast about {industry} and would love to have you as a guest. Your story is inspiring and I think my audience of 50,000 would love to hear it!",
    "{name}, I'm launching a new podcast focused on {topic}. Given your experience, you'd be a perfect guest! It's just a 30-minute casual conversation.",
    "Hi! I run a YouTube channel about {industry} success stories. Would you be interested in being featured? Great exposure for your personal brand!",
    "Hey {name}! I'm building a content series featuring {role}s who've achieved success in {industry}. Quick interview for my blog?",
]

COACHING_TEMPLATES = [
    "Hi {name}! As a certified life coach, I help {role}s like you unlock their full potential. Ready to 10x your success?",
    "{name}, I've helped 200+ {industry} professionals achieve breakthrough results. What's holding you back from your next level?",
    "Hi! I noticed you're a {role}. My 6-week executive coaching program has helped leaders like you increase their impact 3x. Interested in a discovery call?",
    "Hey {name}! Are you where you thought you'd be at this point in your career? I help ambitious professionals bridge the gap between where they are and where they want to be.",
]

FLATTERY_HEAVY_TEMPLATES = [
    "WOW {name}!! I've been following your INCREDIBLE journey and I'm SO inspired by what you've accomplished! You're absolutely CRUSHING IT! Would love to connect!",
    "Hi {name}!! Your profile is AMAZING! I love what you're doing at {company}! You're a true thought leader and innovator! Let's definitely connect!!!",
    "{name}!!! Just had to reach out because your content is PHENOMENAL! You're seriously one of the most impressive people I've come across on LinkedIn! Coffee?",
    "OMG {name}! Your career trajectory is INSANE! From {topic} to {role}?! That's so impressive!! I'd LOVE to learn from you!!!",
]

TEMPLATE_FAIL_TEMPLATES = [
    "Hi {{first_name}}, I noticed your work at {{company}} and thought we should connect!",
    "Hi [Name], as a [Job Title] at [Company], you might be interested in...",
    "Dear {firstName}, I hope this message finds you well. I wanted to reach out about...",
    "Hi FNAME, I came across your profile and was impressed by your experience at COMPANY.",
]

# =============================================================================
# ROLE-SPECIFIC MESSAGE DISTRIBUTIONS
# =============================================================================

ROLE_CONFIGS = {
    "tech": {
        "job_titles": ["Software Engineer", "Senior Engineer", "Staff Engineer", "Engineering Manager", "Tech Lead", "Principal Engineer", "CTO", "VP Engineering"],
        "industries": ["tech", "SaaS", "AI/ML", "cloud computing", "fintech"],
        "topics": ["engineering leadership", "system design", "scaling teams", "AI adoption", "cloud architecture"],
        "companies": ["Google", "Meta", "Amazon", "Microsoft", "Apple", "Netflix", "Uber", "Airbnb", "Stripe", "OpenAI"],
        "message_weights": {
            "time_request": 20,
            "recruiter": 25,
            "financial_advisor": 15,
            "expert_network": 10,
            "sales_pitch": 10,
            "ai_generated": 8,
            "coaching": 5,
            "crypto": 4,
            "podcast": 3,
        },
    },
    "executive": {
        "job_titles": ["CEO", "CTO", "CFO", "COO", "VP", "Director", "C-Suite Executive", "Founder"],
        "industries": ["enterprise", "technology", "finance", "healthcare", "consulting"],
        "topics": ["leadership", "strategy", "scaling", "M&A", "board governance"],
        "companies": ["Fortune 500", "Series C startup", "PE-backed company", "public company"],
        "message_weights": {
            "time_request": 15,
            "financial_advisor": 20,
            "franchise": 10,
            "recruiter": 15,
            "expert_network": 15,
            "sales_pitch": 8,
            "coaching": 8,
            "podcast": 5,
            "ai_generated": 4,
        },
    },
    "sales": {
        "job_titles": ["Account Executive", "Sales Manager", "VP Sales", "SDR", "BDR", "Sales Director", "CRO"],
        "industries": ["SaaS", "enterprise software", "tech sales", "B2B"],
        "topics": ["sales strategy", "quota crushing", "pipeline management", "enterprise deals"],
        "companies": ["Salesforce", "HubSpot", "Outreach", "Gong", "ZoomInfo"],
        "message_weights": {
            "recruiter": 30,
            "time_request": 20,
            "coaching": 15,
            "sales_pitch": 15,  # Meta: salespeople getting sold to
            "mlm": 8,
            "ai_generated": 7,
            "podcast": 5,
        },
    },
    "finance": {
        "job_titles": ["Analyst", "Associate", "VP", "Director", "Managing Director", "Portfolio Manager", "Trader"],
        "industries": ["investment banking", "private equity", "hedge funds", "asset management", "venture capital"],
        "topics": ["deal flow", "portfolio strategy", "market trends", "alternative investments"],
        "companies": ["Goldman Sachs", "Morgan Stanley", "Blackstone", "KKR", "Citadel", "Bridgewater"],
        "message_weights": {
            "time_request": 15,
            "recruiter": 20,
            "expert_network": 20,
            "crypto": 15,
            "sales_pitch": 10,
            "ai_generated": 10,
            "podcast": 5,
            "coaching": 5,
        },
    },
    "founder": {
        "job_titles": ["Founder", "Co-Founder", "CEO", "Entrepreneur", "Solo Founder"],
        "industries": ["startups", "tech", "SaaS", "consumer", "marketplace"],
        "topics": ["fundraising", "product-market fit", "scaling", "hiring", "founder journey"],
        "companies": ["YC startup", "bootstrapped company", "Series A company", "pre-seed startup"],
        "message_weights": {
            "financial_advisor": 20,
            "time_request": 20,
            "franchise": 15,
            "sales_pitch": 15,
            "coaching": 10,
            "crypto": 8,
            "podcast": 7,
            "mlm": 5,
        },
    },
    "influencer": {
        "job_titles": ["Content Creator", "Thought Leader", "Author", "Speaker", "LinkedIn Top Voice"],
        "industries": ["personal branding", "content", "marketing", "coaching"],
        "topics": ["content strategy", "personal brand", "audience building", "monetization"],
        "companies": ["Self-employed", "Consulting", "Speaking circuit"],
        "message_weights": {
            "flattery": 25,
            "time_request": 20,
            "podcast": 20,
            "sales_pitch": 15,
            "coaching": 10,
            "mlm": 5,
            "ai_generated": 5,
        },
    },
}

# =============================================================================
# MESSAGE GENERATOR
# =============================================================================

class LinkedInMessageGenerator:
    def __init__(self, role: str = "tech", chaos_mode: bool = False):
        self.role = role
        self.chaos_mode = chaos_mode
        self.config = ROLE_CONFIGS.get(role, ROLE_CONFIGS["tech"])

    def _fill_template(self, template: str) -> str:
        """Fill in template variables."""
        replacements = {
            "{name}": random_name().split()[0],  # Just first name
            "{role}": random.choice(self.config["job_titles"]),
            "{company}": random.choice(self.config["companies"]),
            "{industry}": random.choice(self.config["industries"]),
            "{topic}": random.choice(self.config["topics"]),
            "{city}": random.choice(["San Francisco", "New York", "Austin", "Seattle", "Boston", "Denver", "LA"]),
        }
        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)
        return result

    def _get_template_for_category(self, category: str) -> str:
        """Get a random template for a category."""
        templates = {
            "time_request": TIME_REQUEST_TEMPLATES,
            "financial_advisor": FINANCIAL_ADVISOR_TEMPLATES,
            "franchise": FRANCHISE_CONSULTANT_TEMPLATES,
            "recruiter": RECRUITER_TEMPLATES,
            "expert_network": EXPERT_NETWORK_TEMPLATES,
            "ai_generated": AI_GENERATED_TEMPLATES,
            "crypto": CRYPTO_TEMPLATES,
            "mlm": MLM_TEMPLATES,
            "sales_pitch": SALES_PITCH_TEMPLATES,
            "podcast": PODCAST_TEMPLATES,
            "coaching": COACHING_TEMPLATES,
            "flattery": FLATTERY_HEAVY_TEMPLATES,
            "template_fail": TEMPLATE_FAIL_TEMPLATES,
        }
        return random.choice(templates.get(category, TIME_REQUEST_TEMPLATES))

    def _select_category(self) -> str:
        """Select a message category based on weights."""
        weights = self.config["message_weights"]
        categories = list(weights.keys())
        weight_values = list(weights.values())

        # In chaos mode, add some extra spicy categories
        if self.chaos_mode:
            categories.extend(["template_fail", "flattery"])
            weight_values.extend([10, 10])

        return random.choices(categories, weights=weight_values)[0]

    def generate_message(self) -> dict:
        """Generate a single message."""
        category = self._select_category()
        template = self._get_template_for_category(category)
        content = self._fill_template(template)

        # Generate sender info
        sender_name = random_name()

        # Random date in the last 90 days
        days_ago = random.randint(0, 90)
        hours_ago = random.randint(0, 23)
        msg_date = datetime.now() - timedelta(days=days_ago, hours=hours_ago)

        # Chaos mode: sometimes send at weird hours
        if self.chaos_mode and random.random() < 0.2:
            msg_date = msg_date.replace(hour=random.choice([2, 3, 4, 5, 23, 0, 1]))

        return {
            "CONVERSATION ID": f"conv_{random.randint(10000000, 99999999)}",
            "CONVERSATION TITLE": sender_name,
            "FROM": sender_name,
            "SENDER PROFILE URL": f"https://www.linkedin.com/in/{sender_name.lower().replace(' ', '-')}-{random.randint(1000, 9999)}",
            "TO": "You",
            "DATE": msg_date.strftime("%Y-%m-%d %H:%M:%S"),
            "SUBJECT": "",
            "CONTENT": content,
            "FOLDER": "INBOX",
            "_CATEGORY": category,  # Hidden field for reference
        }

    def generate_messages(self, count: int) -> list:
        """Generate multiple messages."""
        messages = []
        for _ in range(count):
            messages.append(self.generate_message())

        # Sort by date
        messages.sort(key=lambda x: x["DATE"], reverse=True)
        return messages

    def add_repeat_offenders(self, messages: list, num_offenders: int = 5) -> list:
        """Add some repeat offenders who message multiple times."""
        offender_names = [random_name() for _ in range(num_offenders)]

        for name in offender_names:
            # Each offender sends 2-5 messages
            num_messages = random.randint(2, 5)
            for i in range(num_messages):
                msg = self.generate_message()
                msg["FROM"] = name
                msg["CONVERSATION TITLE"] = name
                msg["SENDER PROFILE URL"] = f"https://www.linkedin.com/in/{name.lower().replace(' ', '-')}"

                # Follow-up messages reference previous attempts
                if i > 0:
                    followups = [
                        f"Hi again! Just following up on my previous message...",
                        f"Hey! Not sure if you saw my earlier message. Just wanted to bump this up!",
                        f"Following up! I know you're busy but I really think this would be valuable for you.",
                        f"Hi! Just checking if you had a chance to see my message? Would love to connect!",
                        f"Bumping this to the top of your inbox!",
                    ]
                    msg["CONTENT"] = random.choice(followups)

                messages.append(msg)

        messages.sort(key=lambda x: x["DATE"], reverse=True)
        return messages


def main():
    parser = argparse.ArgumentParser(
        description="Generate sample LinkedIn messages for testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python generate_samples.py --role tech --count 100
    python generate_samples.py --role executive --count 200 --chaos-mode
    python generate_samples.py --role founder --count 150 --output my_samples.csv

Available roles: tech, executive, sales, finance, founder, influencer
        """
    )
    parser.add_argument("--role", choices=list(ROLE_CONFIGS.keys()), default="tech",
                        help="Your role/persona (affects message distribution)")
    parser.add_argument("--count", type=int, default=100,
                        help="Number of messages to generate")
    parser.add_argument("--output", default="sample_messages.csv",
                        help="Output CSV filename")
    parser.add_argument("--chaos-mode", action="store_true",
                        help="Add extra chaos: template fails, weird hours, more variety")
    parser.add_argument("--repeat-offenders", type=int, default=5,
                        help="Number of repeat offenders to add")
    parser.add_argument("--generate-all", action="store_true",
                        help="Generate sample files for ALL roles")

    args = parser.parse_args()

    # Generate all samples if requested
    if args.generate_all:
        generate_all_samples(count=args.count)
        return

    generator = LinkedInMessageGenerator(role=args.role, chaos_mode=args.chaos_mode)
    messages = generator.generate_messages(args.count)
    messages = generator.add_repeat_offenders(messages, args.repeat_offenders)

    # Write to CSV
    output_path = Path(__file__).parent / args.output
    fieldnames = ["CONVERSATION ID", "CONVERSATION TITLE", "FROM", "SENDER PROFILE URL",
                  "TO", "DATE", "SUBJECT", "CONTENT", "FOLDER"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(messages)

    print(f"Generated {len(messages)} messages to {output_path}")
    print(f"\nMessage distribution:")

    # Count categories
    from collections import Counter
    categories = Counter(m.get("_CATEGORY", "unknown") for m in messages)
    for cat, count in categories.most_common():
        print(f"  {cat}: {count}")


def generate_all_samples(output_dir: Path | None = None, count: int = 50):
    """Generate sample files for all roles.

    Args:
        output_dir: Directory to save files (default: same directory as script)
        count: Number of messages per file
    """
    if output_dir is None:
        output_dir = Path(__file__).parent

    output_dir.mkdir(parents=True, exist_ok=True)

    fieldnames = ["CONVERSATION ID", "CONVERSATION TITLE", "FROM", "SENDER PROFILE URL",
                  "TO", "DATE", "SUBJECT", "CONTENT", "FOLDER"]

    for role in ROLE_CONFIGS.keys():
        generator = LinkedInMessageGenerator(role=role, chaos_mode=True)
        messages = generator.generate_messages(count)
        messages = generator.add_repeat_offenders(messages, num_offenders=3)

        output_path = output_dir / f"sample_{role}.csv"

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(messages)

        print(f"Generated: {output_path} ({len(messages)} messages)")


if __name__ == "__main__":
    main()
