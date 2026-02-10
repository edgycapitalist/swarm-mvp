"""
Custom exceptions for Gemini integration
"""


class GeminiError(Exception):
    """Base exception for Gemini-related errors"""
    pass


class GeminiValidationError(GeminiError):
    """Raised when Gemini output fails schema validation"""
    pass


class GeminiRateLimitError(GeminiError):
    """Raised when hitting rate limits"""
    pass


class GeminiAPIError(GeminiError):
    """Raised for general API errors"""
    pass