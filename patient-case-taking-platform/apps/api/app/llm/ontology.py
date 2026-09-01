"""Small, clinician-reviewable ontology used by the deterministic mock provider."""

SOCRATES_DOMAINS = (
    "site",
    "onset",
    "character",
    "radiation",
    "associated_symptoms",
    "timing",
    "exacerbating_relieving_factors",
    "severity",
)

SOCRATES_QUESTIONS = {
    "en": {
        "site": "Where exactly do you feel the problem?",
        "onset": "When did it begin, and did it start suddenly or gradually?",
        "character": "How would you describe what it feels like?",
        "radiation": "Does it spread anywhere else?",
        "associated_symptoms": "What other symptoms are you having with it?",
        "timing": "Is it constant, or does it come and go?",
        "exacerbating_relieving_factors": "What makes it better or worse?",
        "severity": "On a scale from 0 to 10, how severe is it?",
    },
    "hi": {
        "site": "समस्या या दर्द ठीक कहाँ महसूस हो रहा है?",
        "onset": "यह कब शुरू हुआ, अचानक या धीरे-धीरे?",
        "character": "यह कैसा महसूस होता है? अपने शब्दों में बताइए।",
        "radiation": "क्या दर्द या तकलीफ शरीर के किसी और हिस्से में फैलती है?",
        "associated_symptoms": "इसके साथ और कौन-से लक्षण हो रहे हैं?",
        "timing": "यह लगातार रहता है या बीच-बीच में होता है?",
        "exacerbating_relieving_factors": "किस चीज़ से यह बढ़ता या कम होता है?",
        "severity": "0 से 10 तक, तकलीफ कितनी गंभीर है?",
    },
}

# These rules are intentionally conservative and deterministic. They trigger a
# clinician workflow; they do not diagnose or prescribe.
RED_FLAG_TERMS = {
    "difficulty_breathing": (
        "difficulty breathing",
        "cannot breathe",
        "shortness of breath",
        "सांस लेने में तकलीफ",
        "साँस लेने में तकलीफ",
        "सांस नहीं",
    ),
    "chest_pressure": ("chest pressure", "chest feels heavy", "सीना भारी", "छाती में दबाव"),
    "loss_of_consciousness": (
        "unconscious",
        "fainted",
        "loss of consciousness",
        "बेहोश",
        "बेहोशी",
    ),
    "stroke_signs": (
        "face drooping",
        "slurred speech",
        "one sided weakness",
        "बोलने में दिक्कत",
        "चेहरा टेढ़ा",
        "एक तरफ कमजोरी",
    ),
    "severe_bleeding": ("heavy bleeding", "bleeding won't stop", "बहुत खून", "खून नहीं रुक"),
}


def detect_red_flags(text: str) -> list[str]:
    normalized = " ".join(text.casefold().split())
    return [name for name, terms in RED_FLAG_TERMS.items() if any(term in normalized for term in terms)]
