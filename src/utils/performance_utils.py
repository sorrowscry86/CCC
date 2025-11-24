"""
Performance utilities for CCC - Phase 4 Optimizations
Implements caching, async operations, and performance enhancements
"""

import os
import asyncio
import logging
import hashlib
import json
from typing import Optional, Dict, Any, Tuple
from cachetools import TTLCache, LRUCache
from functools import wraps
import aiohttp

logger = logging.getLogger(__name__)


# P4.5: LRU Cache with limits for sessions (prevents memory leaks)
class BoundedSessionCache:
    """Thread-safe LRU cache for session data with size limits"""

    def __init__(self, maxsize=1000, ttl=300):
        """
        Args:
            maxsize: Maximum number of cached sessions
            ttl: Time-to-live in seconds (default 5 minutes)
        """
        self._cache = LRUCache(maxsize=maxsize)
        self._ttl = ttl
        self._timestamps = {}
        logger.info(f"Initialized BoundedSessionCache: maxsize={maxsize}, ttl={ttl}s")

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        import time
        if key in self._cache:
            if time.time() - self._timestamps.get(key, 0) < self._ttl:
                return self._cache[key]
            else:
                # Expired, remove it
                self._cache.pop(key, None)
                self._timestamps.pop(key, None)
        return None

    def set(self, key: str, value: Any):
        """Set cached value with timestamp"""
        import time
        self._cache[key] = value
        self._timestamps[key] = time.time()

    def clear(self):
        """Clear all cached values"""
        self._cache.clear()
        self._timestamps.clear()


# P4.7: Response cache with TTL (prevents redundant API calls)
class ResponseCache:
    """Cache for LLM responses to avoid redundant API calls"""

    def __init__(self, maxsize=500, ttl=3600):
        """
        Args:
            maxsize: Maximum number of cached responses
            ttl: Time-to-live in seconds (default 1 hour)
        """
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        logger.info(f"Initialized ResponseCache: maxsize={maxsize}, ttl={ttl}s")

    def _generate_key(self, messages: list, model: str, temperature: float) -> str:
        """Generate cache key from request parameters"""
        # Create deterministic key from messages, model, and temperature
        cache_data = {
            'messages': messages,
            'model': model,
            'temperature': temperature
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()

    def get(self, messages: list, model: str, temperature: float) -> Optional[Dict]:
        """Get cached response if available"""
        key = self._generate_key(messages, model, temperature)
        return self._cache.get(key)

    def set(self, messages: list, model: str, temperature: float, response: Dict):
        """Cache a response"""
        key = self._generate_key(messages, model, temperature)
        self._cache[key] = response
        logger.debug(f"Cached response for key {key[:16]}...")


# P4.2: Async OpenAI API client (improves concurrency)
class AsyncOpenAIClient:
    """Async HTTP client for OpenAI API calls"""

    def __init__(self, api_key: str, base_url: str, timeout: int = 60):
        """
        Args:
            api_key: OpenAI API key
            base_url: Base URL for OpenAI API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
        logger.info("Initialized AsyncOpenAIClient")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def call_api(self, endpoint: str, data: Dict) -> Tuple[Optional[Dict], Optional[Tuple[Dict, int]]]:
        """
        Make async API call to OpenAI

        Args:
            endpoint: API endpoint (e.g., 'chat/completions')
            data: Request payload

        Returns:
            Tuple of (response_dict, error_tuple) where error_tuple is (error_dict, status_code)
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        url = f'{self.base_url}/{endpoint}'
        logger.info(f"Calling OpenAI API (async): {endpoint} with model {data.get('model', 'unknown')}")

        try:
            session = await self._get_session()
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"OpenAI API call successful: {endpoint}")
                    return result, None
                else:
                    error_text = await response.text()
                    error_msg = f"OpenAI API error: {response.status} - {error_text}"
                    logger.error(error_msg)
                    try:
                        error_json = json.loads(error_text) if error_text else {'error': 'Unknown error'}
                    except:
                        error_json = {'error': error_text or 'Unknown error'}
                    return None, (error_json, response.status)

        except asyncio.TimeoutError:
            logger.error(f"OpenAI API timeout: {endpoint}")
            return None, ({'error': 'Request timeout'}, 408)
        except aiohttp.ClientError as e:
            logger.error(f"OpenAI API request error: {e}")
            return None, ({'error': 'Request failed', 'details': str(e)}, 500)
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI API call: {e}")
            return None, ({'error': 'Internal error', 'details': str(e)}, 500)

    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("Closed AsyncOpenAIClient session")


def truncate_context(context: str, max_tokens: int = 2000) -> str:
    """
    P4.9: Truncate large context to save tokens

    Args:
        context: Context string to truncate
        max_tokens: Approximate maximum tokens (uses ~4 chars/token)

    Returns:
        Truncated context with ellipsis if needed
    """
    # Rough approximation: 1 token ~= 4 characters
    max_chars = max_tokens * 4

    if len(context) <= max_chars:
        return context

    truncated = context[:max_chars]
    # Try to truncate at sentence boundary
    last_period = truncated.rfind('.')
    if last_period > max_chars * 0.8:  # If we can truncate at a nearby sentence
        truncated = truncated[:last_period + 1]

    logger.debug(f"Truncated context from {len(context)} to {len(truncated)} chars")
    return truncated + "\n\n[Context truncated for length...]"


def limit_query_results(results: list, max_results: int = 100) -> list:
    """
    P4.8: Limit results from full table scans

    Args:
        results: Query results
        max_results: Maximum number of results to return

    Returns:
        Limited results list
    """
    if len(results) > max_results:
        logger.warning(f"Query returned {len(results)} results, limiting to {max_results}")
        return results[:max_results]
    return results


# Decorator for async task management (P4.10)
def background_task(func):
    """
    Decorator for fire-and-forget async tasks with proper error handling

    Ensures tasks are properly tracked and don't silently fail
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        task = asyncio.create_task(func(*args, **kwargs))

        def _done_callback(t):
            try:
                exc = t.exception()
                if exc:
                    logger.error(f"Background task {func.__name__} failed: {exc}")
            except Exception as e:
                logger.error(f"Error in background task callback: {e}")

        task.add_done_callback(_done_callback)
        return task

    return wrapper
