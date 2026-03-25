# SPDX-License-Identifier: GPL-3.0-or-later

import json
import os
import time
from typing import List, Optional

from resources.lib.logger import Logger
from resources.lib.retroconfig import Config


_SECONDS_PER_DAY = 24 * 60 * 60
_USER_AGENTS_URL = "https://jnrbsn.github.io/user-agents/user-agents.json"
_USER_AGENTS_CACHE_DAYS = 7
_USER_AGENTS_CACHE_FILE = "user_agent_cache.json"
_USER_AGENTS_FETCH_TIMEOUT = 5
FALLBACK_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
)


class UserAgentHelper(object):
    """Resolve the default modern User-Agent for outbound web requests."""

    def __init__(self):
        raise NotImplementedError()


    @staticmethod
    def _fetch_and_cache_user_agents(source_url: str, cache_filename: str) -> Optional[List[str]]:
        """Fetch a fresh user-agent list from source and write it to cache."""

        try:
            import requests as _requests
            Logger.debug("UserAgent: Fetching fresh user agents list")
            response = _requests.get(source_url, timeout=_USER_AGENTS_FETCH_TIMEOUT)
            if response.status_code != 200:
                Logger.warning(f"UserAgent: Fetch returned HTTP {response.status_code}")
                return None

            user_agents = response.json()
            if (not isinstance(user_agents, list) or
                not user_agents):
                Logger.warning(f"UserAgent: Expected list, got {type(user_agents).__name__}")
                return None

            os.makedirs(Config.cacheDir, exist_ok=True)
            cache_path = os.path.join(Config.cacheDir, cache_filename)
            with open(cache_path, 'w') as f:
                json.dump(user_agents, f)

            Logger.debug(f"UserAgent: Cached {len(user_agents)} user agents")
            return user_agents
        except Exception as e:
            Logger.error(f"UserAgent: Failed to fetch user agents: {e}")
            return None


    @staticmethod
    def _load_cached_user_agents(cache_filename: str, max_age_days: int) -> Optional[List[str]]:
        """Load cached user agents if the cache is still fresh."""

        cache_path = os.path.join(Config.cacheDir, cache_filename)
        if not os.path.exists(cache_path):
            return None

        try:
            cache_mtime = os.path.getmtime(cache_path)
            cache_age_seconds = time.time() - cache_mtime
            max_age_seconds = max_age_days * _SECONDS_PER_DAY
            if cache_age_seconds >= max_age_seconds:
                return None

            with open(cache_path, 'r') as f:
                user_agents = json.load(f)

            if (not isinstance(user_agents, list) or
                not user_agents):
                Logger.warning(f"UserAgent: Expected cached list, got {type(user_agents).__name__}")
                return None

            Logger.trace("UserAgent: Using cached user agents")
            return user_agents
        except (OSError, ValueError, TypeError) as e:
            Logger.warning(f"UserAgent: Failed to load cached user agents: {e}")
            return None


    @staticmethod
    def get_user_agent() -> str:
        """
        Return a modern default User-Agent string.

        Tries the local cache first. On a cache miss, fetches a fresh list from
        the upstream source and caches it. Falls back to the bundled modern
        browser User-Agent if both fail.
        """

        user_agents = UserAgentHelper._load_cached_user_agents(
            _USER_AGENTS_CACHE_FILE,
            _USER_AGENTS_CACHE_DAYS
        )
        if not user_agents:
            user_agents = UserAgentHelper._fetch_and_cache_user_agents(
                _USER_AGENTS_URL,
                _USER_AGENTS_CACHE_FILE
            )
        if user_agents:
            return user_agents[0]

        Logger.debug("UserAgent: Using fallback user agent")
        return FALLBACK_USER_AGENT
