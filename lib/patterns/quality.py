"""Patterns for detecting message quality signals (flattery, fake personalization, templates)."""

# Phrases that indicate fake/lazy personalization ("personalization theater")
FAKE_PERSONALIZATION_PATTERNS = [
    r'\b(loved your (recent )?post|great post|saw your post)\b(?!.{0,30}(about|on|regarding))',
    r'\b(impressive (background|profile|experience|career))\b',
    r'\b(came across your profile|stumbled upon your profile)\b',
    r'\b(your profile caught my eye|profile stood out)\b',
    r'\b(noticed you|I see you|I see that you)\b',
    r'\b(people like you|professionals like yourself)\b',
    r'\b(in your position|someone in your role)\b',
    r'\b(thought (we should|I\'d reach out|to connect))\b',
]

# Flattery phrases - empty praise before the ask
# Format: (pattern, weight)
FLATTERY_PATTERNS: list[tuple[str, int]] = [
    # Generic compliments
    (r'\b(impressive|amazing|incredible|outstanding|remarkable|fantastic|excellent)\b', 1),
    (r'\b(love what you\'re doing|love your work|love your content)\b', 2),
    (r'\b(inspiring|inspirational|motivated by)\b', 2),
    (r'\b(thought leader|industry leader|leader in)\b', 2),
    (r'\b(successful|accomplished|achieved)\b', 1),
    (r'\b(great work|great job|killing it|crushing it)\b', 2),
    (r'\b(so cool|really cool|very cool)\b', 1),
    # LinkedIn-specific flattery
    (r'\b(your profile (really )?stood out)\b', 2),
    (r'\b(came across your (impressive |amazing )?(profile|content|post))\b', 1),
    (r'\b(been following your (work|journey|content))\b', 2),
    (r'\b(big fan of)\b', 2),
    (r'\b(admire (what you|your))\b', 2),
    (r'\b(respect (what you|your))\b', 1),
    # Exclamation amplifiers (count !'s as flattery signal)
    (r'!{2,}', 1),  # Multiple exclamation marks
]

# Common template/automation indicators
TEMPLATE_INDICATORS = [
    r'\{\{.*?\}\}',  # Merge field remnants
    r'\[first.?name\]|\[company\]|\[title\]',  # Unfilled placeholders
    r'^(hi|hey|hello)[\s,!]+$',  # Generic greeting with nothing else
    r'hope this (message finds you well|email finds you)',
    r'i\'ll keep this (short|brief)',
    r'i know you\'re (busy|swamped)',
    r'not sure if (this is the right|you\'re the right)',
    r'feel free to ignore',
    r'no worries if not',
    r'totally understand if',
]
