"""
Build the system prompt and few-shot examples for the baseline gate.
Examples are real diary entries, none of them a test case.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data" / "processed" / "baseline_cases.json"

SYSTEM = (
    "You are reproducing the register of the Babylonian Astronomical Diaries "
    "as rendered in the Sachs and Hunger English translation.\n"
    "Write ONE dated diary entry describing exactly the sky state given.\n"
    "Rules:\n"
    "- Mention every celestial object named in the OBSERVATION_STATE.\n"
    "- Mention no celestial object that is absent from it. Do not add planets, "
    "stars or events that were not given.\n"
    "- Preserve the measurements and relations exactly as given "
    "(cubits, fingers, degrees, above/below/in front of/behind).\n"
    "- Write continuous prose in the diary's voice, not a bulleted list of facts.\n"
    "- Do not add omens, interpretations or predictions. This is an observation "
    "genre, not an omen genre.\n"
    "- Output only the entry text. No preamble, no commentary."
)

FEWSHOT = [
    (
        "<TRADITION=BABYLONIAN>\n<GENRE=OBSERVATION>\n<OBSERVATION_STATE>\n"
        "  Date: year 49 of the Seleucid Era, month V, night of the 10th\n"
        "  Watch: beginning of the night\n"
        "  Moon: visible, confidence: high\n"
        "  Events: [{\"event\":\"conjunction\",\"objects\":[\"Moon\",\"beta Capricorni\"],"
        "\"relation\":\"below\",\"separation\":\"3 cubits\","
        "\"note\":\"Moon having passed 2/3 cubit to the east\",\"confidence\":\"high\"}]\n"
        "</OBSERVATION_STATE>\n<ENTRY>",
        "Night of the 10th, beginning of the night, the moon was 3 cubits below "
        "β Capricorni, the moon having passed 2/3 cubit to the east.",
    ),
    (
        "<TRADITION=BABYLONIAN>\n<GENRE=OBSERVATION>\n<OBSERVATION_STATE>\n"
        "  Date: year 38 of the Seleucid Era, month VIII, night of the 8th\n"
        "  Watch: beginning of the night\n"
        "  Moon: visible, confidence: high\n  Saturn: visible, confidence: high\n"
        "  Events: [{\"event\":\"conjunction\",\"objects\":[\"Moon\",\"Saturn\"],"
        "\"relation\":\"in front of\",\"separation\":\"2/3 cubit\","
        "\"direction\":\"to the west\",\"confidence\":\"high\"}]\n"
        "</OBSERVATION_STATE>\n<ENTRY>",
        "Night of the 8th, beginning of the night, the moon stood 2/3 cubit in "
        "front of Saturn to the west.",
    ),
    (
        "<TRADITION=BABYLONIAN>\n<GENRE=OBSERVATION>\n<OBSERVATION_STATE>\n"
        "  Date: year 49 of the Seleucid Era, month V, the 20th\n"
        "  Jupiter: first visibility, in Leo, brightness: small, confidence: high\n"
        "  Events: [{\"event\":\"first_appearance\",\"objects\":[\"Jupiter\"],"
        "\"sign\":\"Leo\",\"rising_to_sunrise_deg\":\"11 40\","
        "\"ideal_first_appearance\":\"the 19th\",\"confidence\":\"medium\"}]\n"
        "</OBSERVATION_STATE>\n<ENTRY>",
        "The 20th, Jupiter's first appearance in Leo; it was small, rising of "
        "Jupiter to sunrise: 11° 40'; (ideal) first appearance on the 19th.",
    ),
    (
        "<TRADITION=BABYLONIAN>\n<GENRE=OBSERVATION>\n<OBSERVATION_STATE>\n"
        "  Date: year 179 of the Seleucid Era, month VI, night of the 28th\n"
        "  Watch: first part of the night\n"
        "  Mars: visible, confidence: high\n  Saturn: visible, confidence: high\n"
        "  Events: [{\"event\":\"conjunction\",\"objects\":[\"Mars\",\"Saturn\"],"
        "\"relation\":\"below\",\"separation\":\"1 cubit 4 fingers\","
        "\"confidence\":\"high\"}]\n"
        "</OBSERVATION_STATE>\n<ENTRY>",
        "Night of the 28th, first part of the night, Mars was 1 cubit 4 fingers "
        "below Saturn.",
    ),
    (
        "<TRADITION=BABYLONIAN>\n<GENRE=OBSERVATION>\n<OBSERVATION_STATE>\n"
        "  Date: year 8 of Alexander, month VII, the 1st\n"
        "  Month start: the 1st followed the 30th of the preceding month\n"
        "  Moon: first visibility, earthshine: present, confidence: high\n"
        "  Events: [{\"event\":\"lunar_first_visibility\",\"objects\":[\"Moon\"],"
        "\"sunset_to_moonset_deg\":16,\"confidence\":\"high\"}]\n"
        "</OBSERVATION_STATE>\n<ENTRY>",
        "Month VII, the 1st (of which followed the 30th of the preceding month); "
        "sunset to moonset: 16°; earthshine.",
    ),
]


def build(case, shots=3):
    """Return (system, user) for one case. shots=0 gives the zero-shot tier."""
    parts = []
    for state, entry in FEWSHOT[:shots]:
        parts.append(f"{state}\n{entry}\n</ENTRY>")
    parts.append(case["observation_state"])
    return SYSTEM, "\n\n".join(parts)


def main():
    data = json.loads(CASES.read_text(encoding="utf-8"))
    for c in data["cases"]:
        sys_p, user_p = build(c)
        print("=" * 78)
        print(f"CASE {c['id']}  ({c['phenomenon']})")
        print("=" * 78)
        print(user_p)
        print("\n--- held-back reference (never shown to the model) ---")
        print(f"  {c['reference_text']}\n")


if __name__ == "__main__":
    main()
