import hashlib
import json
import asyncio
import logging
from openai import AsyncOpenAI, RateLimitError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)

# Configure base URL based on provider
def get_base_url(provider: str) -> str | None:
    if provider.lower() == "groq":
        return "https://api.groq.com/openai/v1"
    elif provider.lower() == "ollama":
        return "http://host.docker.internal:11434/v1"
    # Fallback to default OpenAI URL
    return None

# 24 hour TTL (86400 seconds)
CACHE_TTL = 86400

def hash_prompt(system: str, user: str) -> str:
    """Create a deterministic hash of the prompt for caching."""
    content = f"{system}:::{user}".encode("utf-8")
    return hashlib.sha256(content).hexdigest()

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(RateLimitError),
    before_sleep=lambda retry_state: logger.warning(f"Rate limited. Retrying attempt {retry_state.attempt_number}...")
)
async def generate_completion(system_prompt: str, user_prompt: str, response_format: dict | None = None) -> str:
    """
    Generates a completion from the LLM, wrapped in cache, throttle, and tenacity retries.
    """
    prompt_hash = hash_prompt(system_prompt, user_prompt)
    cache_key = f"llm_cache:{prompt_hash}"

    async with Redis.from_url(settings.redis_url, decode_responses=True) as redis_client:
        # 1. Check Cache
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            logger.info("Cache hit for LLM extraction.")
            return cached_result
    
        # 2. Throttle
        # Prevent burst spikes by sleeping a small amount before the actual outgoing request
        await asyncio.sleep(1.5)
    
        # 3. Call LLM
        logger.info(f"Calling LLM ({settings.llm_provider} - {settings.llm_model})")
        
        llm_client = AsyncOpenAI(
            api_key=settings.llm_api_key or "placeholder",
            base_url=get_base_url(settings.llm_provider)
        )
        
        kwargs = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.0
        }
        
        if response_format:
            kwargs["response_format"] = response_format
    
        response = await llm_client.chat.completions.create(**kwargs)
        result = response.choices[0].message.content
    
        # 4. Cache Result with TTL
        await redis_client.set(cache_key, result, ex=CACHE_TTL)
        
        return result
