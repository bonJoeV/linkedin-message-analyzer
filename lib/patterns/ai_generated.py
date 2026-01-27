"""Patterns for detecting AI-generated (ChatGPT/LLM) messages.

These patterns catch the telltale signs of lazy AI-assisted outreach:
- Overly formal openings
- Generic compliments that could apply to anyone
- Buzzword soup
- Suspiciously perfect structure with zero personality
"""

# Classic ChatGPT openings - the "I hope this finds you well" energy
AI_OPENING_PATTERNS = [
    r'^i hope this (message |email )?(finds you well|reaches you)',
    r'^i hope you\'?re (doing well|having a great)',
    r'^i wanted to (reach out|connect|touch base)',
    r'^i came across your (profile|post|content) and',
    r'^i\'?m reaching out (because|to|regarding)',
    r'^i trust this (message|email) finds you',
    r'^greetings!',  # Nobody says this in real life
    r'^i hope you don\'t mind me reaching out',
]

# ChatGPT loves these filler phrases
AI_FILLER_PATTERNS = [
    r'\bin today\'s (fast-paced|ever-changing|dynamic|competitive)',
    r'\bin this day and age\b',
    r'\bat the end of the day\b',
    r'\bneedless to say\b',
    r'\bit goes without saying\b',
    r'\bwith that being said\b',
    r'\bhaving said that\b',
    r'\bmoving forward\b',
    r'\bgoing forward\b',
    r'\ball things considered\b',
]

# Corporate buzzword bingo - extra points if multiple appear
AI_BUZZWORD_PATTERNS = [
    r'\bsynergy\b',
    r'\bleverage\b(?! (against|on))',  # "leverage" as a verb, not physical
    r'\bscalable\b',
    r'\bactionable\b',
    r'\bimpactful\b',
    r'\bgame.?changer\b',
    r'\bthought leader(ship)?\b',
    r'\bdisrupt(ive|ion|or)?\b',
    r'\binnovate|innovative\b',
    r'\bparadigm\b',
    r'\bholistic\b',
    r'\brobust\b',
    r'\bseamless(ly)?\b',
    r'\boptimize|optimization\b',
    r'\bstreamline\b',
    r'\bpivot(ing)?\b',
    r'\bvalue.?add\b',
    r'\bwin.?win\b',
    r'\blow.?hanging fruit\b',
    r'\bmoving the needle\b',
    r'\bbandwidth\b(?!.{0,10}(mb|gb|internet))',  # Metaphorical, not technical
    r'\bcircle back\b',
    r'\btake (this )?offline\b',
    r'\btouch base\b',
]

# AI loves vague compliments that apply to literally anyone
AI_GENERIC_COMPLIMENT_PATTERNS = [
    r'\byour (impressive |extensive )?(experience|background|expertise|journey)',
    r'\byour (remarkable|outstanding|exceptional) (work|career|achievements)',
    r'\b(truly|really|genuinely) (impressed|inspired|amazed) by',
    r'\byour profile (really )?resonat(es|ed) with',
    r'\bi\'?ve been following your (work|journey|content)',  # But can't name anything specific
    r'\byou\'?re (clearly|obviously) (passionate|knowledgeable|experienced)',
    r'\bsomeone (of|with) your (caliber|stature|expertise)',
]

# Suspiciously perfect closings
AI_CLOSING_PATTERNS = [
    r'\bi look forward to (hearing from you|connecting|your response)',
    r'\bplease (do )?let me know if you have any questions',
    r'\bfeel free to reach out',
    r'\bdon\'t hesitate to (contact|reach out)',
    r'\bi\'d be (happy|delighted|thrilled) to discuss',
    r'\bwarm(est)? regards\b',
    r'\bkind(est)? regards\b',
    r'\bbest regards\b',
    r'\brespectfully\b$',
]

# Signs of AI trying too hard to be "personal"
AI_FAKE_PERSONAL_PATTERNS = [
    r'\bi (genuinely|truly|sincerely) believe',
    r'\bi\'m (genuinely|truly|really) excited',
    r'\bthis is not (just )?a(nother)? (generic|mass|template)',  # Ironic
    r'\bi\'m not (just )?sending this to everyone',  # They definitely are
    r'\bi hand.?picked you',
    r'\bi specifically (chose|selected) you',
    r'\bunlike other (messages|emails|outreach)',  # Sure, buddy
]

# Combined list for easy detection
AI_GENERATED_PATTERNS = (
    AI_OPENING_PATTERNS +
    AI_FILLER_PATTERNS +
    AI_BUZZWORD_PATTERNS +
    AI_GENERIC_COMPLIMENT_PATTERNS +
    AI_CLOSING_PATTERNS +
    AI_FAKE_PERSONAL_PATTERNS
)

# Weighted patterns - some are stronger signals than others
AI_WEIGHTED_PATTERNS: list[tuple[str, int]] = [
    # Strong signals (these are almost always AI)
    (r'^i hope this (message |email )?(finds you well|reaches you)', 3),
    (r'\bsynergy\b', 3),
    (r'\bthought leader\b', 3),
    (r'\bi\'m not (just )?sending this to everyone', 4),  # The irony
    (r'\bthis is not (just )?a(nother)? generic', 4),

    # Medium signals
    (r'\bleverage\b', 2),
    (r'\bin today\'s (fast-paced|ever-changing)', 2),
    (r'\byour (impressive|extensive) (experience|background)', 2),
    (r'\bi look forward to hearing from you', 2),

    # Weak signals (common but not conclusive)
    (r'\bscalable\b', 1),
    (r'\bimpactful\b', 1),
    (r'\bwarm regards\b', 1),
    (r'\bmoving forward\b', 1),
]
