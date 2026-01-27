"""Patterns for detecting LinkedIn Lunatic behavior.

For those special messages that make you question humanity:
- Humblebrags
- Engagement bait
- Crypto bros
- "Agree?" posters
- Inspirational quote regurgitators
"""

# Humblebrags - complaining while actually boasting
HUMBLEBRAG_PATTERNS = [
    r'\b(so (humbled|blessed|grateful|honored) to)\b',
    r'\b(exhausted|overwhelmed).{0,30}(success|growth|opportunity)',
    r'\b(can\'t believe|never thought|who knew).{0,30}(achievement|award|promotion|feature)',
    r'\b(hate|don\'t like) (talking about|sharing).{0,30}(but|however)',  # "I hate bragging but..."
    r'\banother (award|feature|recognition)\b',
    r'\b(too many|so many) (opportunities|offers|invitations)\b',
]

# Engagement bait - manufacturing interaction
ENGAGEMENT_BAIT_PATTERNS = [
    r'\bagree\??\s*$',  # The classic "Agree?" ending
    r'\bthoughts\??\s*$',
    r'\bam i (right|wrong)\?',
    r'\bwhat do you think\??\s*$',
    r'\bdrop a .{0,20} (if|in the comments)',
    r'\blike (this|if you) (if|agree)',
    r'\brepost (this|if)',
    r'\bshare (this|if you)',
    r'\bcomment .{0,10} below',
    r'\btag someone who',
    r'\bfollow me for more',
]

# Crypto/NFT/Web3 hustlers
CRYPTO_HUSTLER_PATTERNS = [
    r'\b(crypto|bitcoin|btc|ethereum|eth|blockchain)\b',
    r'\bnft\b',
    r'\bweb\s*3\b',
    r'\bdecentraliz',
    r'\bto the moon\b',
    r'\bdiamond hands\b',
    r'\bhodl\b',
    r'\b(defi|yield farming|staking)\b',
    r'\bpassive income.{0,20}(crypto|nft)',
    r'\b(token|coin) (launch|sale|drop)\b',
]

# "Thought leaders" who just repost motivational content
THOUGHT_LEADER_PATTERNS = [
    r'\b(monday|tuesday|wednesday|thursday|friday) (motivation|mood|vibes)\b',
    r'\brise and grind\b',
    r'\bhustle (culture|harder|mode)\b',
    r'\b(success|failure) (is|isn\'t) (a|about)\b',
    r'\bwork.?life balance\b',
    r'\b(winners|losers) (do|don\'t)\b',
    r'\bremember:?\s',  # "Remember: [generic wisdom]"
    r'\bthe (only|real|true) (secret|key|difference)\b',
    r'\bif (elon|bezos|jobs|gates) (can|could|did)\b',
]

# Pyramid scheme / MLM indicators
MLM_PATTERNS = [
    r'\bpassive income\b',
    r'\bfinancial freedom\b',
    r'\bwork from (home|anywhere|your phone)',
    r'\bbe your own boss\b',
    r'\b(side|extra) income\b',
    r'\b(amazing|incredible|life-?changing) opportunity\b',
    r'\bground floor\b',
    r'\b(dm|message|reach out) (for|to learn) more\b',
    r'\bserious (inquiries|people) only\b',
    r'\b(change|transform) your life\b',
]

# Self-promotion disguised as "value"
SELF_PROMO_PATTERNS = [
    r'\bi (just |recently )?(wrote|published|posted|launched|created)',
    r'\bcheck out my (new|latest|recent)',
    r'\blink in (bio|comments|first comment)',
    r'\bfull (article|post|thread) (in |on )',
    r'\b(free|exclusive) (download|access|guide)\b',
    r'\bsubscribe to my\b',
    r'\bjoin (my|the) (newsletter|community|waitlist)',
]

# The "I made it" posts
SUCCESS_THEATER_PATTERNS = [
    r'\b(excited|thrilled|proud) to (announce|share)',
    r'\bbig news\b',
    r'\bI did (it|the thing)\b',
    r'\b(finally|officially)\b.{0,20}(announce|share|reveal)',
    r'\bafter (years|months|weeks) of',
    r'\bhere\'s (what|how) I (learned|did it)',
    r'\bthe journey from.{0,30}to\b',
]

# Fake vulnerability posts
FAKE_VULNERABILITY_PATTERNS = [
    r'\bI\'ll (be honest|admit|confess)\b',
    r'\breal talk\b',
    r'\bunpopular opinion\b',
    r'\bhot take\b',
    r'\bI\'m going to (say|share) something (controversial|unpopular)',
    r'\bthis might (upset|surprise) (some|a lot of) people',
    r'\bnobody (talks|is talking) about\b',
]
