"""
retrieval/query_router.py

Routes a user query to the relevant Qdrant collections using keyword detection.
Falls back to searching all collections if intent is ambiguous.

Returns: list of section keys e.g. ["sops"], ["deviations", "capas"], ["all"]
"""

import re
from typing import List


# Keyword patterns per collection (including German equivalents)
COLLECTION_KEYWORDS = {
    "sops": [
        r"\bsops?\b", r"\bprocedure\b", r"\bstandard\b", r"\bprocess\b",
        r"\bprotocol\b", r"\bguideline\b", r"\bdocument\b", r"\bpolicy\b",
        r"\bworkflow\b", r"\binstruction\b", r"\bmanual\b", r"\bhandbook\b",
        r"\beffective\b", r"\bdepartment\b", r"\bversion\b", 
        r"\bverantwortlich\b", r"\babschnitt\b", r"\bgültig\b", r"\bänderung\b",
        r"\bit\b", r"\bhr\b", r"\bfinance\b", r"\bsecurity\b", r"\bsop-\b",
    ],
    "deviations": [
        r"\bdeviations?\b", r"\babweichungen?\b", r"\bdev\b", r"\bincident\b", r"\bviolation\b",
        r"\bfailure\b", r"\bbreach\b", r"\broot cause\b", r"\bursache\b", r"\bimpact\b",
        r"\bnon.?conformance\b", r"\bpattern\b", r"\bmuster\b", r"\bcritical\b", r"\bkritisch\b",
        r"\bdev-\b",
    ],
    "capas": [
        r"\bcapas?\b", r"\bcorrective\b", r"\bpreventive\b", r"\baction\b", r"\bmaßnahme\b",
        r"\bfix\b", r"\bremediation\b", r"\bimprovement\b", r"\bimplementation\b", r"\bumsetzung\b",
        r"\bowner\b", r"\bdue date\b", r"\beffectiveness\b", r"\bwirksamkeit\b",
        r"\bcapa-\b",
    ],
    "audits": [
        r"\baudits?\b", r"\bfindings?\b", r"\bbefunde?\b", r"\binspection\b", r"\bobservation\b",
        r"\bassessment\b", r"\bcompliance\b", r"\bakzeptiert\b", r"\bfokus\b",
        r"\baudit-\b",
    ],
    "decisions": [
        r"\bdecisions?\b", r"\bentscheidungen?\b", r"\bapproval\b", r"\bgenehmigung\b",
        r"\bbudget\b", r"\bescalation\b", r"\bresolution\b", r"\bbegründung\b", r"\brisiken\b",
        r"\bdec-\b",
    ],
}

# Phrases that trigger ALL collections (including relational/linking intent)
ALL_TRIGGERS = [
    r"\ball collections?\b", r"\beverything\b", r"\balle\b", r"\bgesamte\b",
    r"\bcross[- ]collection\b", r"\bacross all\b", r"\bcontext\b", r"\bkontext\b",
    r"\blinked\b", r"\bverknüpft\b", r"\bzusammenhang\b", r"\bverbindung\b",
    r"\bcompare\b", r"\bvergleiche\b", r"\bunterschied\b", r"\bmuster\b",
    r"\bthis case\b", r"\bdieser fall\b", r"\bdiesem fall\b", r"\bthis\b", r"\bdieser\b",
]


def route_query(query: str) -> List[str]:
    """
    Returns the list of collection keys to search for the given query.
    e.g. ["sops"] or ["deviations", "capas"] or ["sops","deviations","capas","audits","decisions"]
    """
    q = query.lower()

    # Score each collection by keyword matches
    scores = {}
    for section, patterns in COLLECTION_KEYWORDS.items():
        hits = sum(1 for p in patterns if re.search(p, q))
        if hits > 0:
            scores[section] = hits

    # Check if the query explicitly requests cross-collection search
    for pattern in ALL_TRIGGERS:
        if re.search(pattern, q):
            if scores:
                # Keep precision when query clearly indicates one area.
                if len(scores) == 1:
                    return list(scores.keys())
            return ["sops", "deviations", "capas", "audits", "decisions"]

    if not scores:
        # No clear match — search all
        return ["sops", "deviations", "capas", "audits", "decisions"]

    if len(scores) == 1:
        return list(scores.keys())

    # If multiple, return top 2 by score
    sorted_sections = sorted(scores, key=lambda k: scores[k], reverse=True)
    return sorted_sections[:2]


def describe_route(sections: List[str]) -> str:
    """Human-readable description of which collections will be searched."""
    label_map = {
        "sops":       "SOPs",
        "deviations": "Deviations",
        "capas":      "CAPAs",
        "audits":     "Audit Findings",
        "decisions":  "Decisions",
    }
    return " + ".join(label_map.get(s, s) for s in sections)
