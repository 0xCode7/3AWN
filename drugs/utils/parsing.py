import re

PARENS = re.compile(r"\([^)]*\)")

def parse_active_ingredients(raw: str) -> list[str]:
    """
    Amoxycillin (500mg) + Clavulanic Acid (125mg)
    -> ["amoxycillin", "clavulanic acid"]
    """
    if not raw:
        return []

    text = raw.lower()
    text = PARENS.sub("", text)

    parts = text.split("+")
    return [p.strip() for p in parts if p.strip()]
