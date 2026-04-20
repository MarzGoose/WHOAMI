LIFE_DOMAINS = {
    "work": {
        "keywords": ["work", "job", "career", "boss", "office", "client", "project", "meeting", "deadline", "colleague", "salary", "employed"],
        "description": "employment, career, professional life",
    },
    "money": {
        "keywords": ["money", "finance", "budget", "debt", "savings", "invest", "salary", "income", "expense", "spend", "spending", "buy", "bought", "purchase", "cost", "afford"],
        "description": "finances, spending, debt, income",
    },
    "health": {
        "keywords": ["health", "sick", "doctor", "medical", "exercise", "diet", "fitness", "pain", "hospital", "sleep", "tired", "energy", "gym", "body"],
        "description": "physical health, fitness, medical",
    },
    "family": {
        "keywords": ["family", "mum", "mom", "dad", "parent", "sibling", "brother", "sister", "kids", "children", "wife", "husband", "partner"],
        "description": "family relationships",
    },
    "relationships": {
        "keywords": ["friend", "friendship", "relationship", "social", "lonely", "people", "connect", "community", "partner", "dating"],
        "description": "social relationships, friendships",
    },
    "faith": {
        "keywords": ["faith", "god", "church", "prayer", "spiritual", "religion", "belief", "worship", "jesus", "bible"],
        "description": "faith, spirituality, religion",
    },
    "purpose": {
        "keywords": ["purpose", "meaning", "goal", "dream", "aspire", "passion", "fulfil", "fulfill", "calling", "mission"],
        "description": "purpose, meaning, long-term goals",
    },
    "mental_health": {
        "keywords": ["anxiety", "stress", "depressed", "depression", "overwhelm", "therapy", "counsell", "mental health", "burnout", "grief", "trauma"],
        "description": "mental health, emotional wellbeing",
    },
}

DOMAIN_KEYWORDS = {k: v["keywords"] for k, v in LIFE_DOMAINS.items()}
