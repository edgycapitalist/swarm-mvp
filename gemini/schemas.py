"""
JSON schema validation for Gemini outputs
"""
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field, field_validator
from .exceptions import GeminiValidationError


# Valid emotion names (Plutchik's wheel)
VALID_EMOTIONS = [
    'joy', 'trust', 'fear', 'surprise', 
    'sadness', 'disgust', 'anger', 'anticipation'
]

# Valid intent labels
VALID_INTENTS = [
    'share_positive',      # Will share with positive framing
    'share_negative',      # Will share with criticism
    'engage_supportive',   # Will comment supportively
    'engage_critical',     # Will comment critically
    'ignore',              # Will scroll past
    'oppose_actively',     # Will actively push back
    'purchase_intent',     # Shows buying interest
    'seek_more_info',      # Wants to learn more
]


class EmotionsSchema(BaseModel):
    """Validates emotion scores"""
    joy: float = Field(ge=0, le=1)
    trust: float = Field(ge=0, le=1)
    fear: float = Field(ge=0, le=1)
    surprise: float = Field(ge=0, le=1)
    sadness: float = Field(ge=0, le=1)
    disgust: float = Field(ge=0, le=1)
    anger: float = Field(ge=0, le=1)
    anticipation: float = Field(ge=0, le=1)


class AgentResponseSchema(BaseModel):
    """
    Validates the JSON output contract from Gemini.
    Each agent-phase call must return these fields.
    """
    approval: int = Field(ge=1, le=10, description="Approval score 1-10")
    emotions: EmotionsSchema
    intent: str = Field(description="Intent label")
    intent_confidence: float = Field(ge=0, le=1, description="Confidence 0-1")
    verbatim: str = Field(max_length=500, description="Short reaction text")
    
    @field_validator('intent')
    @classmethod
    def validate_intent(cls, v):
        if v not in VALID_INTENTS:
            raise ValueError(f'Intent must be one of: {VALID_INTENTS}')
        return v


def validate_agent_response(data: Dict[str, Any]) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Validate agent response against schema.
    
    Args:
        data: The parsed JSON response from Gemini
        
    Returns:
        Tuple of (is_valid, validated_data, error_message)
    """
    try:
        validated = AgentResponseSchema(**data)
        return True, validated.model_dump(), None
    except Exception as e:
        return False, None, str(e)


def get_schema_instructions() -> str:
    """
    Returns the JSON schema instructions to include in prompts.
    """
    return """
You must respond with ONLY a valid JSON object with exactly these fields:
{
    "approval": <integer 1-10, where 1=strongly disapprove, 10=strongly approve>,
    "emotions": {
        "joy": <float 0-1>,
        "trust": <float 0-1>,
        "fear": <float 0-1>,
        "surprise": <float 0-1>,
        "sadness": <float 0-1>,
        "disgust": <float 0-1>,
        "anger": <float 0-1>,
        "anticipation": <float 0-1>
    },
    "intent": <one of: "share_positive", "share_negative", "engage_supportive", "engage_critical", "ignore", "oppose_actively", "purchase_intent", "seek_more_info">,
    "intent_confidence": <float 0-1>,
    "verbatim": <string max 500 chars - what this person would actually say/post in response>
}

Do not include any text before or after the JSON. Only output the JSON object.
"""