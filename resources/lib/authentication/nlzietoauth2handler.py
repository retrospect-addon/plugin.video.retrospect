# SPDX-License-Identifier: GPL-3.0-or-later

import json
import os
import re
import secrets
import time
from typing import Optional
from urllib.parse import urlencode, urlparse, parse_qs

from resources.lib.authentication.oauth2handler import OAuth2Handler
from resources.lib.authentication.authenticationresult import AuthenticationResult
from resources.lib.urihandler import UriHandler
from resources.lib.logger import Logger
from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.retroconfig import Config
from http import HTTPStatus

try:
    import requests
except ImportError:
    requests = None


class NLZIETOAuth2Handler(OAuth2Handler):
    """NLZiet OAuth2 authentication handler supporting both web and device flows.

    Implements the publicly known NLZiet OAuth2 authentication mechanism with
    support for headless browser-based login and RFC 8628 device flow for TV devices.

    Web flow: Uses triple-web client with PKCE and silent refresh
    Device flow: Uses triple-android-tv client with refresh tokens
    """
    USER_AGENTS_URL = "https://jnrbsn.github.io/user-agents/user-agents.json"
    USER_AGENTS_CACHE_DAYS = 7
    USER_AGENTS_CACHE_FILE = "user_agent_cache.json"
    USER_AGENTS_FETCH_TIMEOUT = 10
    FALLBACK_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

    WEB_CLIENT_ID = "triple-web"
    TV_CLIENT_ID = "triple-android-tv"

    BASE_AUTH_URL = "https://id.nlziet.nl/connect/authorize"
    TOKEN_ENDPOINT = "https://id.nlziet.nl/connect/token"
    LOGIN_ENDPOINT = "https://id.nlziet.nl/account/login"
    DEVICE_AUTH_ENDPOINT = "https://id.nlziet.nl/connect/deviceauthorization"
    DEVICE_PORTAL_URL = "https://id.nlziet.nl/device"
    USERINFO_ENDPOINT = "https://id.nlziet.nl/connect/userinfo"
    REDIRECT_URI = "https://app.nlziet.nl/callback"
    SESSION_API_ENDPOINT = "https://id.nlziet.nl/api/session"
    SESSION_REVOKE_ENDPOINT = "https://id.nlziet.nl/api/session/revoke"
    PROFILE_API_ENDPOINT = "https://api.nlziet.nl/v8/profile"

    AUTH_METHOD_SETTING = "nlziet_auth_method"

    def __init__(self, use_device_flow: Optional[bool] = None):
        """Initialize NLZiet OAuth2 handler.

        Reads the stored auth method from settings to determine which client to
        use. If no method is stored (new user), defaults to device flow.

        :param use_device_flow: Optional override (mainly for tests).
                                If None, reads from stored settings.
        """
        if use_device_flow is None:
            stored = AddonSettings.get_setting(self.AUTH_METHOD_SETTING, store=LOCAL)
            use_device_flow = stored != "web"

        self._use_device_flow = use_device_flow
        client_id = self.TV_CLIENT_ID if use_device_flow else self.WEB_CLIENT_ID
        super(NLZIETOAuth2Handler, self).__init__(realm="nlziet", client_id=client_id)
        # id_token is NLZIET-specific; used for web-flow silent re-authentication.
        self._id_token = AddonSettings.get_setting(f"{self.prefix}id_token", store=LOCAL) or ""

    @property
    def base_auth_url(self) -> str: return self.BASE_AUTH_URL

    @property
    def use_device_flow(self) -> bool: return self._use_device_flow

    @property
    def profile_type(self) -> str:
        return AddonSettings.get_setting(f"{self.prefix}profile_type", store=LOCAL) or ""

    @property
    def token_endpoint(self) -> str: return self.TOKEN_ENDPOINT

    @property
    def redirect_uri(self) -> str: return self.REDIRECT_URI

    @property
    def scopes(self) -> list: return ["openid", "api"]

    @staticmethod
    def _load_cached_user_agents(cache_filename: str, max_age_days: int) -> Optional[list]:
        """Load user agents from cache if fresh enough."""
        cache_path = os.path.join(Config.cacheDir, cache_filename)

        if not os.path.exists(cache_path):
            return None

        try:
            cache_mtime = os.path.getmtime(cache_path)
            cache_age_seconds = time.time() - cache_mtime
            max_age_seconds = max_age_days * 24 * 3600

            if cache_age_seconds >= max_age_seconds:
                return None

            with open(cache_path, 'r') as f:
                user_agents = json.load(f)
            Logger.trace("NLZiet: Using cached user agents")
            return user_agents
        except Exception as e:
            Logger.warning(f"NLZiet: Failed to load cached user agents: {e}")
            return None

    @staticmethod
    def _fetch_and_cache_user_agents(source_url: str, cache_filename: str) -> Optional[list]:
        """Fetch fresh user agents from source and cache them."""
        if requests is None:
            Logger.debug("NLZiet: 'requests' module not available, skipping user agent fetch")
            return None

        try:
            Logger.debug("NLZiet: Fetching fresh user agents list")
            response = requests.get(source_url, timeout=NLZIETOAuth2Handler.USER_AGENTS_FETCH_TIMEOUT)
            if response.status_code != HTTPStatus.OK:
                return None

            user_agents = response.json()
            cache_path = os.path.join(Config.cacheDir, cache_filename)

            os.makedirs(Config.cacheDir, exist_ok=True)
            with open(cache_path, 'w') as f:
                json.dump(user_agents, f)

            Logger.debug(f"NLZiet: Cached {len(user_agents)} user agents")
            return user_agents
        except Exception as e:
            Logger.warning(f"NLZiet: Failed to fetch user agents: {e}")
            return None

    @staticmethod
    def _get_latest_user_agent() -> str:
        """Get latest browser user agent string, cached for 7 days.

        Returns the first (most common) user agent from jnrbsn's list, or a fallback.
        """
        user_agents = NLZIETOAuth2Handler._load_cached_user_agents(
            NLZIETOAuth2Handler.USER_AGENTS_CACHE_FILE,
            NLZIETOAuth2Handler.USER_AGENTS_CACHE_DAYS
        )

        if not user_agents:
            user_agents = NLZIETOAuth2Handler._fetch_and_cache_user_agents(
                NLZIETOAuth2Handler.USER_AGENTS_URL,
                NLZIETOAuth2Handler.USER_AGENTS_CACHE_FILE
            )

        if user_agents:
            return user_agents[0]

        Logger.debug("NLZiet: Using fallback user agent")
        return NLZIETOAuth2Handler.FALLBACK_USER_AGENT

    def _request_tokens(self, data: dict):
        """Override to also store id_token for NLZiet silent auth."""
        try:
            response = UriHandler.open(self.token_endpoint, data=data, no_cache=True)
            tokens = JsonHelper(response).json
            self._store_tokens(tokens)
        except Exception as e:
            Logger.error(f"OAuth2: Token request failed for {self.realm}: {e}")
            raise

    def _store_tokens(self, tokens: dict):
        """Override to also store id_token for NLZiet silent auth."""
        super()._store_tokens(tokens)
        if "id_token" in tokens:
            self._id_token = tokens["id_token"]
            AddonSettings.set_setting(f"{self.prefix}id_token", self._id_token, store=LOCAL)
            Logger.debug(f"OAuth2: Stored id_token for {self.realm} silent auth")

    def _exchange_code_with_verifier(self, auth_code: str, code_verifier: str):
        """Exchange authorization code for tokens with explicit code verifier."""
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id_val,
            "code": auth_code,
            "redirect_uri": f"{self.redirect_uri}-silent.html",
            "code_verifier": code_verifier
        }
        self._request_tokens(data)

    def _do_token_refresh(self):
        """Unconditional token refresh: uses refresh_token (device flow) or silent re-auth (web flow)."""
        if self._refresh_token:
            Logger.debug(f"OAuth2: Refreshing access token using refresh_token for {self.realm}")
            super()._do_token_refresh()
            return

        if not self._id_token:
            raise ValueError("No refresh_token or id_token available for authentication.")

        Logger.debug(f"OAuth2: Attempting silent re-authentication for {self.realm}")

        code_verifier, code_challenge = self._generate_pkce()
        headers = {"User-Agent": self._get_latest_user_agent()}

        state = secrets.token_urlsafe(24)
        auth_params = {
            "response_type": "code",
            "client_id": self.client_id_val,
            "scope": " ".join(self.scopes),
            "redirect_uri": f"{self.redirect_uri}-silent.html",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "response_mode": "query",
            "prompt": "none",
            "id_token_hint": self._id_token
        }

        auth_url = f"{self.base_auth_url}?{urlencode(auth_params)}"

        try:
            response = UriHandler.open(auth_url, no_cache=True, additional_headers=headers)
            final_url = UriHandler.instance().status.url

            parsed = urlparse(final_url)
            params = parse_qs(parsed.query)

            if "code" not in params:
                raise RuntimeError("Silent auth failed: no authorization code in redirect")

            received_state = params.get("state", [None])[0]
            if received_state != state:
                raise RuntimeError(f"Silent auth state mismatch: expected {state}, got {received_state}")

            auth_code = params["code"][0]
            Logger.debug(f"OAuth2: Silent auth successful, exchanging code for tokens")

            self._exchange_code_with_verifier(auth_code, code_verifier)

        except Exception as e:
            Logger.warning(f"OAuth2: Silent re-authentication failed for {self.realm}: {e}")
            self._id_token = ""
            self._access_token = ""
            AddonSettings.set_setting(f"{self.prefix}id_token", "", store=LOCAL)
            AddonSettings.set_setting(f"{self.prefix}access_token", "", store=LOCAL)
            raise

    def _set_profile_settings(self, profile_id: str = "", display_name: str = "", profile_type: str = "") -> None:
        AddonSettings.set_setting(f"{self.prefix}profile_id", profile_id, store=LOCAL)
        AddonSettings.set_setting(f"{self.prefix}profile_name", display_name, store=LOCAL)
        AddonSettings.set_setting(f"{self.prefix}profile_type", profile_type, store=LOCAL)

    def list_profiles(self) -> Optional[list]:
        """Get list of available profiles for the authenticated user.

        :return: List of profile dicts with id, displayName, type, color fields, or None on failure.
        """
        try:
            access_token = self.get_valid_token()
            if not access_token:
                Logger.warning("NLZIET: No access token available for profile list")
                return None

            Logger.debug("NLZIET: Fetching profile list")

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }

            response = UriHandler.open(
                self.PROFILE_API_ENDPOINT,
                additional_headers=headers,
                no_cache=True
            )

            status = UriHandler.instance().status
            if status.error and status.code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
                Logger.warning("NLZIET: Profile API returned %s, attempting token refresh", status.code)
                try:
                    self._do_token_refresh()
                    access_token = self.get_valid_token()
                    if not access_token:
                        Logger.warning("NLZIET: Token refresh did not yield an access token")
                        return None
                    headers["Authorization"] = f"Bearer {access_token}"
                    response = UriHandler.open(
                        self.PROFILE_API_ENDPOINT,
                        additional_headers=headers,
                        no_cache=True
                    )
                    status = UriHandler.instance().status
                    if status.error:
                        Logger.error("NLZIET: Profile API still failing after refresh: %s", status.code)
                        return None
                except Exception as e:
                    Logger.warning(f"NLZIET: Token refresh failed: {e}")
                    self._clear_token_settings()
                    return None
            elif not response:
                Logger.error("NLZIET: Empty response from profile API")
                return None

            profiles = JsonHelper(response)
            profile_list = profiles.get_value()

            if not isinstance(profile_list, list):
                Logger.error("NLZIET: Expected profile list, got: %s", type(profile_list))
                return None

            Logger.debug(f"NLZIET: Found {len(profile_list)} profile(s)")
            known_types = {"Adult", "ChildYoung"}
            for profile in profile_list:
                ptype = profile.get("type", "")
                if ptype not in known_types:
                    Logger.warning("NLZIET: Unknown profile type '%s' for '%s'",
                                   ptype, profile.get("displayName", "?"))
            return profile_list

        except Exception as e:
            Logger.error(f"NLZIET: Failed to list profiles: {e}", exc_info=True)
            return None

    def get_nlziet_profile(self, profile_id: str) -> Optional[dict]:
        """Get a specific profile by ID.

        :param profile_id: The unique ID of the profile to find.
        :return: Profile dict if found, None otherwise.
        """
        profiles = self.list_profiles()
        if not profiles:
            return None

        for profile in profiles:
            if profile.get("id") == profile_id:
                return profile

        Logger.warning(f"NLZIET: Profile with ID {profile_id[:20]}... not found")
        return None

    def get_profile(self) -> Optional[dict]:
        """Get the currently selected profile.

        Retrieves the profile ID from settings and validates it still exists.
        If the profile was deleted (e.g., via web UI), returns None and clears the setting.
        If the API call fails, preserves the stored profile selection.

        :return: Profile dict if selected profile exists, None if no profile selected or deleted.
        """
        profile_id = AddonSettings.get_setting(f"{self.prefix}profile_id", store=LOCAL)
        if not profile_id:
            Logger.debug("NLZIET: No profile selected")
            return None

        profiles = self.list_profiles()
        if profiles is None:
            Logger.warning("NLZIET: Cannot verify profile - API call failed, preserving selection")
            return None

        for profile in profiles:
            if profile.get("id") == profile_id:
                Logger.debug(f"NLZIET: Current profile: {profile['displayName']} (type: {profile['type']})")
                return profile

        Logger.warning(f"NLZIET: Selected profile {profile_id[:20]}... no longer exists - clearing selection")
        self._set_profile_settings()
        return None

    def set_profile(self, profile_id: str) -> bool:
        """Set the selected profile and exchange the token for a profile-scoped one.

        Validates the profile exists, then performs a token exchange at the
        ``/connect/token`` endpoint with ``grant_type=profile``.  The returned
        access token is scoped to the selected profile, which is required for
        the API to apply profile-level content filtering (e.g. kids profiles).

        :param profile_id: The unique ID of the profile to select.
        :return: True if profile was validated, token exchanged and stored.
        """
        profile = self.get_nlziet_profile(profile_id)
        if not profile:
            Logger.error(f"NLZIET: Cannot set profile - profile ID {profile_id[:20]}... not found")
            return False

        access_token = self.get_valid_token()
        if not access_token:
            Logger.error("NLZIET: No access token available for profile switch")
            return False

        data = {
            "client_id": self.client_id_val,
            "profile": profile_id,
            "scope": "openid api",
            "grant_type": "profile"
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        try:
            response = UriHandler.open(
                self.token_endpoint, data=data,
                additional_headers=headers, no_cache=True)
            tokens = JsonHelper(response).json
            self._store_tokens(tokens)
        except Exception as e:
            Logger.error(f"NLZIET: Profile token exchange failed: {e}")
            return False

        self._set_profile_settings(profile_id, profile["displayName"], profile["type"])
        Logger.info(f"NLZIET: Switched to profile '{profile['displayName']}' (type: {profile['type']})")
        return True

    def clear_profile(self) -> None:
        """Clear the currently selected profile."""
        self._set_profile_settings()
        Logger.info("NLZIET: Profile selection cleared")

    def list_devices(self, access_token: str = None) -> Optional[list]:
        """List all linked devices for the current user.

        :param access_token: Optional access token. If not provided, uses stored token.
        :return: List of device sessions, or None on error.

        Example response:
        [
            {
                "key": "session_key_string",
                "name": "My Device",
                "lastActivityUtc": "2026-02-18T12:34:56Z",
                ...
            }
        ]
        """
        try:
            Logger.debug("NLZIET: Fetching device list")

            headers = {
                "User-Agent": self._get_latest_user_agent(),
                "Origin": "https://mijn.nlziet.nl",
                "Referer": "https://mijn.nlziet.nl/",
                "Accept": "application/json, text/plain, */*"
            }

            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"

            response = UriHandler.open(
                self.SESSION_API_ENDPOINT,
                additional_headers=headers,
                no_cache=True
            )

            data = JsonHelper(response).json

            if isinstance(data, dict) and "sessions" in data:
                sessions = data["sessions"]
                Logger.debug(f"NLZIET: Found {len(sessions)} device(s)")
                return sessions
            elif isinstance(data, list):
                Logger.debug(f"NLZIET: Found {len(data)} device(s)")
                return data
            else:
                Logger.error(f"NLZIET: Unexpected response format: {type(data)}")
                return []

        except Exception as e:
            Logger.error(f"NLZIET: Failed to list devices: {e}", exc_info=True)
            return None

    def start_device_flow(self, device_name: str,
                          device_client_id: Optional[str] = None) -> Optional[dict]:
        """Start OAuth2 device authorization flow (RFC 8628).

        This starts the device flow where the user authenticates on another device.

        :param device_name: Device name to display in user's account
        :param device_client_id: Optional client ID for device flow (defaults to self.client_id_val)
        :return: Dict with device_code, user_code, verification_uri, etc., or None on error

        Example response:
        {
            "device_code": "...",
            "user_code": "GHM77G",
            "verification_uri": "https://nlziet.nl/koppel",
            "verification_uri_complete": "https://nlziet.nl/koppel?user_code=GHM77G",
            "expires_in": 900,
            "interval": 5
        }
        """
        client_id = device_client_id or self.client_id_val
        headers = {"User-Agent": self._get_latest_user_agent()}

        device_scopes = self.scopes + ["offline_access"]

        data = {
            "client_id": client_id,
            "scope": " ".join(device_scopes),
            "device_name": device_name
        }

        try:
            Logger.info(f"NLZIET: Starting device flow with client_id={client_id}")
            response = UriHandler.open(
                self.DEVICE_AUTH_ENDPOINT,
                data=data,
                additional_headers=headers,
                no_cache=True
            )

            result = JsonHelper(response).json
            if "device_code" not in result or "user_code" not in result:
                Logger.error(f"NLZIET: Invalid device flow response: {result}")
                return None

            Logger.info(f"NLZIET: Device flow started. User code: {result.get('user_code')}")
            return result

        except OSError:
            Logger.error("NLZIET: Device flow start failed (connection error)", exc_info=True)
            raise
        except Exception as e:
            Logger.error(f"NLZIET: Device flow start failed: {e}", exc_info=True)
            return None

    def poll_device_flow_once(self, device_code: str,
                             device_client_id: Optional[str] = None) -> str:
        """Perform a single device flow poll attempt.

        :param device_code: The device_code from start_device_flow()
        :param device_client_id: Optional client ID for device flow
        :return: "pending", "slow_down", "success", or an error string
        """
        client_id = device_client_id or self.client_id_val
        headers = {"User-Agent": self._get_latest_user_agent()}

        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
            "client_id": client_id
        }

        try:
            response = UriHandler.open(
                self.token_endpoint,
                data=data,
                additional_headers=headers,
                no_cache=True
            )

            tokens = JsonHelper(response).json

            if "error" in tokens:
                error = tokens["error"]
                if error in ("authorization_pending", "slow_down"):
                    return error
                Logger.warning(f"NLZIET: Device flow error: {error}")
                return error

            if "access_token" in tokens:
                Logger.info("NLZIET: Device flow authentication successful!")
                self._store_tokens(tokens)
                AddonSettings.set_setting(self.AUTH_METHOD_SETTING, "device", store=LOCAL)
                return "success"

            return "unknown_response"

        except Exception as e:
            Logger.error(f"NLZIET: Device flow polling error: {e}", exc_info=True)
            return "error"

    def poll_device_flow(self, device_code: str, interval: int = 5,
                        expires_in: int = 900, device_client_id: Optional[str] = None,
                        max_attempts: int = 12) -> bool:
        """Poll for device flow completion.

        Polls the token endpoint until the user completes authentication or timeout occurs.

        :param device_code: The device_code from start_device_flow()
        :param interval: Polling interval in seconds (from device flow response)
        :param expires_in: How long to poll before giving up (from device flow response)
        :param device_client_id: Optional client ID for device flow
        :param max_attempts: Maximum number of polling attempts (default: 12 = ~1 min at 5s intervals)
        :return: True if authentication succeeded, False otherwise
        """

        end_time = time.time() + expires_in
        current_interval = interval
        attempts = 0

        Logger.info(f"NLZIET: Polling for device flow completion (max {max_attempts} attempts, {expires_in}s timeout)")

        while time.time() < end_time and attempts < max_attempts:
            time.sleep(current_interval)
            attempts += 1

            result = self.poll_device_flow_once(device_code, device_client_id)

            if result == "authorization_pending":
                Logger.trace(f"NLZIET: Still waiting for user authorization (attempt {attempts}/{max_attempts})...")
                if attempts > 5:
                    current_interval = min(current_interval + 2, 15)
                continue

            if result == "slow_down":
                current_interval += 5
                Logger.debug(f"NLZIET: Server requested slow down, interval now {current_interval}s")
                continue

            if result == "success":
                return True

            if result == "error":
                time.sleep(current_interval)
                continue

            return False

        if attempts >= max_attempts:
            Logger.warning(f"NLZIET: Device flow stopped after {max_attempts} attempts")
        else:
            Logger.warning("NLZIET: Device flow timed out")
        return False

    def log_on_with_device_flow(self, device_name: str, device_client_id: Optional[str] = None,
                                display_callback=None) -> AuthenticationResult:
        """Perform device flow authentication.

        :param device_name: Device name to register (e.g., "Living Room Kodi")
        :param device_client_id: Optional client ID for device flow
        :param display_callback: Optional callback function(user_code, verification_uri, verification_uri_complete)
                                to display the code to the user. If None, logs to Logger.
        :return: AuthenticationResult with login status
        """
        device_flow = self.start_device_flow(device_name, device_client_id)
        if not device_flow:
            return AuthenticationResult(None, error="Failed to start device flow")

        user_code = device_flow.get("user_code")
        verification_uri = device_flow.get("verification_uri", self.DEVICE_PORTAL_URL)
        verification_uri_complete = device_flow.get("verification_uri_complete")
        expires_in = device_flow.get("expires_in", 900)
        interval = device_flow.get("interval", 5)

        if display_callback:
            display_callback(user_code, verification_uri, verification_uri_complete)
        else:
            Logger.info("=" * 60)
            Logger.info(f"NLZIET Device Flow Authentication")
            Logger.info(f"1. Go to: {verification_uri}")
            Logger.info(f"2. Enter code: {user_code}")
            if verification_uri_complete:
                Logger.info(f"Or visit: {verification_uri_complete}")
            Logger.info(f"Waiting up to {expires_in // 60} minutes for you to complete...")
            Logger.info("=" * 60)

        if not self.poll_device_flow(device_flow["device_code"], interval, expires_in, device_client_id):
            return AuthenticationResult(None, error="Device flow authentication failed or timed out")

        token = self.get_valid_token()
        if not token:
            return AuthenticationResult(None, error="Failed to retrieve authentication token")

        extracted_username = self._extract_username_from_token(token)
        return AuthenticationResult(
            username=extracted_username or "NLZiet User",
            existing_login=False,
            jwt=token
        )

    def remove_device(self, session_key: str, access_token: str = None) -> bool:
        """Remove a linked device by its session key.

        :param session_key: The session key of the device to remove.
        :param access_token: Optional access token. If not provided, uses stored token.
        :return: True if successful, False otherwise.
        """
        if not session_key:
            Logger.error("NLZIET: Cannot remove device - no session key provided")
            return False

        try:
            Logger.debug(f"NLZIET: Removing device with key: {session_key[:20]}...")

            headers = {
                "User-Agent": self._get_latest_user_agent(),
                "Origin": "https://mijn.nlziet.nl",
                "Referer": "https://mijn.nlziet.nl/",
                "Accept": "application/json, text/plain, */*"
            }

            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"

            UriHandler.open(
                f"{self.SESSION_REVOKE_ENDPOINT}/{session_key}",
                additional_headers=headers,
                no_cache=True,
                method="DELETE"
            )

            Logger.info("NLZIET: Device removed successfully")
            return True

        except Exception as e:
            Logger.error(f"NLZIET: Failed to remove device: {e}", exc_info=True)
            return False

    def get_user_info(self) -> Optional[dict]:
        """Get user information using the current access token.

        :return: Dictionary with user info (email, name, etc.) or None on error.
        """
        token = self.get_valid_token()
        if not token:
            Logger.error("NLZIET: No valid token available for userinfo request")
            return None

        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": self._get_latest_user_agent()
        }

        try:
            Logger.debug("NLZIET: Requesting user info from /connect/userinfo")
            response = UriHandler.open(
                self.USERINFO_ENDPOINT,
                additional_headers=headers,
                no_cache=True
            )

            userinfo = JsonHelper(response).json
            Logger.debug(f"NLZIET: User info retrieved for: {userinfo.get('email', 'N/A')}")
            return userinfo

        except Exception as e:
            Logger.error(f"NLZIET: Failed to get user info: {e}", exc_info=True)
            return None

    def _clear_token_settings(self) -> None:
        super()._clear_token_settings()
        self._id_token = ""
        AddonSettings.set_setting(f"{self.prefix}id_token", "", store=LOCAL)

    def _extract_csrf_token(self, content: str) -> Optional[str]:
        """Extract the RequestVerificationToken CSRF token from HTML.

        :param content:     The HTML response content
        :return:            The CSRF token string, or None if not found

        """
        csrf_pattern = r'name="__RequestVerificationToken".*?value="([^"]+)"'
        csrf = re.search(csrf_pattern, content)
        return csrf.group(1) if csrf else None

    def perform_headless_login(self, username: str, password: str) -> bool:
        """Perform headless OAuth2 PKCE login flow.

        Flow:
        1. GET authorize endpoint -> redirects to login page (302)
        2. GET login page -> extract CSRF token and ReturnUrl
        3. POST credentials to login -> redirects with code (302)
        4. Follow redirect chain to get final callback with auth code
        5. Exchange auth code for tokens
        """
        state = secrets.token_urlsafe(16)
        verifier, challenge = self._generate_pkce()

        headers = {"User-Agent": self._get_latest_user_agent()}

        params = {
            "client_id": self.client_id_val,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "response_mode": "query"
        }

        try:
            Logger.debug(f"NLZIET: Starting authorization at {self.base_auth_url}")
            auth_url = f"{self.base_auth_url}?{urlencode(params)}"

            login_page = UriHandler.open(auth_url, no_cache=True, additional_headers=headers)

            final_url = UriHandler.instance().status.url
            sso_code_match = re.search(r'[?&]code=([^&\s]+)', final_url)
            sso_state_match = re.search(r'[?&]state=([^&\s]+)', final_url)

            if sso_code_match and sso_state_match:
                received_state = sso_state_match.group(1)
                if received_state != state:
                    Logger.error(f"NLZIET: SSO state mismatch! Expected: {state}, Got: {received_state}")
                    return False

                Logger.info("NLZIET: SSO session detected, extracting authorization code from callback")
                auth_code = sso_code_match.group(1)
                Logger.debug(f"NLZIET: SSO authorization code: {auth_code[:10]}...")
                return self.exchange_code(auth_code, verifier)

            csrf_token = self._extract_csrf_token(login_page)

            ret_url_match = re.search(r'<input[^>]*name="ReturnUrl"[^>]*value="([^"]+)"', login_page)
            if not ret_url_match:
                ret_url_match = re.search(r'ReturnUrl=([^&"\s]+)', login_page)

            if not csrf_token:
                Logger.error("NLZIET: Missing CSRF token from login page")
                Logger.debug(f"NLZIET: Page preview: {login_page[:500]}")
                return False
            if not ret_url_match:
                Logger.error("NLZIET: Missing ReturnUrl from login page")
                Logger.debug(f"NLZIET: Page preview: {login_page[:500]}")
                return False

            from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
            return_url = HtmlEntityHelper.convert_html_entities(ret_url_match.group(1))
            Logger.debug(f"NLZIET: Extracted ReturnUrl: {return_url[:100]}...")

            login_data = {
                "ReturnUrl": return_url,
                "EmailAddress": username,
                "Password": password,
                "RememberLogin": "true",
                "button": "login",
                "__RequestVerificationToken": csrf_token
            }

            login_response = UriHandler.open(
                self.LOGIN_ENDPOINT,
                params=urlencode(login_data),
                no_cache=True,
                additional_headers=headers
            )

            final_url = UriHandler.instance().status.url
            Logger.debug(f"NLZIET: Final URL after login POST: {final_url}")

            code_match = re.search(r'[?&]code=([^&\s]+)', final_url)
            state_match = re.search(r'[?&]state=([^&\s]+)', final_url)

            if not code_match:
                Logger.error("NLZIET: No authorization code in final URL")
                Logger.debug(f"NLZIET: Final URL: {final_url}")
                Logger.debug(f"NLZIET: Response preview: {login_response[:500]}")
                return False

            if not state_match:
                Logger.error("NLZIET: No state in final URL")
                return False

            received_state = state_match.group(1)
            if received_state != state:
                Logger.error(f"NLZIET: State mismatch! Expected: {state}, Got: {received_state}")
                return False

            auth_code = code_match.group(1)
            Logger.debug(f"NLZIET: Received authorization code: {auth_code[:10]}...")

            return self.exchange_code(auth_code, verifier)

        except Exception as e:
            Logger.error(f"NLZIET: Login failed with exception: {e}", exc_info=True)
            return False

    def log_on(self, username: str, password: str) -> AuthenticationResult:
        """Framework override to support headless login.

        :param username:    The NLZIET username/email
        :param password:    The NLZIET password
        :return:            AuthenticationResult with login status

        """
        if not username or not password:
            return AuthenticationResult(None, error="Username and password are required.")

        if not self.perform_headless_login(username, password):
            return AuthenticationResult(None, error="NLZIET login failed.")

        AddonSettings.set_setting(self.AUTH_METHOD_SETTING, "web", store=LOCAL)

        token = self.get_valid_token()
        if not token:
            return AuthenticationResult(None, error="Failed to retrieve authentication token.")

        extracted_username = self._extract_username_from_token(token)
        return AuthenticationResult(
            username=extracted_username or username,
            existing_login=False,
            jwt=token
        )

    def log_off(self, username) -> bool:
        self._clear_token_settings()
        self._set_profile_settings()
        Logger.info(f"OAuth2: Logged off user for {self.realm}")
        return True
