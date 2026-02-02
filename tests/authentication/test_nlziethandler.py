# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
import os
import re
import secrets
import time
import unittest
import threading

from resources.lib.authentication.nlzietoauth2handler import NLZIETOAuth2Handler
from resources.lib.authentication.authenticationresult import AuthenticationResult
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.addonsettings import AddonSettings, LOCAL
from tests.authentication.nlziet_mocks import MOCK_INVALID_PASSWORD


# ============================================================================
# Test Helper Functions
# ============================================================================

def generate_test_device_name() -> str:
    """Generate a unique test device name with timestamp and random ID.

    Format: retrospect_unit_test_YYYYMMDD_<8-char-hex>
    Example: retrospect_unit_test_20260218_a32a6c6f
    """
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    uid = secrets.token_hex(4)
    return f"retrospect_unit_test_{date_str}_{uid}"


def submit_device_code(handler: NLZIETOAuth2Handler, user_code: str, device_name: str) -> bool:
    """Automate device code submission using authenticated session cookies."""
    Logger.info(f"Attempting to submit device code '{user_code}' with name '{device_name}'")

    uri_handler = UriHandler.instance()
    headers = {'User-Agent': handler._get_latest_user_agent()}

    try:
        Logger.debug("Fetching https://id.nlziet.nl/device to get CSRF token...")
        html = uri_handler.open('https://id.nlziet.nl/device', additional_headers=headers)

        if 'account/login' in uri_handler.status.url or 'ReturnUrl' in html:
            Logger.error("Not authenticated - redirected to login page")
            return False

        csrf_match = re.search(
            r'<input[^>]*name=["\']__RequestVerificationToken["\'][^>]*value=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE
        )
        if not csrf_match:
            csrf_match = re.search(
                r'<input[^>]*value=["\']([^"\']+)["\'][^>]*name=["\']__RequestVerificationToken["\']',
                html,
                re.IGNORECASE
            )
        if not csrf_match:
            Logger.error("Could not find CSRF token on /device page")
            return False

        csrf_token = csrf_match.group(1)
        Logger.debug(f"Found CSRF token: {csrf_token[:20]}...")

        from urllib.parse import urlencode
        form_data = {
            'Name': device_name,
            'Code': user_code,
            'button': '',
            '__RequestVerificationToken': csrf_token
        }

        Logger.info(f"Submitting device code to https://id.nlziet.nl/device")
        response = uri_handler.open(
            'https://id.nlziet.nl/device',
            params=urlencode(form_data),
            additional_headers=headers
        )

        final_url = uri_handler.status.url
        Logger.debug(f"Final URL after submission: {final_url}")

        if '/device/confirmed' in final_url:
            Logger.info("Device code submitted successfully - confirmed!")
            return True
        elif 'success' in response.lower() or 'gekoppeld' in response.lower():
            Logger.info("Device code submitted successfully (success message)")
            return True
        else:
            Logger.warning("Device code submitted but no success confirmation found")
            return False

    except Exception as error:
        Logger.error(f"Failed to submit device code: {error}", exc_info=True)
        return False


# ============================================================================
# Test Class
# ============================================================================


class TestNLZIETAuthLive(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize singletons with robust environment scaffolding."""
        # 1. Initialize Logger
        Logger.create_logger(None, str(cls), min_log_level=0)

        # 2. Initialize UriHandler
        UriHandler.create_uri_handler(ignore_ssl_errors=False)

        # 3. Initialize Config and ensure addon_data directory exists
        from resources.lib.retroconfig import Config
        if not os.path.exists(Config.profileDir):
            os.makedirs(Config.profileDir, exist_ok=True)
            Logger.debug(f"Created profile directory: {Config.profileDir}")

        # 4. Initialize handler
        cls.handler = NLZIETOAuth2Handler(use_device_flow=False)

        # 5. Load credentials
        cls.username = os.getenv('NLZIET_USERNAME')
        cls.password = os.getenv('NLZIET_PASSWORD')

        if not cls.username or not cls.password:
            raise unittest.SkipTest("NLZIET credentials not in environment.")

    @classmethod
    def tearDownClass(cls):
        """Clean up logger."""
        if Logger.instance():
            Logger.instance().close_log()

    def setUp(self):
        """Clean cookies before each test for total isolation."""
        UriHandler.delete_cookie(domain=".nlziet.nl")

    # =================================================================
    # HEADLESS LOGIN TESTS (Username/Password)
    # =================================================================

    # --- 1. PREFLIGHT CHECKS ---

    def test_01_preflight_empty_credentials(self):
        """Verify handler rejects empty inputs."""
        result = self.handler.log_on("", "")
        self.assertIsInstance(result, AuthenticationResult)
        self.assertFalse(result.logged_on, "Should fail with empty credentials")

    def test_02_preflight_invalid_password(self):
        """Verify backend rejects incorrect credentials."""
        # Clear identity server session to prevent SSO bypass
        UriHandler.delete_cookie(domain="id.nlziet.nl")
        result = self.handler.log_on(self.username, MOCK_INVALID_PASSWORD)
        self.assertFalse(result.logged_on, "Should fail with wrong password")

    # --- 2. AUTHENTICATION (log_on) ---

    def test_03_log_on_headless_success(self):
        """Main Integration: Full headless flow against NLZIET."""
        Logger.info(f"NLZIET: Testing live log_on for {self.username}")

        result = self.handler.log_on(self.username, self.password)

        self.assertTrue(result.logged_on, f"Live login failed: {result.error}")
        self.assertIsNotNone(result.jwt, "No JWT returned")
        self.assertFalse(result.existing_login, "Should be new login")
        self.assertIsNotNone(result.username, "No username extracted")

        self.assertGreater(len(result.jwt), 100, "JWT too short")
        self.assertEqual(result.jwt.count('.'), 2, "JWT should have 3 parts")

        Logger.info(f"NLZIET: Authenticated as: {result.username}")

    # --- 3. SESSION PERSISTENCE ---

    def test_04_active_authentication_persistence(self):
        """Verify session persists in AddonSettings."""
        result = self.handler.active_authentication()

        self.assertTrue(result.logged_on, "Session not persisted")
        self.assertTrue(result.existing_login, "Should be existing session")

        token = self.handler.get_valid_token()
        self.assertIsNotNone(token, "Stored token missing")

    # --- 4. DATA INTEGRITY ---

    def test_05_username_extraction_from_jwt(self):
        """Verify username extraction handles real NLZIET JWT claims.

        Uses token from previous tests (either test_03 or test_06)."""
        token = self.handler.get_valid_token()
        if not token:
            self.skipTest("No token available - test_03 must run first")

        username = self.handler._extract_username_from_token(token)
        self.assertIsNotNone(username, "Failed to extract username from real JWT")
        # Flexible assertion as suggested: check that it contains data
        self.assertGreater(len(username), 0, "Extracted username is empty")
        Logger.info(f"NLZIET: Verified identity extraction: {username}")

    # --- 5. TOKEN REFRESH ---

    def test_06_token_refresh(self):
        """Verify automatic token refresh via silent re-authentication.

        Depends on test_03 having established a session with id_token."""
        # Verify we have an active session from previous test
        result = self.handler.active_authentication()
        if not result.logged_on:
            self.skipTest("No active session - test_03 must run first")

        # Force token expiry
        expiry_key = f"{self.handler.prefix}expires_at"
        AddonSettings.set_setting(expiry_key, str(int(time.time()) - 100), store=LOCAL)

        # get_valid_token should trigger silent re-authentication
        token = self.handler.get_valid_token()
        self.assertIsNotNone(token, "Silent re-authentication failed")

        # Verify expiry was updated
        new_expiry = int(AddonSettings.get_setting(expiry_key, store=LOCAL))
        self.assertGreater(new_expiry, int(time.time()), "Expiry not updated after refresh")

    # --- 6. PROFILE MANAGEMENT ---

    def test_07_list_profiles(self):
        """Test listing available profiles."""
        if not self.handler.get_valid_token():
            self.skipTest("No active session - test_03 must run first")

        profiles = self.handler.list_profiles()

        self.assertIsNotNone(profiles, "Profile list should not be None")
        self.assertIsInstance(profiles, list, "Profiles should be a list")
        self.assertGreater(len(profiles), 0, "Should have at least one profile")

        for profile in profiles:
            self.assertIn("id", profile)
            self.assertIn("displayName", profile)
            self.assertIn("type", profile)
            self.assertIn("userId", profile)
            Logger.info(f"Profile: {profile['displayName']} (type: {profile['type']}, id: {profile['id']})")

        kids_profile = next((p for p in profiles if p["type"] == "ChildYoung"), None)
        if kids_profile:
            Logger.info(f"Done: Found {len(profiles)} profile(s), including Kids profile: {kids_profile['displayName']}")
        else:
            Logger.info(f"Done: Found {len(profiles)} profile(s), no Kids profile present")

    def test_08_get_nlziet_profile(self):
        """Test getting a profile by ID."""
        if not self.handler.get_valid_token():
            self.skipTest("No active session - test_03 must run first")

        profiles = self.handler.list_profiles()
        self.assertIsNotNone(profiles, "Failed to list profiles")
        self.assertGreater(len(profiles), 0, "No profiles available")

        test_profile = profiles[0]
        retrieved = self.handler.get_nlziet_profile(test_profile['id'])
        self.assertIsNotNone(retrieved, "Should find profile by ID")
        self.assertEqual(retrieved['id'], test_profile['id'])
        self.assertEqual(retrieved['displayName'], test_profile['displayName'])
        self.assertEqual(retrieved['type'], test_profile['type'])
        Logger.info(f"Done: Successfully retrieved profile by ID: {retrieved['displayName']}")

    def test_09_invalid_profile_id(self):
        """Test graceful handling of invalid/deleted profile ID."""
        if not self.handler.get_valid_token():
            self.skipTest("No active session - test_03 must run first")

        fake_profile_id = "00000000-0000-0000-0000-000000000000"
        invalid_profile = self.handler.get_nlziet_profile(fake_profile_id)
        self.assertIsNone(invalid_profile, "Should return None for invalid profile ID")
        Logger.info(f"Done: Invalid profile ID correctly returned None (graceful failure)")

    def test_10_set_and_get_profile(self):
        """Test setting and getting the selected profile."""
        if not self.handler.get_valid_token():
            self.skipTest("No active session - test_03 must run first")

        profiles = self.handler.list_profiles()
        self.assertIsNotNone(profiles, "Failed to list profiles")
        self.assertGreater(len(profiles), 0, "No profiles available")

        test_profile = profiles[0]
        success = self.handler.set_profile(test_profile['id'])
        self.assertTrue(success, "Failed to set selected profile")
        Logger.info(f"Selected profile: {test_profile['displayName']}")

        selected = self.handler.get_profile()
        self.assertIsNotNone(selected, "Failed to get selected profile")
        self.assertEqual(selected['id'], test_profile['id'])
        self.assertEqual(selected['displayName'], test_profile['displayName'])
        self.assertEqual(selected['type'], test_profile['type'])
        Logger.info(f"Done: Retrieved selected profile: {selected['displayName']}")

    def test_11_get_profile_when_deleted(self):
        """Test graceful handling when selected profile no longer exists."""
        if not self.handler.get_valid_token():
            self.skipTest("No active session - test_03 must run first")

        fake_profile_id = "00000000-0000-0000-0000-000000000000"
        from resources.lib.addonsettings import AddonSettings, LOCAL
        AddonSettings.set_setting(f"{self.handler.prefix}profile_id", fake_profile_id, store=LOCAL)
        AddonSettings.set_setting(f"{self.handler.prefix}profile_name", "Deleted Profile", store=LOCAL)
        AddonSettings.set_setting(f"{self.handler.prefix}profile_type", "Adult", store=LOCAL)

        selected = self.handler.get_profile()
        self.assertIsNone(selected, "Should return None for deleted profile")

        stored_id = AddonSettings.get_setting(f"{self.handler.prefix}profile_id", store=LOCAL)
        self.assertEqual(stored_id, "", "Profile ID should be cleared")
        Logger.info(f"Done: Deleted profile detected and cleared from settings")

    def test_12_set_invalid_profile(self):
        """Test that setting an invalid profile ID fails gracefully."""
        if not self.handler.get_valid_token():
            self.skipTest("No active session - test_03 must run first")

        fake_profile_id = "00000000-0000-0000-0000-000000000000"
        success = self.handler.set_profile(fake_profile_id)
        self.assertFalse(success, "Should fail to set invalid profile")

        selected = self.handler.get_profile()
        if selected:
            self.assertNotEqual(selected['id'], fake_profile_id, "Invalid profile should not be stored")
        Logger.info(f"Done: Invalid profile correctly rejected")

    # --- 7. SESSION TERMINATION ---

    def test_13_log_off_cleanup(self):
        """Verify tokens are wiped and session cleared."""
        success = self.handler.log_off(self.username)
        self.assertTrue(success, "log_off returned False")

        result = self.handler.active_authentication()
        self.assertFalse(result.logged_on, "Session still active after log_off")

    # =================================================================
    # DEVICE FLOW TESTS (TV-Friendly Authentication)
    # =================================================================

    def test_14_device_flow_initiation(self):
        """Test device flow initiation with real API (does NOT complete login)."""
        # Create handler configured for device flow
        device_handler = NLZIETOAuth2Handler(use_device_flow=True)

        # Generate unique test device name
        device_name = generate_test_device_name()

        result = device_handler.start_device_flow(device_name=device_name)

        self.assertIsNotNone(result, "Device flow should return a result")
        self.assertIn("device_code", result)
        self.assertIn("user_code", result)
        self.assertIn("verification_uri", result)
        self.assertEqual(result["verification_uri"], "https://nlziet.nl/koppel")
        self.assertIn("expires_in", result)
        self.assertIn("interval", result)

        Logger.info("=" * 60)
        Logger.info(f"Device flow initiated successfully!")
        Logger.info(f"Device name: {device_name}")
        Logger.info(f"User code: {result['user_code']}")
        Logger.info(f"Verification URL: {result['verification_uri']}")
        Logger.info(f"NOTE: Flow was NOT completed - no device added to account")
        Logger.info("=" * 60)

    @unittest.skipIf(os.getenv('TEST_NLZIET_DEVICE_FLOW', 'AUTO') not in ('AUTO', 'MANUAL'),
                     "Set TEST_NLZIET_DEVICE_FLOW=AUTO or MANUAL to enable device flow test")
    def test_15_device_flow_authentication(self):
        """Test device flow authentication and cleanup.

        Steps:
        1. Initiate device flow
        2. Ensure authentication (web login or existing SSO)
        3. Auto-submit device code
        4. Poll and complete device flow
        5. Activate device session (makes device visible in session list)
        6. Clean up: remove the device (AUTO mode only)

        Environment:
        - TEST_NLZIET_DEVICE_FLOW=AUTO: Full automation with cleanup
        - TEST_NLZIET_DEVICE_FLOW=MANUAL: Manual code submission, device left for testing
        """
        self._run_device_flow_authentication()

    def _run_device_flow_authentication(self):
        Logger.info("=" * 60)
        Logger.info("DEVICE FLOW AUTHENTICATION TEST")
        Logger.info("=" * 60)

        device_handler = NLZIETOAuth2Handler(use_device_flow=True)
        device_name = generate_test_device_name()

        Logger.info("Step 1: Initiating device flow...")
        device_info = device_handler.start_device_flow(device_name=device_name)
        self.assertIsNotNone(device_info, "Failed to initiate device flow")
        user_code = device_info['user_code']
        device_code = device_info['device_code']
        Logger.info(f"Done: Device flow initiated - code: {user_code}")

        Logger.info("Step 2: Ensuring authentication...")
        try:
            test_response = UriHandler.open("https://id.nlziet.nl/device", no_cache=True)
            if 'account/login' in UriHandler.instance().status.url:
                Logger.debug("No active session - logging in...")
                login_result = self.handler.log_on(self.username, self.password)
                self.assertTrue(login_result.logged_on, f"Web login failed: {login_result.error}")
                Logger.info("Web login successful")
            else:
                Logger.info("Using existing SSO session")
        except Exception:
            login_result = self.handler.log_on(self.username, self.password)
            self.assertTrue(login_result.logged_on, f"Web login failed: {login_result.error}")
            Logger.info("Web login successful")

        Logger.info("Step 3: Auto-submitting device code...")
        submission_result = {'success': False}

        def submit_with_result():
            submission_result['success'] = submit_device_code(self.handler, user_code, device_name)

        submit_thread = threading.Thread(target=submit_with_result)
        submit_thread.start()
        submit_thread.join(timeout=10)

        self.assertTrue(submission_result['success'], "Device code submission failed")
        Logger.info("Device code submitted")

        Logger.info("Step 4: Polling for device flow completion...")
        success = device_handler.poll_device_flow(device_code, device_info['interval'], max_attempts=3)
        self.assertTrue(success, "Device flow polling failed")

        auth_result = device_handler.active_authentication()
        self.assertTrue(auth_result.logged_on, "Not authenticated after device flow")
        Logger.info(f"Device flow complete - authenticated as: {auth_result.username}")

        Logger.info("Step 5: Activating device...")
        userinfo = device_handler.get_user_info()
        self.assertIsNotNone(userinfo, "Failed to get user info")
        Logger.info("Device activated")

        device_flow_mode = os.getenv('TEST_NLZIET_DEVICE_FLOW', 'AUTO')
        Logger.info("Step 6: Verifying device was added to account...")
        mijn_access_token = self._get_mijn_nlziet_token()
        self.assertIsNotNone(mijn_access_token, "Failed to get mijn-nlziet token for verification")

        devices = self.handler.list_devices(access_token=mijn_access_token)
        self.assertIsNotNone(devices, "Failed to list devices for verification")

        device_found = any(d.get('name') == device_name for d in devices)
        self.assertTrue(device_found, f"Device '{device_name}' not found in account after creation!")
        Logger.info(f"Verified device '{device_name}' exists in account")

        device_key = next((d['key'] for d in devices if d.get('name') == device_name), None)

        if device_flow_mode == 'AUTO':
            Logger.info("Step 7: Cleanup - removing test device (AUTO mode)...")
            self.assertIsNotNone(device_key, f"Could not find device key for '{device_name}'")

            removed = self.handler.remove_device(device_key, access_token=mijn_access_token)
            self.assertTrue(removed, f"Failed to remove device '{device_name}'")
            Logger.info(f"Device '{device_name}' removed")

            devices_after = self.handler.list_devices(access_token=mijn_access_token)
            device_still_exists = any(d.get('name') == device_name for d in devices_after) if devices_after else False
            self.assertFalse(device_still_exists, f"Device '{device_name}' still exists after removal!")
            Logger.info(f"Verified device '{device_name}' was removed from account")

            for key in ['access_token', 'refresh_token', 'id_token', 'expires_at']:
                AddonSettings.set_setting(f"{device_handler.prefix}{key}", "", store=LOCAL)
            Logger.info("Cleared device flow tokens")

            Logger.info("=" * 60)
            Logger.info("DEVICE FLOW TEST COMPLETE - Cleanup successful")
            Logger.info("=" * 60)
        else:
            Logger.info("=" * 60)
            Logger.info("DEVICE FLOW TEST COMPLETE - Device left for manual testing")
            Logger.info(f"Device name: {device_name}")
            if device_key:
                removal_url = f"https://mijn.nlziet.nl/instellingen/apparaten"
                Logger.info(f"Remove via web: {removal_url}")
                Logger.info(f"Device key: {device_key}")
            Logger.info("To remove later, use: test script with AUTO mode or mijn.nlziet.nl")
            Logger.info("=" * 60)

    def _get_mijn_nlziet_token(self):
        """Get access token for mijn-nlziet OAuth client via silent auth.

        Returns access_token string or None on failure.
        """
        import hashlib
        import base64
        from urllib.parse import urlencode, parse_qs, urlparse

        try:
            state = secrets.token_urlsafe(16)
            code_verifier = secrets.token_urlsafe(32)
            code_challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).rstrip(b'=').decode()

            auth_params = {
                'client_id': 'mijn-nlziet',
                'redirect_uri': 'https://mijn.nlziet.nl/callback-silent.html',
                'response_type': 'code',
                'scope': 'IdentityServerApi openid api',
                'state': state,
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256',
                'prompt': 'none',
                'response_mode': 'query'
            }

            auth_url = f"https://id.nlziet.nl/connect/authorize?{urlencode(auth_params)}"
            UriHandler.open(auth_url, no_cache=True)
            final_url = UriHandler.instance().status.url

            parsed = urlparse(final_url)
            params = parse_qs(parsed.query)

            if 'code' not in params:
                return None

            auth_code = params['code'][0]

            token_data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': 'https://mijn.nlziet.nl/callback-silent.html',
                'client_id': 'mijn-nlziet',
                'code_verifier': code_verifier
            }

            token_response = UriHandler.open(
                'https://id.nlziet.nl/connect/token',
                params=urlencode(token_data),
                no_cache=True
            )

            import json
            tokens = json.loads(token_response) if isinstance(token_response, str) else token_response
            return tokens.get('access_token')

        except Exception as e:
            Logger.warning(f"Failed to get mijn-nlziet token: {e}")
            return None

    @unittest.skipIf(os.getenv('TEST_NLZIET_DEVICE_FLOW', 'AUTO') not in ('AUTO', 'MANUAL'),
                     "Set TEST_NLZIET_DEVICE_FLOW=AUTO or MANUAL to enable device flow test")
    def test_16_device_flow_refresh_token(self):
        """Test device flow refresh token grant.

        Self-sufficient: If device flow tokens don't exist, performs device flow first.
        Then tests that refresh_token grant works correctly.
        """
        self._run_device_flow_refresh_token()

    def _run_device_flow_refresh_token(self):
        device_handler = NLZIETOAuth2Handler(use_device_flow=True)
        refresh_token = AddonSettings.get_setting(f"{device_handler.prefix}refresh_token", store=LOCAL)

        created_device_name = None
        device_flow_mode = os.getenv('TEST_NLZIET_DEVICE_FLOW', 'AUTO')

        if not refresh_token:
            Logger.info("No device flow tokens found - performing device flow authentication first...")

            device_name = generate_test_device_name()
            created_device_name = device_name

            device_info = device_handler.start_device_flow(device_name=device_name)
            self.assertIsNotNone(device_info, "Failed to initiate device flow for test_10")

            if not self.handler.get_valid_token():
                result = self.handler.log_on(self.username, self.password)
                self.assertTrue(result.logged_on, "Web login failed in test_10 setup")

            submit_device_code(
                self.handler,
                device_info['user_code'],
                device_name
            )

            success = device_handler.poll_device_flow(
                device_info['device_code'],
                device_info.get('interval', 5),
                device_info.get('expires_in', 900)
            )
            self.assertTrue(success, "Device flow polling failed in test_10 setup")

            # Activate the device
            device_handler.get_user_info()

            Logger.info("Device flow authentication complete for test_10")

            refresh_token = AddonSettings.get_setting(f"{device_handler.prefix}refresh_token", store=LOCAL)
            self.assertIsNotNone(refresh_token, "Failed to get refresh_token after device flow")

        Logger.info("Testing device flow refresh token grant...")

        expiry_key = f"{device_handler.prefix}expires_at"
        old_expiry = int(AddonSettings.get_setting(expiry_key, store=LOCAL) or 0)
        AddonSettings.set_setting(expiry_key, str(int(time.time()) - 10), store=LOCAL)

        token = device_handler.get_valid_token()
        self.assertIsNotNone(token, "Refresh token grant failed")

        new_expiry = int(AddonSettings.get_setting(expiry_key, store=LOCAL))
        self.assertGreater(new_expiry, int(time.time()), "Expiry not updated")

        Logger.info(f"Device refresh token grant successful - new expiry: {new_expiry - int(time.time())}s")

        if created_device_name and device_flow_mode == 'AUTO':
            Logger.info(f"Cleanup: Removing test device '{created_device_name}'...")

            mijn_access_token = self._get_mijn_nlziet_token()

            if mijn_access_token:
                devices = self.handler.list_devices(access_token=mijn_access_token)
                if devices:
                    device_key = next((d['key'] for d in devices if d.get('name') == created_device_name), None)
                    if device_key:
                        removed = self.handler.remove_device(device_key, access_token=mijn_access_token)
                        if removed:
                            Logger.info(f"Cleanup: Device '{created_device_name}' removed")
                        else:
                            Logger.warning(f"Cleanup: Failed to remove device '{created_device_name}'")
                    else:
                        Logger.warning(f"Cleanup: Could not find device key for '{created_device_name}'")
            else:
                Logger.warning("Cleanup: Could not get mijn-nlziet token for device removal")

# ============================================================================
# Mocked Test Class — runs all tests against mock API responses
# ============================================================================


class TestNLZIETAuthMocked(TestNLZIETAuthLive):
    """Runs all NLZiet auth tests against mocked API responses.

    Inherits all test methods from TestNLZIETAuthLive. Overrides
    setUpClass to inject mock UriHandler.open() instead of requiring real
    credentials. This class always runs, even without NLZIET_USERNAME/PASSWORD.
    """

    _mock_dispatcher = None
    _original_open = None

    @classmethod
    def setUpClass(cls):
        """Initialize with mock dispatcher instead of real credentials."""
        from tests.authentication.nlziet_mocks import NLZietMockDispatcher

        Logger.create_logger(None, str(cls), min_log_level=0)
        UriHandler.create_uri_handler(ignore_ssl_errors=False)

        from resources.lib.retroconfig import Config
        if not os.path.exists(Config.profileDir):
            os.makedirs(Config.profileDir, exist_ok=True)

        cls.handler = NLZIETOAuth2Handler(use_device_flow=False)

        cls.username = "test@example.com"
        cls.password = "mock_password"

        cls._mock_dispatcher = NLZietMockDispatcher()
        cls._original_open = UriHandler.instance().open

        uri_handler_instance = UriHandler.instance()

        def mock_open(uri, proxy=None, params=None, data=None, json=None,
                      referer=None, additional_headers=None, no_cache=False,
                      force_text=False, force_cache_duration=None, method=""):
            return cls._mock_dispatcher.dispatch(
                uri, uri_handler_instance,
                params=params, data=data, json=json, method=method,
                additional_headers=additional_headers
            )

        uri_handler_instance.open = mock_open

    @classmethod
    def tearDownClass(cls):
        """Restore original UriHandler.open and clean up."""
        if cls._original_open:
            UriHandler.instance().open = cls._original_open
        super().tearDownClass()

    def setUp(self):
        """Reset mock state and clean cookies between tests."""
        if self._mock_dispatcher:
            self._mock_dispatcher.reset()
        UriHandler.delete_cookie(domain=".nlziet.nl")

    # Override to bypass parent's @skipIf — mock tests always run
    def test_15_device_flow_authentication(self):
        self._run_device_flow_authentication()

    def test_16_device_flow_refresh_token(self):
        self._run_device_flow_refresh_token()

    def test_refresh_no_tokens_raises_value_error(self):
        """refresh_access_token raises ValueError when no refresh or id token is stored."""
        AddonSettings.set_setting(f"{self.handler.prefix}refresh_token", "", store=LOCAL)
        AddonSettings.set_setting(f"{self.handler.prefix}id_token", "", store=LOCAL)
        with self.assertRaises(ValueError):
            self.handler.refresh_access_token()

    def test_set_profile_exchanges_token(self):
        """set_profile performs a token exchange and stores a profile-scoped token."""
        from tests.authentication.nlziet_mocks import (
            MOCK_ACCESS_TOKEN, MOCK_PROFILE_ACCESS_TOKEN, MOCK_PROFILE_LIST)
        # Ensure we have a valid session first.
        if not self.handler.get_valid_token():
            self.handler.log_on(self.username, self.password)

        token_before = self.handler.get_valid_token()
        self.assertIsNotNone(token_before)

        profile_id = MOCK_PROFILE_LIST[1]["id"]  # Kids profile
        success = self.handler.set_profile(profile_id)
        self.assertTrue(success)

        token_after = self.handler.get_valid_token()
        self.assertEqual(token_after, MOCK_PROFILE_ACCESS_TOKEN)
        self.assertNotEqual(token_after, MOCK_ACCESS_TOKEN)
        self.assertEqual(self.handler.profile_type, "ChildYoung")
