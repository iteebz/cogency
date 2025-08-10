"""Universal credential detection for any service."""

import os
from pathlib import Path
from typing import Dict, List

# Auto-load .env file for seamless credential detection
try:
    from dotenv import load_dotenv

    # Look for .env file in project root (where cogency is installed)
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, skip auto-loading
    pass


class Credentials:
    """Universal credential detection - works for any service."""

    @staticmethod
    def detect(service: str) -> Dict[str, str]:
        """Detect API keys for any service using standard naming conventions.

        Args:
            service: Service name (e.g., 'openai', 'anthropic', 'mistral')

        Returns:
            Dict with 'api_key' containing single key or list of keys for rotation

        Example:
            >>> Credentials.detect('openai')
            {'api_key': 'sk-...'}  # Single key

            >>> Credentials.detect('openai')  # With OPENAI_API_KEY_1, _2 set
            {'api_key': ['sk-...', 'sk-...']}  # Multiple keys for rotation
        """
        keys = Credentials._detect_from_env(service)
        if not keys:
            return {}

        return {"api_key": keys[0] if len(keys) == 1 else keys}

    @staticmethod
    def for_supabase() -> Dict[str, str]:
        """Supabase-specific credential detection.

        Returns:
            Dict with 'url' and 'service_key' for Supabase connection

        Example:
            >>> Credentials.for_supabase()
            {'url': 'https://abc.supabase.co', 'service_key': 'eyJ...'}
        """
        return {"url": os.getenv("SUPABASE_URL"), "service_key": os.getenv("SUPABASE_SERVICE_KEY")}

    @staticmethod
    def for_database(service: str) -> Dict[str, str]:
        """Database-style services with multiple connection components.

        Args:
            service: Service name (e.g., 'postgres', 'redis')

        Returns:
            Dict with url, key, secret components

        Example:
            >>> Credentials.for_database('postgres')
            {'url': 'postgresql://...', 'key': '...', 'secret': '...'}
        """
        service_upper = service.upper()
        return {
            "url": os.getenv(f"{service_upper}_URL"),
            "key": os.getenv(f"{service_upper}_KEY"),
            "secret": os.getenv(f"{service_upper}_SECRET"),
        }

    @staticmethod
    def _detect_from_env(service: str) -> List[str]:
        """Auto-detect API keys from environment variables for any service.

        Checks for keys in this order:
        1. Numbered keys: SERVICE_API_KEY_1, SERVICE_API_KEY_2, etc.
        2. Base key: SERVICE_API_KEY

        Args:
            service: Service name (e.g., 'openai', 'anthropic', 'mistral')

        Returns:
            List of detected API keys for the service
        """
        keys = []
        env_prefix = service.upper()

        # Try numbered keys first (SERVICE_API_KEY_1, SERVICE_API_KEY_2, etc.)
        numbered_keys = []
        for env_var, value in os.environ.items():
            if env_var.startswith(f"{env_prefix}_API_KEY_") and env_var != f"{env_prefix}_API_KEY":
                try:
                    # Extract the number and store with the key
                    suffix = env_var[len(f"{env_prefix}_API_KEY_") :]
                    key_num = int(suffix)
                    numbered_keys.append((key_num, value))
                except ValueError:
                    # Skip non-numeric suffixes
                    continue

        # Sort by key number and add to keys list
        numbered_keys.sort(key=lambda x: x[0])
        keys.extend([key for _, key in numbered_keys])

        # Fall back to base key if no numbered keys found
        if not keys:
            base_key = os.getenv(f"{env_prefix}_API_KEY")
            if base_key:
                keys.append(base_key)

        return keys


__all__ = ["Credentials"]
