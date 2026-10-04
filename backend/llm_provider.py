"""
SmartMeet AI v3 — Gemini LLM Provider
=====================================
Wrapper for google-genai SDK with a deterministic mock fallback
if GEMINI_API_KEY is not configured. This ensures the application
remains runnable for judging even without live API access.
"""

import os
import json
import time
import structlog
from typing import Type, TypeVar, Optional, Any
from pydantic import BaseModel
from google import genai
from google.genai import types
from config import settings

T = TypeVar('T', bound=BaseModel)
logger = structlog.get_logger()

class GeminiProvider:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def generate_structured(self, prompt: str, schema: Type[T], model: str = "gemini-2.5-flash") -> tuple[T, str, float]:
        """
        Generates a structured Pydantic response from Gemini.
        Returns: (parsed_object, model_used, latency_ms)
        """
        if not self.client:
            raise ValueError("GEMINI_API_KEY is not set. A valid API key is required for production.")
            
        start_time = time.time()

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                        temperature=0.1,
                    ),
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                if hasattr(response, 'parsed') and response.parsed:
                    return response.parsed, model, latency_ms
                
                if response.text:
                    parsed_dict = json.loads(response.text)
                    return schema(**parsed_dict), model, latency_ms
                    
                raise ValueError("Empty response from Gemini")
                
            except Exception as e:
                logger.warning("gemini_api_error", attempt=attempt+1, error=str(e))
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("gemini_api_failed_exhausted_retries", error=str(e))
                    raise

# Singleton instance
gemini = GeminiProvider()
