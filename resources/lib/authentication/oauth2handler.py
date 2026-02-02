# SPDX-License-Identifier: GPL-3.0-or-later

import base64
import hashlib
import time
import urllib.parse
import secrets
from abc import ABC, abstractmethod
from typing import Optional, Tuple

try:
    import jwt
except ImportError:
    try:
        import pyjwt as jwt
    except ImportError:
        # PyJWT's cryptography dependency uses Rust (PyO3) bindings, which don't support
        # Python 3.14 subinterpreters yet (https://github.com/PyO3/pyo3/issues/576).
        # This shim provides bare-minimum JWT payload decoding without signature verification.
        import json

        class _JwtFallback:

            @staticmethod
            def decode(token, **_kwargs):
                try:
                    payload = token.split('.')[1]
                    padding = 4 - len(payload) % 4
                    if padding != 4:
                        payload += '=' * padding
                    return json.loads(base64.urlsafe_b64decode(payload))
                except (IndexError, ValueError):
                    return {}

        jwt = _JwtFallback()

from resources.lib.authentication.authenticationhandler import AuthenticationHandler
from resources.lib.authentication.authenticationresult import AuthenticationResult
from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger

class OAuth2Handler(AuthenticationHandler, ABC):
    """Generic OAuth2 PKCE Handler for Retrospect."""

    def __init__(self, realm: str, client_id: str):
        super(OAuth2Handler, self).__init__(realm, device_id=None)
        self.client_id_val = client_id
        # Use client-specific prefix to prevent storage collisions between different OAuth clients
        # e.g., "nlziet_oauth2_triple-web_" vs "nlziet_oauth2_triple-android-tv_"
        self.prefix = f"{realm}_oauth2_{client_id}_"

    @property
    @abstractmethod
    def base_auth_url(self) -> str:
        pass

    @property
    @abstractmethod
    def token_endpoint(self) -> str:
        pass

    @property
    @abstractmethod
    def redirect_uri(self) -> str:
        pass

    @property
    def scopes(self) -> list:
        """Default OAuth2 scopes. Override in subclass for specific needs."""
        return ["openid", "profile", "email", "offline_access"]

    def _generate_pkce(self) -> Tuple[str, str]:
        """Generate PKCE verifier and challenge."""
        verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode().rstrip('=')
        digest = hashlib.sha256(verifier.encode()).digest()
        challenge = base64.urlsafe_b64encode(digest).decode().rstrip('=')
        return verifier, challenge

    def get_auth_url_and_verifier(self) -> Tuple[str, str, str]:
        """Generate authorization URL with PKCE parameters."""
        verifier, challenge = self._generate_pkce()
        state = secrets.token_urlsafe(32)

        params = {
            "client_id": self.client_id_val,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "redirect_uri": self.redirect_uri,
            "state": state
        }
        return f"{self.base_auth_url}?{urllib.parse.urlencode(params)}", verifier, state

    def _request_tokens(self, data: dict):
        """Make token request and store results."""
        try:
            response = UriHandler.open(self.token_endpoint, data=data, no_cache=True)
            tokens = JsonHelper(response).json
            self._store_tokens(tokens)
        except Exception as e:
            Logger.error(f"OAuth2: Token request failed for {self.realm}: {e}")
            raise

    def _store_tokens(self, tokens: dict):
        """Persist token fields to addon settings."""
        AddonSettings.set_setting(f"{self.prefix}access_token", tokens["access_token"], store=LOCAL)
        if "refresh_token" in tokens:
            AddonSettings.set_setting(f"{self.prefix}refresh_token", tokens["refresh_token"], store=LOCAL)

        expires_in = tokens.get("expires_in", 3600)
        AddonSettings.set_setting(f"{self.prefix}expires_at", str(int(time.time()) + expires_in), store=LOCAL)

    def exchange_code(self, code: str, verifier: str) -> bool:
        """Exchange authorization code for tokens.

        :param code:        The authorization code from OAuth2 provider
        :param verifier:    The PKCE verifier
        :return:            True if exchange successful, False otherwise

        """
        try:
            data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id_val,
                "code": code,
                "redirect_uri": self.redirect_uri,
                "code_verifier": verifier
            }
            self._request_tokens(data)
            return True
        except Exception as e:
            Logger.error(f"OAuth2: exchange_code failed for {self.realm}: {e}")
            return False

    def refresh_access_token(self):
        """Refresh the access token using the refresh token."""
        refresh_token = AddonSettings.get_setting(f"{self.prefix}refresh_token", store=LOCAL)
        if not refresh_token:
            raise ValueError("No refresh token available.")

        Logger.debug(f"OAuth2: Refreshing access token for {self.realm}")
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id_val,
            "refresh_token": refresh_token
        }
        self._request_tokens(data)

    def get_valid_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary."""
        expires_at = int(AddonSettings.get_setting(f"{self.prefix}expires_at", store=LOCAL) or 0)

        if time.time() > (expires_at - 60):
            try:
                self.refresh_access_token()
            except Exception as e:
                Logger.warning(f"OAuth2: Token refresh failed for {self.realm}: {e}")
                return None
        else:
            Logger.trace(f"OAuth2: Using cached token for {self.realm}")

        return AddonSettings.get_setting(f"{self.prefix}access_token", store=LOCAL)

    def _extract_username_from_token(self, token: str) -> Optional[str]:
        """Extract username from JWT token."""
        if not token:
            return None
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            return (decoded.get("email") or
                    decoded.get("preferred_username") or
                    decoded.get("nickname") or
                    decoded.get("sub"))
        except Exception as e:
            Logger.error(f"OAuth2: Could not decode username from token: {e}")
            return None

    def active_authentication(self) -> AuthenticationResult:
        """Check for active authentication session."""
        token = self.get_valid_token()
        if token:
            username = self._extract_username_from_token(token)
            return AuthenticationResult(username or "OAuth2 User", existing_login=True, jwt=token)
        return AuthenticationResult(None)

    def get_authentication_token(self) -> Optional[str]:
        """Get the current authentication token."""
        return self.get_valid_token()

    def log_on(self, username: str, password: str) -> AuthenticationResult:
        """OAuth2 requires browser-based login."""
        return AuthenticationResult(None, error="OAuth2 requires browser login.")

    def _clear_token_settings(self) -> None:
        AddonSettings.set_setting(f"{self.prefix}access_token", "", store=LOCAL)
        AddonSettings.set_setting(f"{self.prefix}refresh_token", "", store=LOCAL)
        AddonSettings.set_setting(f"{self.prefix}expires_at", "", store=LOCAL)

    def log_off(self, username) -> bool:
        """Clear stored tokens."""
        self._clear_token_settings()
        Logger.info(f"OAuth2: Logged off user for {self.realm}")
        return True
