# SPDX-License-Identifier: GPL-3.0-or-later

"""Mock dispatcher for NLZiet OAuth2 tests.

Intercepts UriHandler.open() calls and returns canned responses,
enabling all NLZiet authentication tests to run without credentials.
"""

import base64
import json
import re
from urllib.parse import urlparse, parse_qs

from resources.lib.urihandler import UriStatus


# ============================================================================
# Mock Response Data
# ============================================================================

_JWT_HEADER = base64.urlsafe_b64encode(
    json.dumps({"alg": "RS256", "typ": "JWT"}).encode()
).rstrip(b"=").decode()

_JWT_SIGNATURE = base64.urlsafe_b64encode(
    b"mock_signature_padding_bytes_0123456789abcdef"
).rstrip(b"=").decode()


def _make_jwt(claims: dict) -> str:
    """Build a fake JWT with the given claims."""
    payload = base64.urlsafe_b64encode(
        json.dumps(claims).encode()
    ).rstrip(b"=").decode()
    return f"{_JWT_HEADER}.{payload}.{_JWT_SIGNATURE}"


MOCK_EMAIL = "test@example.com"
MOCK_USER_ID = "mock_user_id_a1b2c3d4"

MOCK_ACCESS_TOKEN = _make_jwt({
    "sub": MOCK_USER_ID,
    "email": MOCK_EMAIL,
    "name": "Test User",
    "iss": "https://id.nlziet.nl",
    "aud": "triple-web",
    "exp": 9999999999,
    "iat": 1700000000,
    "nbf": 1700000000,
    "scope": "openid api"
})

MOCK_ID_TOKEN = _make_jwt({
    "sub": MOCK_USER_ID,
    "email": MOCK_EMAIL,
    "name": "Test User",
    "iss": "https://id.nlziet.nl",
    "aud": "triple-web",
    "exp": 9999999999,
    "iat": 1700000000,
    "nbf": 1700000000,
    "at_hash": "mock_at_hash"
})

MOCK_REFRESH_TOKEN = "mock_refresh_token_x7y8z9w0"
MOCK_DEVICE_CODE = "mock_device_code_ABCDEF1234567890"
MOCK_USER_CODE = "T3ST7K"
MOCK_AUTH_CODE = "mock_auth_code_9876543210FEDCBA"
MOCK_CSRF_TOKEN = "mock_csrf_CgNlLmR2b3J5X2FjY2Vzc19pbnRlZ3JhdGlvbl90ZXN0"
MOCK_SESSION_KEY = "AABB00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDD"
MOCK_INVALID_PASSWORD = "WrongPassword123!"

MOCK_PROFILE_ACCESS_TOKEN = _make_jwt({
    "sub": MOCK_USER_ID,
    "email": MOCK_EMAIL,
    "name": "Test User",
    "iss": "https://id.nlziet.nl",
    "aud": "triple-web",
    "exp": 9999999999,
    "iat": 1700000000,
    "nbf": 1700000000,
    "scope": "openid api",
    "profile": "AAAAAAAA-BBBB-CCCC-DDDD-111111111111"
})

MOCK_TOKEN_RESPONSE = {
    "id_token": MOCK_ID_TOKEN,
    "access_token": MOCK_ACCESS_TOKEN,
    "expires_in": 3600,
    "token_type": "Bearer",
    "scope": "openid api"
}

MOCK_TOKEN_RESPONSE_WITH_REFRESH = {
    "id_token": MOCK_ID_TOKEN,
    "access_token": MOCK_ACCESS_TOKEN,
    "refresh_token": MOCK_REFRESH_TOKEN,
    "expires_in": 3600,
    "token_type": "Bearer",
    "scope": "openid api offline_access"
}

MOCK_PROFILE_TOKEN_RESPONSE = {
    "id_token": MOCK_ID_TOKEN,
    "access_token": MOCK_PROFILE_ACCESS_TOKEN,
    "expires_in": 3600,
    "token_type": "Bearer",
    "scope": "openid api"
}

MOCK_DEVICE_AUTH_RESPONSE = {
    "device_code": MOCK_DEVICE_CODE,
    "user_code": MOCK_USER_CODE,
    "verification_uri": "https://nlziet.nl/koppel",
    "verification_uri_complete": f"https://nlziet.nl/koppel?user_code={MOCK_USER_CODE}",
    "expires_in": 900,
    "interval": 5
}

MOCK_USERINFO_RESPONSE = {
    "sub": MOCK_USER_ID,
    "email": MOCK_EMAIL,
    "name": "Test User",
    "email_verified": True
}

MOCK_EMPTY_SESSION_RESPONSE = {"sessions": []}

MOCK_SESSION_RESPONSE = {"sessions": [{
    "key": MOCK_SESSION_KEY,
    "name": "Mock Test Device",
    "createdAt": "2026-02-18T12:00:00.000+00:00",
    "updatedAt": "2026-02-18T12:00:00.000+00:00"
}]}

MOCK_PROFILE_LIST = [
    {
        "id": "AAAAAAAA-BBBB-CCCC-DDDD-111111111111",
        "userId": MOCK_USER_ID,
        "displayName": "Test Adult Profile",
        "type": "Adult",
        "color": "FF427C"
    },
    {
        "id": "AAAAAAAA-BBBB-CCCC-DDDD-222222222222",
        "userId": MOCK_USER_ID,
        "displayName": "Kids",
        "type": "ChildYoung",
        "color": "FE6C44"
    }
]

MOCK_LOGIN_PAGE_HTML = """<!DOCTYPE html>
<html>
<head><title>NLZIET - Inloggen</title></head>
<body>
<form method="post" action="/account/login">
    <input name="__RequestVerificationToken" type="hidden" value="{csrf_token}" />
    <input type="hidden" name="ReturnUrl" value="{{return_url}}" />
    <input type="email" name="EmailAddress" />
    <input type="password" name="Password" />
    <input type="hidden" name="RememberLogin" value="true" />
    <button type="submit" name="button" value="login">Inloggen</button>
</form>
</body>
</html>""".format(csrf_token=MOCK_CSRF_TOKEN)

MOCK_DEVICE_PAGE_HTML = """<!DOCTYPE html>
<html>
<head><title>NLZIET - Apparaat koppelen</title></head>
<body>
<div id="primary-container">
<div><div>
<form method="post" action="/device">
    <input name="__RequestVerificationToken" type="hidden" value="{csrf_token}" />
    <input type="text" id="Name" name="Name" placeholder="Apparaatnaam" />
    <input type="text" id="Code" name="Code" placeholder="Code" />
    <div><div>
    <button type="submit" name="button" value="">Bevestigen</button>
    </div></div>
</form>
</div></div>
</div>
</body>
</html>""".format(csrf_token=MOCK_CSRF_TOKEN)

MOCK_DEVICE_CONFIRMED_HTML = """<!DOCTYPE html>
<html><head><title>NLZIET</title></head>
<body><p>Apparaat succesvol gekoppeld</p></body>
</html>"""

MOCK_DEVICE_CONFIRMED_URL = "https://id.nlziet.nl/device/confirmed"
MOCK_DEFAULT_REDIRECT_URI = "https://app.nlziet.nl/callback"
MOCK_DEFAULT_STATE = "mock_state"
MOCK_ANDROID_TV_CLIENT_ID = "triple-android-tv"

MOCK_LOGIN_ERROR_HTML_FRAGMENT = '<div class="validation-summary-errors">Invalid credentials</div></form>'

MOCK_DEVICE_PENDING_RESPONSE = {"error": "authorization_pending"}


# ============================================================================
# Mock Dispatcher
# ============================================================================

MOCK_HOME_PLACEMENT_RESPONSE = {
    "components": [
        {
            "type": "ItemTileList",
            "title": "Trending",
            "url": "https://api.nlziet.nl/v9/recommend/filtered?category=Trending&limit=10",
        }
    ]
}

MOCK_SERIES_DETAIL_RESPONSE = {
    "content": {
        "id": "mock-series-001",
        "title": "Mock Series",
        "seasons": [
            {
                "id": "mock-season-001",
                "title": "Seizoen 1",
                "seasonNumber": 1,
                "episodes": [
                    {"id": "mock-ep-001", "title": "Aflevering 1", "episodeNumber": 1}
                ],
            }
        ],
    }
}

# Real HAR data for boundary-detection live tests.
# Flikken Maastricht S18: descending API order, clean broadcastAt.
# series=noplAjB-l0e8onWe66xr_g  season=T8MyYV32fkOB68ZrA15zzg
MOCK_FM_S18_SERIES_ID = "noplAjB-l0e8onWe66xr_g"
MOCK_FM_S18_SEASON_ID = "T8MyYV32fkOB68ZrA15zzg"
MOCK_FM_S18_EPISODES_RESPONSE = {"data": [
    {"content": {"id": "glAJoJ9h1EKtk1PnSJndCw", "subtitle": "S18:A13 Vendetta",
                 "broadcastAt": "2024-04-26T20:35:00+02:00"}},
    {"content": {"id": "VeNwZlhKb0qAWkrMvOJ30Q", "subtitle": "S18:A12 Cluster B",
                 "broadcastAt": "2024-04-19T20:35:00+02:00"}},
    {"content": {"id": "XWcwoMsvj0-Q3yZ__jWvsg", "subtitle": "S18:A11 Ontvoerd",
                 "broadcastAt": "2024-04-12T20:35:00+02:00"}},
    {"content": {"id": "zGvggxtv_k2amuN1wWzf2g", "subtitle": "S18:A10 Leviticus 18:22",
                 "broadcastAt": "2024-04-05T20:35:00+02:00"}},
    {"content": {"id": "xY2ZFzySAUmeY_o9WSWwBw", "subtitle": "S18:A9 Tuig",
                 "broadcastAt": "2024-03-29T20:35:00+01:00"}},
    {"content": {"id": "VKyydgLJxkapvMoDzep1Ug", "subtitle": "S18:A8 Asiel",
                 "broadcastAt": "2024-03-22T20:35:00+01:00"}},
    {"content": {"id": "ttJ9bQpBS0a4yXeN_x_hMw", "subtitle": "S18:A7 Gangsters",
                 "broadcastAt": "2024-03-15T20:35:00+01:00"}},
    {"content": {"id": "5Y2Ya6UTBU6jgLUnt5urvw", "subtitle": "S18:A6 Jaloezie",
                 "broadcastAt": "2024-03-08T20:35:00+01:00"}},
    {"content": {"id": "wKcZAqWIW0KX0TMV9gezAA", "subtitle": "S18:A5 Beschuldigd",
                 "broadcastAt": "2024-03-01T20:35:00+01:00"}},
    {"content": {"id": "u1fyvBsN3EmR0sWCAyUudA", "subtitle": "S18:A4 Larry Konings",
                 "broadcastAt": "2024-02-23T20:35:00+01:00"}},
    {"content": {"id": "fBh2HAYhyUOepl0NSucnKw", "subtitle": "S18:A3 Juice",
                 "broadcastAt": "2024-02-16T20:35:00+01:00"}},
    {"content": {"id": "bVawig8-1kqcC9-TXlcrcQ", "subtitle": "S18:A2 Beste vrienden",
                 "broadcastAt": "2024-02-09T20:35:00+01:00"}},
    {"content": {"id": "mAbab8km6kunAmBJ4-goxQ", "subtitle": "S18:A1 Masker 19",
                 "broadcastAt": "2024-02-02T20:35:00+01:00"}},
]}

# De Luizenmoeder S1: descending API order, non-monotonic broadcastAt (re-broadcasts).
# series=ngpiHZQzmUq4q1uktOmlIQ  season=ml2xrgt2TkWWv9enhMd-sQ
MOCK_LUIZENMOEDER_S1_SERIES_ID = "ngpiHZQzmUq4q1uktOmlIQ"
MOCK_LUIZENMOEDER_S1_SEASON_ID = "ml2xrgt2TkWWv9enhMd-sQ"
MOCK_LUIZENMOEDER_S1_EPISODES_RESPONSE = {"data": [
    {"content": {"id": "lm-ep10", "subtitle": "S1:A10 Special",
                 "broadcastAt": "2018-03-18T20:25:00+01:00"}},
    {"content": {"id": "lm-ep09", "subtitle": "S1:A9 Send in the clowns",
                 "broadcastAt": "2018-03-11T20:25:00+01:00"}},
    {"content": {"id": "lm-ep08", "subtitle": "S1:A8 Kanjertraining",
                 "broadcastAt": "2018-03-04T20:25:00+01:00"}},
    {"content": {"id": "lm-ep07", "subtitle": "S1:A7 Een helder licht",
                 "broadcastAt": "2018-02-25T20:25:00+01:00"}},
    {"content": {"id": "lm-ep06", "subtitle": "S1:A6 Lentekriebels",
                 "broadcastAt": "2018-02-18T20:25:00+01:00"}},
    {"content": {"id": "lm-ep05", "subtitle": "S1:A5 Winterklaas",
                 "broadcastAt": "2020-12-04T20:25:00+01:00"}},  # re-broadcast
    {"content": {"id": "lm-ep04", "subtitle": "S1:A4 Laat ze maar glanzen",
                 "broadcastAt": "2018-02-04T20:25:00+01:00"}},
    {"content": {"id": "lm-ep03", "subtitle": "S1:A3 Er zijn er twee jarig, hoera hoera",
                 "broadcastAt": "2020-12-11T20:25:00+01:00"}},  # re-broadcast
    {"content": {"id": "lm-ep02", "subtitle": "S1:A2 Afspraak is afspraak",
                 "broadcastAt": "2022-05-08T02:05:00+02:00"}},  # re-broadcast
    {"content": {"id": "lm-ep01", "subtitle": "S1:A1 Het zijn altijd de nieuwkomers",
                 "broadcastAt": "2018-01-14T20:25:00+01:00"}},
]}

# Fawlty Towers S1: ascending API order, clean broadcastAt.
# series=PBby8G53Rk2xtH67ku044g  season=OssVKJHye0WUMhPSig9A5w
MOCK_FAWLTY_S1_SERIES_ID = "PBby8G53Rk2xtH67ku044g"
MOCK_FAWLTY_S1_SEASON_ID = "OssVKJHye0WUMhPSig9A5w"
MOCK_FAWLTY_S1_EPISODES_RESPONSE = {"data": [
    {"content": {"id": "ft-ep01", "subtitle": "S1:A1 A Touch of Class",
                 "broadcastAt": "1975-09-19T01:00:00+01:00"}},
    {"content": {"id": "ft-ep02", "subtitle": "S1:A2 The Builders",
                 "broadcastAt": "1975-09-26T01:00:00+01:00"}},
    {"content": {"id": "ft-ep03", "subtitle": "S1:A3 The Wedding",
                 "broadcastAt": "1975-10-03T01:00:00+01:00"}},
    {"content": {"id": "ft-ep04", "subtitle": "S1:A4 The Hotel Inspectors",
                 "broadcastAt": "1975-10-10T01:00:00+01:00"}},
    {"content": {"id": "ft-ep05", "subtitle": "S1:A5 Gourmet Night",
                 "broadcastAt": "1975-10-17T01:00:00+01:00"}},
    {"content": {"id": "ft-ep06", "subtitle": "S1:A6 The Germans",
                 "broadcastAt": "1975-10-24T01:00:00+01:00"}},
]}

# Map of (series_id, season_id) → mock episodes response.
MOCK_EPISODES_BY_SEASON = {
    (MOCK_FM_S18_SERIES_ID, MOCK_FM_S18_SEASON_ID): MOCK_FM_S18_EPISODES_RESPONSE,
    (MOCK_LUIZENMOEDER_S1_SERIES_ID, MOCK_LUIZENMOEDER_S1_SEASON_ID):
        MOCK_LUIZENMOEDER_S1_EPISODES_RESPONSE,
    (MOCK_FAWLTY_S1_SERIES_ID, MOCK_FAWLTY_S1_SEASON_ID): MOCK_FAWLTY_S1_EPISODES_RESPONSE,
}


MOCK_EPG_LIVE_RESPONSE = {
    "data": [
        {
            "channel": {
                "content": {
                    "id": "npo1",
                    "title": "NPO 1",
                    "logo": {"normalUrl": "https://example.com/npo1.png"},
                }
            },
            "programLocations": [
                {"content": {"assetId": "live-abc", "title": "Journaal"}}
            ],
        }
    ]
}


class NLZietMockDispatcher:
    """Routes UriHandler.open() calls to canned responses.

    Tracks state for multi-step flows:
    - Login flow: authorize → login page → POST credentials → callback with code
    - Device flow: initiate → poll (pending) → poll (success)
    - Session management: list devices → remove device
    """

    def __init__(self):
        self.device_flow_authorized = False
        self.device_poll_count = 0
        self._device_created = False
        self._device_removed = False
        self._device_name = ""
        self._last_auth_state = None

    def reset(self):
        """Reset state between tests."""
        self.device_flow_authorized = False
        self.device_poll_count = 0
        self._device_created = False
        self._device_removed = False
        self._device_name = ""
        self._last_auth_state = None

    def dispatch(self, uri, uri_handler_instance, **kwargs):
        """Route a UriHandler.open() call to the appropriate mock handler."""
        params = kwargs.get("params")
        data = kwargs.get("data")
        method = kwargs.get("method", "")

        parsed = urlparse(uri)
        path = parsed.path.lower()
        host = parsed.netloc.lower()

        if "id.nlziet.nl" in host:
            if path == "/connect/deviceauthorization" and data:
                return self._handle_device_authorization(uri, uri_handler_instance, data)

            if path == "/connect/token":
                return self._handle_token(uri, uri_handler_instance, data or params)

            if path == "/connect/authorize":
                return self._handle_authorize(uri, uri_handler_instance, parsed)

            if path == "/account/login" and params:
                return self._handle_login_post(uri, uri_handler_instance, params)

            if path == "/connect/userinfo":
                uri_handler_instance.status = UriStatus(code=200, url=uri, error=False, reason="OK")
                return json.dumps(MOCK_USERINFO_RESPONSE)

            if path == "/device" and not params:
                return self._handle_device_page_get(uri, uri_handler_instance)

            if path == "/device" and params:
                return self._handle_device_page_post(uri, uri_handler_instance, params)

            if "/api/session/revoke/" in uri and method == "DELETE":
                return self._handle_session_revoke(uri, uri_handler_instance)

            if path == "/api/session":
                return self._handle_session_list(uri, uri_handler_instance)

        if "api.nlziet.nl" in host:
            if path == "/v8/profile":
                return self._handle_profile_list(uri, uri_handler_instance)
            if path.startswith("/v9/placement/"):
                uri_handler_instance.status = UriStatus(code=200, url=uri, error=False, reason="OK")
                return json.dumps(MOCK_HOME_PLACEMENT_RESPONSE)
            if re.match(r"^/v8/series/", path):
                uri_handler_instance.status = UriStatus(code=200, url=uri, error=False, reason="OK")
                return json.dumps(MOCK_SERIES_DETAIL_RESPONSE)
            episode_m = re.match(r"^/v9/series/([^/]+)/episodes$", parsed.path)
            if episode_m:
                qs = parse_qs(parsed.query)
                season_id = qs.get("seasonId", [""])[0]
                series_id_raw = episode_m.group(1)
                key = (series_id_raw, season_id)
                response = MOCK_EPISODES_BY_SEASON.get(key, {"data": []})
                uri_handler_instance.status = UriStatus(
                    code=200, url=uri, error=False, reason="OK")
                return json.dumps(response)
            if path == "/v9/epg/programlocations/live":
                uri_handler_instance.status = UriStatus(code=200, url=uri, error=False, reason="OK")
                return json.dumps(MOCK_EPG_LIVE_RESPONSE)


        uri_handler_instance.status = UriStatus(code=404, url=uri, error=True, reason="Not Found")
        return ""

    def _handle_authorize(self, uri, uri_handler_instance, parsed):
        query_params = parse_qs(parsed.query)

        state = query_params.get("state", [""])[0]
        redirect_uri = query_params.get("redirect_uri", [""])[0]
        prompt = query_params.get("prompt", [""])[0]

        if prompt == "none":
            callback_url = f"{redirect_uri}?code={MOCK_AUTH_CODE}&state={state}&scope=openid%20api"
            uri_handler_instance.status = UriStatus(code=200, url=callback_url, error=False, reason="OK")
            return ""

        self._last_auth_state = state
        return_url = f"/connect/authorize/callback?client_id={query_params.get('client_id', [''])[0]}" \
                     f"&redirect_uri={redirect_uri}" \
                     f"&response_type=code&scope={query_params.get('scope', [''])[0]}" \
                     f"&state={state}" \
                     f"&code_challenge={query_params.get('code_challenge', [''])[0]}" \
                     f"&code_challenge_method=S256&response_mode=query"

        login_html = MOCK_LOGIN_PAGE_HTML.replace("{return_url}", return_url)
        login_url = f"https://id.nlziet.nl/account/login?ReturnUrl={return_url}"
        uri_handler_instance.status = UriStatus(code=200, url=login_url, error=False, reason="OK")
        return login_html

    def _handle_login_post(self, uri, uri_handler_instance, params):
        if isinstance(params, str):
            form_data = parse_qs(params)
        else:
            form_data = params

        email = form_data.get("EmailAddress", [""])[0] if isinstance(form_data, dict) else ""
        password = form_data.get("Password", [""])[0] if isinstance(form_data, dict) else ""
        return_url = form_data.get("ReturnUrl", [""])[0] if isinstance(form_data, dict) else ""

        if not email or not password:
            uri_handler_instance.status = UriStatus(code=200, url=uri, error=False, reason="OK")
            return MOCK_LOGIN_PAGE_HTML

        if password == MOCK_INVALID_PASSWORD:
            uri_handler_instance.status = UriStatus(code=200, url=uri, error=False, reason="OK")
            return MOCK_LOGIN_PAGE_HTML.replace("</form>", MOCK_LOGIN_ERROR_HTML_FRAGMENT)

        state = self._last_auth_state or MOCK_DEFAULT_STATE
        return_url_params = parse_qs(return_url.split("?", 1)[-1] if "?" in return_url else return_url)
        redirect_uri = return_url_params.get("redirect_uri", [MOCK_DEFAULT_REDIRECT_URI])[0]

        callback_url = f"{redirect_uri}?code={MOCK_AUTH_CODE}&state={state}&scope=openid%20api"
        uri_handler_instance.status = UriStatus(code=200, url=callback_url, error=False, reason="OK")
        return ""

    def _handle_token(self, uri, uri_handler_instance, data):
        if isinstance(data, str):
            form_data = parse_qs(data)
        elif isinstance(data, dict):
            form_data = {k: [v] if not isinstance(v, list) else v for k, v in data.items()}
        else:
            form_data = {}

        grant_type = form_data.get("grant_type", [""])[0]
        uri_handler_instance.status = UriStatus(code=200, url=uri, error=False, reason="OK")

        if grant_type == "urn:ietf:params:oauth:grant-type:device_code":
            self.device_poll_count += 1
            if not self.device_flow_authorized:
                return json.dumps(MOCK_DEVICE_PENDING_RESPONSE)
            return json.dumps(MOCK_TOKEN_RESPONSE_WITH_REFRESH)

        if grant_type == "refresh_token":
            return json.dumps(MOCK_TOKEN_RESPONSE_WITH_REFRESH)

        if grant_type == "authorization_code":
            client_id = form_data.get("client_id", [""])[0]
            if client_id == MOCK_ANDROID_TV_CLIENT_ID:
                return json.dumps(MOCK_TOKEN_RESPONSE_WITH_REFRESH)
            return json.dumps(MOCK_TOKEN_RESPONSE)

        if grant_type == "profile":
            return json.dumps(MOCK_PROFILE_TOKEN_RESPONSE)

        return json.dumps(MOCK_TOKEN_RESPONSE)

    def _handle_device_authorization(self, uri, uri_handler_instance, data):
        uri_handler_instance.status = UriStatus(code=200, url=uri, error=False, reason="OK")
        self.device_flow_authorized = False
        self.device_poll_count = 0
        return json.dumps(MOCK_DEVICE_AUTH_RESPONSE)

    def _handle_device_page_get(self, uri, uri_handler_instance):
        uri_handler_instance.status = UriStatus(code=200, url=uri, error=False, reason="OK")
        return MOCK_DEVICE_PAGE_HTML

    def _handle_device_page_post(self, uri, uri_handler_instance, params):
        if isinstance(params, str):
            form_data = parse_qs(params)
            self._device_name = form_data.get("Name", [""])[0]
        self.device_flow_authorized = True
        self._device_created = True
        uri_handler_instance.status = UriStatus(code=200, url=MOCK_DEVICE_CONFIRMED_URL, error=False, reason="OK")
        return MOCK_DEVICE_CONFIRMED_HTML

    def _handle_session_list(self, uri, uri_handler_instance):
        uri_handler_instance.status = UriStatus(code=200, url=uri, error=False, reason="OK")

        if self._device_removed or not self._device_created:
            return json.dumps(MOCK_EMPTY_SESSION_RESPONSE)

        response = MOCK_SESSION_RESPONSE.copy()
        response["sessions"][0]["name"] = self._device_name
        return json.dumps(response)

    def _handle_session_revoke(self, uri, uri_handler_instance):
        self._device_removed = True
        uri_handler_instance.status = UriStatus(code=200, url=uri, error=False, reason="OK")
        return ""

    def _handle_profile_list(self, uri, uri_handler_instance):
        uri_handler_instance.status = UriStatus(code=200, url=uri, error=False, reason="OK")
        return json.dumps(MOCK_PROFILE_LIST)
