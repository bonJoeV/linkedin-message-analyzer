"""Patterns for detecting sales pitches, life coaches, and other solicitations.

The fine art of detecting people who want to:
- Sell you something you don't need
- Transform your life/mindset/paradigm
- Have you on their podcast (audience of 12)
- Invite you to their "exclusive" webinar
"""

# Sales pitch patterns - the classics
SALES_PITCH_PATTERNS = [
    r'\b(quick )?demo\b',
    r'\bfree trial\b',
    r'\b(book|schedule) a (call|meeting|demo)\b',
    r'\bwould you be open to\b',
    r'\bif i could show you\b',
    r'\bsave (you )?(time|money|hours)\b',
    r'\b(boost|increase|improve) your (revenue|sales|productivity|roi)\b',
    r'\bguaranteed (results|roi|return)\b',
    r'\bno obligation\b',
    r'\bno strings attached\b',
    r'\blimited time (offer|only)\b',
    r'\bexclusive (offer|discount|deal)\b',
    r'\b(our|my) (solution|platform|tool|software)\b',
    r'\bpain points?\b',
    r'\bsolve your\b',
    r'\btransform your (business|workflow|process)',
    r'\bstreamline your\b',
    r'\bautomate your\b',
    r'\b(10|100|1000)x your\b',
    r'\broi (of|within|in)\b',
]

# Life coach / business coach patterns
COACHING_PATTERNS = [
    r'\b(life|business|executive|leadership) coach\b',
    r'\btransformation(al)? (journey|coaching|program)\b',
    r'\bunlock your (potential|true self|full)\b',
    r'\bmindset (shift|work|coaching|transformation)\b',
    r'\bbreakthrough (session|call|coaching)\b',
    r'\blevel up your\b',
    r'\btake (your|it) to the next level\b',
    r'\bachieve (your|peak) (goals|performance|potential)\b',
    r'\bempowerment\b',
    r'\bmanifest(ation|ing)?\b',
    r'\babundance mindset\b',
    r'\bgrowth mindset\b',
    r'\blimiting beliefs?\b',
    r'\bself-?discovery\b',
    r'\bpersonal (development|growth|brand)\b',
    r'\bfind your (why|purpose|passion)\b',
    r'\blive your (best|authentic|true)\b',
    r'\b(6|7) figure\b',
    r'\bscale (yourself|your business)\b',
    r'\bhigh.?performance\b',
    r'\baccountability (partner|coaching|call)\b',
]

# Podcast host patterns
PODCAST_PATTERNS = [
    r'\b(my|our|the) podcast\b',
    r'\bwould love to have you on\b',
    r'\bguest (on|for) (our|my|the)\b',
    r'\bepisode (about|on|featuring)\b',
    r'\b(growing|engaged|loyal) audience\b',
    r'\blisteners (would|will) love\b',
    r'\bshare your (story|expertise|journey)\b',
    r'\bgreat fit for (our|my) (show|podcast|audience)\b',
    r'\binterview you\b',
    r'\bpick your brain\b',  # The classic
    r'\b(record|schedule|book) (a|an) (episode|interview|conversation)\b',
    r'\byour (story|journey) (would|could) (inspire|resonate)\b',
    r'\b(apple|spotify|youtube) podcast\b',
]

# Webinar / Event invitation patterns
WEBINAR_PATTERNS = [
    r'\b(free |exclusive )?webinar\b',
    r'\b(virtual|online|live) (event|summit|conference|workshop)\b',
    r'\b(limited|exclusive) (seats|spots|access)\b',
    r'\breserve your (spot|seat)\b',
    r'\bjoin (us|me) (for|on|at)\b',
    r'\bregister (now|today|here)\b',
    r'\bdon\'t miss (this|out)\b',
    r'\b(industry|thought) leaders?\b',
    r'\bnetworking (event|opportunity)\b',
    r'\bpanel (discussion|of experts)\b',
    r'\bkeynote (speaker|session|address)\b',
    r'\bfireside chat\b',
    r'\bmaster\s?class\b',
    r'\bworkshop (on|about|for)\b',
    r'\bsummit (20|for)\b',
]

# "Let's partner" / collaboration spam
PARTNERSHIP_PATTERNS = [
    r'\bstrategic (partnership|alliance|collaboration)\b',
    r'\b(let\'s|we should) (partner|collaborate|team up)\b',
    r'\bjoint venture\b',
    r'\bcross.?promot(e|ion)\b',
    r'\bmutually beneficial\b',
    r'\bwin.?win (situation|scenario|opportunity)\b',
    r'\bsynergies between\b',
    r'\bcomplement(ary|s) (well|each other|perfectly)\b',
    r'\bexplore (a |potential )?(partnership|collaboration|opportunity)\b',
    r'\baffiliate (partnership|program|marketing)\b',
    r'\breferral (partnership|program)\b',
    r'\bco.?(market|brand|create)\b',
]

# Course / info-product sellers
COURSE_SELLER_PATTERNS = [
    r'\b(my|our|this) (course|program|curriculum|bootcamp)\b',
    r'\benroll (now|today)\b',
    r'\b(limited|special|early.?bird) (enrollment|pricing|offer)\b',
    r'\bcohort.?based\b',
    r'\b(step.?by.?step|proven) (system|framework|method)\b',
    r'\bblueprint (for|to)\b',
    r'\bsecrets (of|to)\b',
    r'\bexact (steps|framework|system)\b',
    r'\b(how|what) I (did|learned|discovered) to\b',
    r'\bfrom (zero|nothing|scratch) to\b',
    r'\bdon\'t (need|require) (any )?(experience|degree)\b',
    r'\b(certification|certificate) (program|course)\b',
]

# Book / content promotion
CONTENT_PROMO_PATTERNS = [
    r'\b(my|our) (new|latest|upcoming) book\b',
    r'\bjust (published|released|launched)\b',
    r'\bbe(st|come a) sell(er|ing)\b',
    r'\bpre.?order (now|today|available)\b',
    r'\bbook launch\b',
    r'\bwould love your (feedback|thoughts|review)\b',
    r'\b(amazon|kindle|audible)\b',
    r'\breview (on|for|would be)\b',
    r'\bdownload (my|your|the) free\b',
    r'\b(free|downloadable) (ebook|guide|checklist|template)\b',
    r'\bwhitepaper\b',
    r'\blead magnet\b',
]

# Combined exports
SALES_COACHING_ALL_PATTERNS = (
    SALES_PITCH_PATTERNS +
    COACHING_PATTERNS +
    PODCAST_PATTERNS +
    WEBINAR_PATTERNS +
    PARTNERSHIP_PATTERNS +
    COURSE_SELLER_PATTERNS +
    CONTENT_PROMO_PATTERNS
)

# Weighted patterns for scoring
SALES_COACHING_WEIGHTED: list[tuple[str, int]] = [
    # Strong signals
    (r'\bunlock your potential\b', 3),
    (r'\b(6|7) figure\b', 3),
    (r'\btransformation(al)? (journey|coaching)\b', 3),
    (r'\blimited (seats|spots)\b', 3),
    (r'\bguaranteed (results|roi)\b', 3),
    (r'\bfrom (zero|nothing) to\b', 3),

    # Medium signals
    (r'\bfree (demo|trial|webinar)\b', 2),
    (r'\b(my|our) podcast\b', 2),
    (r'\b(life|business) coach\b', 2),
    (r'\bstrategic partnership\b', 2),
    (r'\bmasterclass\b', 2),

    # Weak signals
    (r'\bbook a call\b', 1),
    (r'\bjoin us for\b', 1),
    (r'\bwould love to have you on\b', 1),
    (r'\bexplore a partnership\b', 1),
]
