"""Patterns for detecting time/meeting requests."""

# Keywords that suggest someone is asking for your time
TIME_REQUEST_KEYWORDS = [
    # Direct meeting requests
    r'\b(quick call|brief call|short call|phone call|zoom call|video call)\b',
    r'\b(coffee|coffee chat|grab coffee|virtual coffee)\b',
    r'\b(pick your brain|bounce ideas|get your thoughts)\b',
    r'\b(15 minutes?|15 mins?|15-minute|fifteen minutes?)\b',
    r'\b(30 minutes?|30 mins?|30-minute|thirty minutes?)\b',
    r'\b(meet up|meetup|get together|catch up)\b',
    r'\b(schedule a call|schedule a meeting|set up a call|set up a meeting)\b',
    r'\b(hop on a call|jump on a call|quick chat|brief chat)\b',
    r'\b(would love to connect|love to connect|like to connect)\b',
    r'\b(can we talk|could we talk|would you be open to)\b',
    r'\b(informational interview|career advice|advice call)\b',
    r'\b(network|networking)\b',
    r'\b(intro call|introductory call|discovery call)\b',
    r'\b(free for a|available for a|time for a)\b',
    r'\b(calendar|calendly|book time|book a time)\b',
]

# Time estimates (in minutes) for different request types
TIME_ESTIMATES: dict[str, int] = {
    'quick': 15,
    'brief': 15,
    '15 min': 15,
    '30 min': 30,
    'coffee': 30,
    'call': 30,
    'meeting': 45,
    'lunch': 60,
    'default': 30,  # Default estimate if can't determine
}
