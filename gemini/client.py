"""
Gemini API client with retry logic and validation
"""
import json
import time
import logging
from typing import Dict, Any, Optional
from django.conf import settings

import google.generativeai as genai

from .schemas import validate_agent_response, get_schema_instructions
from .exceptions import GeminiError, GeminiValidationError, GeminiAPIError, GeminiRateLimitError

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Client for interacting with Gemini API.
    Handles initialization, retries, and validation.
    """
    
    def __init__(self):
        """Initialize the Gemini client with settings from Django config"""
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise GeminiError("GEMINI_API_KEY not configured")
        
        genai.configure(api_key=api_key)
        
        self.model_name = settings.GEMINI_MODEL
        self.temperature = settings.GEMINI_TEMPERATURE
        self.max_output_tokens = settings.GEMINI_MAX_OUTPUT_TOKENS
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens,
                "response_mime_type": "application/json"
            }
        )
        
        logger.info(f"Gemini client initialized with model: {self.model_name}")
    
    def generate_agent_response(
        self,
        prompt: str,
        max_retries: int = 2,
        retry_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Generate and validate an agent response.
        
        Args:
            prompt: The full prompt including agent context and stimulus
            max_retries: Number of retries on failure
            retry_delay: Seconds to wait between retries
            
        Returns:
            Validated response dictionary
            
        Raises:
            GeminiValidationError: If response fails validation after retries
            GeminiAPIError: If API call fails after retries
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # Make API call
                response = self.model.generate_content(prompt)
                
                # Extract text
                response_text = response.text.strip()
                
                # Parse JSON
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    # Try to extract JSON from response if wrapped in markdown
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        response_text = response_text[json_start:json_end].strip()
                        data = json.loads(response_text)
                    else:
                        raise GeminiValidationError(f"Invalid JSON: {e}")
                
                # Validate against schema
                is_valid, validated_data, error_msg = validate_agent_response(data)
                
                if is_valid:
                    return validated_data
                else:
                    last_error = GeminiValidationError(f"Schema validation failed: {error_msg}")
                    
                    # On validation failure, retry with corrective instruction
                    if attempt < max_retries:
                        logger.warning(f"Validation failed (attempt {attempt + 1}): {error_msg}")
                        prompt = f"{prompt}\n\nPREVIOUS RESPONSE WAS INVALID: {error_msg}\nPlease respond with ONLY valid JSON matching the exact schema."
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise last_error
                        
            except GeminiValidationError:
                raise
            except Exception as e:
                error_msg = str(e)
                
                # Check for rate limiting
                if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                    last_error = GeminiRateLimitError(error_msg)
                else:
                    last_error = GeminiAPIError(error_msg)
                
                if attempt < max_retries:
                    logger.warning(f"API error (attempt {attempt + 1}): {error_msg}")
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    raise last_error
        
        raise last_error or GeminiError("Unknown error occurred")
    
    def test_connection(self) -> bool:
        """Test that the API connection works"""
        try:
            response = self.model.generate_content("Say 'OK' in JSON format: {\"status\": \"OK\"}")
            return "OK" in response.text
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False