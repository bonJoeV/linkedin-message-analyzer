"""Patterns for detecting various types of outreach messages."""

# Patterns that identify financial advisors/wealth managers
FINANCIAL_ADVISOR_PATTERNS = [
    # Titles
    r'\b(financial advisor|financial adviser|wealth advisor|wealth adviser)\b',
    r'\b(financial planner|wealth planner|certified financial planner|cfp)\b',
    r'\b(wealth management|wealth manager|asset manager)\b',
    r'\b(investment advisor|investment adviser|investment manager)\b',
    r'\b(portfolio manager|private banker|private wealth)\b',
    r'\b(retirement planning|retirement specialist)\b',
    r'\b(financial consultant|wealth consultant)\b',
    # Companies (common FA firms)
    r'\b(edward jones|northwestern mutual|ameriprise|raymond james)\b',
    r'\b(merrill lynch|morgan stanley|ubs|charles schwab)\b',
    r'\b(fidelity|vanguard|prudential|mass mutual|massmutual)\b',
    r'\b(new york life|principal financial|transamerica)\b',
    r'\b(lincoln financial|pacific life|equitable)\b',
    # Common phrases in FA pitches
    r'\b(financial goals|retirement goals|investment strategy)\b',
    r'\b(grow your wealth|protect your wealth|wealth preservation)\b',
    r'\b(complimentary review|free consultation|portfolio review)\b',
    r'\b(fiduciary|fee-only|fee-based)\b',
    # MSFT-specific (for employees getting targeted)
    r'\b(espp|employee stock|stock compensation|rsu|restricted stock)\b',
    r'\b(msft.{0,20}(stock|awards|grants|equity))\b',
    r'\b(401.?k|retirement account)\b',
]

# Franchise consultant/broker patterns - people trying to sell you a franchise
FRANCHISE_CONSULTANT_PATTERNS = [
    r'\bfranchise.{0,20}(consult|broker|advisor|coach|opportunity)\b',
    r'\bexplor(e|ing).{0,20}franchise\b',
    r'\bfranchise ownership\b',
    r'\bfranchise.{0,20}(work for you|could work)\b',
    r'\b(corporate|job).{0,20}(layoff|reduction|insecurity)\b',
    r'\bbe your own boss\b',
    r'\bnot.{0,20}report to anyone\b',
    r'\bsemi.?absentee\b',
    r'\bbusiness ownership\b',
    r'\bfranchise industry veteran\b',
    r'\bdream business\b',
    r'\bincome diversification\b',
]

# Expert network / paid consulting firms
EXPERT_NETWORK_PATTERNS = [
    r'\b(glg|gerson lehrman)\b',
    r'\barbolus\b',
    r'\balphasights\b',
    r'\bguidepoint\b',
    r'\bwoozle\b',
    r'\bthird bridge\b',
    r'\btechspert\b',
    r'\bdialectica\b',
    r'\bprosapient\b',
    r'\bcoleman\b',
    r'\bpaid.{0,15}(consultation|call|engagement|phone)\b',
    r'\b(1|one).?hour paid\b',
    r'\bexpert.{0,10}(network|consultation)\b',
]

# Angel investor / startup pitch patterns
ANGEL_INVESTOR_PATTERNS = [
    r'\bangel.{0,10}(round|investor|investment)\b',
    r'\bseed.{0,10}(round|funding|stage)\b',
    r'\bseries.?[ab]\b',
    r'\b(pre.?seed|pre-seed)\b',
    r'\brais(e|ing).{0,15}(funding|capital|round)\b',
    r'\binvestment opportunity\b',
    r'\badvisory.{0,10}board\b',
    r'\bstartup.{0,15}(opportunity|pitch)\b',
]

# Recruiter patterns
RECRUITER_PATTERNS = [
    r'\b(position|role|opportunity).{0,20}(available|open|hiring)\b',
    r'\b(perfect|great|ideal).{0,10}(fit|match|candidate)\b',
    r'\b(reach|reaching) out.{0,20}(role|position|opportunity)\b',
    r'\bresume\b',
    r'\b(job|career).{0,10}(opportunity|opening)\b',
    r'\b(direct hire|contract.to.hire)\b',
    r'\bhybrid.{0,10}(days|onsite)\b',
    r'\b(azure|cloud).{0,10}(engineer|architect|developer)\b',
]

# Role confusion detection patterns
USER_ROLES: dict[str, dict[str, list[str]]] = {
    'microsoft': {
        'keywords': [r'\bmicrosoft\b', r'\bmsft\b', r'\bazure\b', r'\btech (giant|company)\b'],
        'title_hints': [r'\b(software|tech|engineering|product)\b'],
    },
    'franchise': {
        'keywords': [r'\bvital stretch\b', r'\bfranchise\b', r'\bstudio\b', r'\bstretch(ing)?\b', r'\brecovery\b'],
        'title_hints': [r'\b(coo|operations|franchise)\b'],
    },
}

# Pitch types that indicate role confusion when mismatched
PITCH_ROLE_MISMATCHES = [
    # (pitch_pattern, expected_role, wrong_role_indicator)
    (r'\b(enterprise software|saas|b2b software|cloud solution)\b', 'microsoft', 'franchise'),
    (r'\b(franchise consult|multi-location|brick and mortar)\b', 'franchise', 'microsoft'),
    (r'\b(tech startup|developer tool|api|sdk)\b', 'microsoft', 'franchise'),
    (r'\b(wellness|health|fitness|spa|massage)\b', 'franchise', 'microsoft'),
]
