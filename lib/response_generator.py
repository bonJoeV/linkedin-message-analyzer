"""
Polite Decline Response Generator

Because saying "no" 47 times a week is exhausting.
These templates help you decline gracefully (or not so gracefully).
"""

import random
from typing import Literal

ResponseTone = Literal["polite", "firm", "sarcastic", "honest", "corporate"]


class ResponseGenerator:
    """Generate polite (or not) decline responses for various message types."""

    POLITE_RESPONSES = {
        "time_request": [
            "Thanks for reaching out! Unfortunately, I'm not able to take on any new coffee chats at the moment. Best of luck with your endeavors!",
            "I appreciate you thinking of me! My schedule is quite full right now, but I wish you all the best.",
            "Thank you for the kind words! I'm not taking meetings at the moment, but I hope our paths cross in the future.",
            "Hi! I'm flattered by your interest, but I'm focusing on deep work right now and limiting external meetings. Thanks for understanding!",
        ],
        "financial_advisor": [
            "Thanks for reaching out! I'm happy with my current financial planning setup. Best of luck!",
            "I appreciate the offer, but I already have a financial advisor I work with. Thanks anyway!",
            "Thank you, but I'm not looking for financial planning services at this time.",
        ],
        "recruiter": [
            "Thanks for thinking of me! I'm not exploring new opportunities at the moment, but feel free to keep me in mind for the future.",
            "I appreciate you reaching out! I'm happy in my current role, but I'll let you know if anything changes.",
            "Thank you for the opportunity! I'm not looking to make a move right now, but best of luck with your search.",
        ],
        "sales_pitch": [
            "Thanks for reaching out! We're not in the market for this right now, but I'll keep you in mind.",
            "I appreciate the info! This isn't a priority for us at the moment. Best of luck!",
            "Thank you, but we're all set in this area for now.",
        ],
        "default": [
            "Thanks for reaching out! I'm not able to engage at this time, but I appreciate you thinking of me.",
            "Thank you for your message! I'm focusing on other priorities right now. Best of luck!",
        ],
    }

    FIRM_RESPONSES = {
        "time_request": [
            "I'm not available for calls or coffee chats. Thanks for understanding.",
            "I don't take unsolicited meeting requests. Best of luck with your search.",
            "No thank you.",
        ],
        "financial_advisor": [
            "I'm not interested in financial advisory services. Please remove me from your list.",
            "No thank you. I don't respond to cold outreach from financial advisors.",
            "Not interested.",
        ],
        "recruiter": [
            "Not interested in new opportunities. Please don't follow up.",
            "I'm not looking. Thanks.",
        ],
        "sales_pitch": [
            "We're not interested. Please remove me from your outreach list.",
            "No thank you.",
        ],
        "default": [
            "No thank you.",
            "I'm not interested.",
        ],
    }

    SARCASTIC_RESPONSES = {
        "time_request": [
            "Ah yes, another 'quick 15-minute call' that definitely won't turn into an hour. I'll pass, but thanks!",
            "I'd love to, but I'm all booked up 'picking brains' for the next 3 years. Best of luck!",
            "Sorry, my brain-picking quota is full this quarter. Maybe try again in 2030?",
            "If I had coffee with everyone who wanted to 'grab coffee,' I'd be caffeinated into another dimension. Pass!",
        ],
        "financial_advisor": [
            "Shockingly, I managed to figure out that I should save money all by myself. Thanks though!",
            "My retirement plan is 'hope for the best,' and I'm sticking with it. Thanks anyway!",
            "Ah yes, another LinkedIn FA. What are the odds! I'm good, thanks.",
            "I appreciate your concern for my retirement, but I've already accepted that I'll be working forever.",
        ],
        "recruiter": [
            "Let me guess - it's an 'exciting opportunity' at a 'well-funded startup' that you can't name yet? Hard pass.",
            "Is this the 'perfect fit' that 47 other recruiters also found this week? I'm flattered but no.",
            "Sorry, I only respond to recruiters who lead with the actual company name and salary range. Revolutionary, I know.",
        ],
        "sales_pitch": [
            "You're the 12th person this week to tell me your product will 'transform my workflow.' My workflow is fine, thanks.",
            "If your product saved me as much time as your sales team costs me in reading these messages, I might break even.",
            "Wow, a 47% productivity increase? If I got that from every product pitched to me, I'd be 4,700% productive by now!",
        ],
        "ai_generated": [
            "I hope this response finds you well! I wanted to reach out because I came across your message and was genuinely impressed by how obviously ChatGPT wrote it.",
            "Thank you for your thoughtful, definitely-not-templated message. I especially loved the 'synergy' part.",
        ],
        "franchise": [
            "I'd love to be my own boss, but my current boss (also me) is a real jerk. Pass on the franchise!",
            "Semi-absentee ownership sounds great! I'm already semi-absentee at my actual job.",
        ],
        "default": [
            "Thanks but no thanks. May your inbox be less annoying than mine.",
            "I appreciate the outreach! Just kidding, I don't. But thanks anyway.",
        ],
    }

    HONEST_RESPONSES = {
        "time_request": [
            "Hey, I get dozens of these requests every week and unfortunately can't say yes to them all. Nothing personal - I just don't have the bandwidth. Good luck!",
            "Honestly, I've learned that 'quick calls' with strangers rarely benefit me as much as the other person, so I've stopped taking them. Hope you understand.",
            "I appreciate the ask, but I've found these networking calls aren't a good use of my limited time. Best of luck though!",
        ],
        "financial_advisor": [
            "I get approached by FAs on LinkedIn constantly. While I'm sure you're great at your job, I'm not your target market. Good luck with your outreach!",
            "Honestly, the sheer volume of FA cold outreach I get has made me skeptical of anyone who leads this way. Nothing personal.",
        ],
        "recruiter": [
            "I appreciate you reaching out, but I've learned to only respond to recruiters who share the company name and comp range upfront. It saves everyone time.",
            "Thanks for thinking of me! I'm happy where I am, and if I ever look, I'll reach out. Promise.",
        ],
        "default": [
            "Thanks for the message. I'm going to pass, but I appreciate you thinking of me.",
            "Not for me, but good luck with everything!",
        ],
    }

    CORPORATE_RESPONSES = {
        "time_request": [
            "Thank you for your interest in connecting. At this time, I am not accepting external meeting requests. I appreciate your understanding and wish you continued success in your endeavors.",
            "I appreciate you taking the time to reach out. Due to bandwidth constraints, I am unable to accommodate additional networking calls. Best regards.",
        ],
        "financial_advisor": [
            "Thank you for your inquiry regarding financial planning services. I am satisfied with my current financial advisory relationships and do not require additional assistance at this time.",
        ],
        "recruiter": [
            "Thank you for considering me for this opportunity. I am not actively seeking new employment at this time. Should my circumstances change, I will reach out directly.",
        ],
        "sales_pitch": [
            "Thank you for sharing information about your product/service. At this time, we do not have a need that aligns with your offering. We will keep your information on file for future consideration.",
        ],
        "default": [
            "Thank you for your message. I am unable to engage at this time. Best regards.",
        ],
    }

    @classmethod
    def get_response(
        cls,
        message_type: str = "default",
        tone: ResponseTone = "polite"
    ) -> str:
        """Get a decline response for a message type.

        Args:
            message_type: Type of message (time_request, financial_advisor, recruiter, etc.)
            tone: Response tone (polite, firm, sarcastic, honest, corporate)

        Returns:
            A decline response string
        """
        tone_map = {
            "polite": cls.POLITE_RESPONSES,
            "firm": cls.FIRM_RESPONSES,
            "sarcastic": cls.SARCASTIC_RESPONSES,
            "honest": cls.HONEST_RESPONSES,
            "corporate": cls.CORPORATE_RESPONSES,
        }

        responses = tone_map.get(tone, cls.POLITE_RESPONSES)
        options = responses.get(message_type, responses.get("default", ["Thanks, but no thanks."]))
        return random.choice(options)

    @classmethod
    def get_all_responses(cls, message_type: str = "default") -> dict[str, list[str]]:
        """Get all response options for a message type across all tones."""
        return {
            "polite": cls.POLITE_RESPONSES.get(message_type, cls.POLITE_RESPONSES["default"]),
            "firm": cls.FIRM_RESPONSES.get(message_type, cls.FIRM_RESPONSES["default"]),
            "sarcastic": cls.SARCASTIC_RESPONSES.get(message_type, cls.SARCASTIC_RESPONSES["default"]),
            "honest": cls.HONEST_RESPONSES.get(message_type, cls.HONEST_RESPONSES["default"]),
            "corporate": cls.CORPORATE_RESPONSES.get(message_type, cls.CORPORATE_RESPONSES["default"]),
        }


def generate_response_for_message(message: dict, tone: ResponseTone = "polite") -> str:
    """Generate a response for a specific analyzed message.

    Args:
        message: Message dict with analysis results (should have 'matched_patterns' or category info)
        tone: Response tone

    Returns:
        Appropriate decline response
    """
    # Determine message type from analysis
    message_type = "default"

    # Check for specific indicators
    content = message.get("content", "").lower()
    patterns = message.get("matched_patterns", [])

    if any("financial" in str(p).lower() or "advisor" in str(p).lower() for p in patterns):
        message_type = "financial_advisor"
    elif any("recruit" in str(p).lower() or "position" in str(p).lower() or "opportunity" in str(p).lower() for p in patterns):
        message_type = "recruiter"
    elif any("call" in str(p).lower() or "coffee" in str(p).lower() or "15 min" in str(p).lower() for p in patterns):
        message_type = "time_request"
    elif any("demo" in str(p).lower() or "product" in str(p).lower() for p in patterns):
        message_type = "sales_pitch"
    elif "ai_score" in message:
        message_type = "ai_generated"
    elif any("franchise" in str(p).lower() for p in patterns):
        message_type = "franchise"

    return ResponseGenerator.get_response(message_type, tone)
