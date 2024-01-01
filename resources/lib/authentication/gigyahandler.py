import uuid
from typing import Optional

from resources.lib.authentication.authenticationhandler import AuthenticationHandler
from resources.lib.authentication.authenticationresult import AuthenticationResult
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler


class GigyaHandler(AuthenticationHandler):
    def __init__(self, realm: str, api_key_3: str, api_key_4: str, device_id: str):
        super().__init__(realm, device_id)

        self.__api_key_3 = api_key_3
        self.__api_key_4 = api_key_4
        self.__build_id = "15627"

        self.__uid = None
        self.__uid_signature = None
        self.__uid_signature_timestamp = None

    def log_on(self, username, password) -> AuthenticationResult:
        bootstrap_url = f"https://accounts.eu1.gigya.com/accounts.webSdkBootstrap?apiKey={self.__api_key_3}&sdk=js_latest&sdkBuild={self.__build_id}&format=json"
        bootstrap = UriHandler.open(bootstrap_url, no_cache=True)
        bootstrap_json = JsonHelper(bootstrap)
        if not bootstrap_json.get_value("statusReason") == "OK":
            Logger.error("Error initiating login")
            return AuthenticationResult(None)

        gmid = UriHandler.get_cookie("gmid", ".gigya.com").value
        UriHandler.set_cookie(name="gmid", value=gmid, domain=".videoland.com")

        login_url = "https://gigya-merge.videoland.com/accounts.login"
        login_data = {
            "loginID": username,
            "password": password,
            "sessionExpiration": -2,
            "targetEnv": "jssdk",
            "include": "profile,data",
            "includeUserInfo": True,
            "lang": "en",
            "APIKey": self.__api_key_4,
            "sdk": "js_latest",
            "authMode": "cookie",
            "pageURL": "https://www.videoland.com/inloggen",
            "sdkBuild": 15627,
            "format": "json",
        }

        headers = {
            "content-type": "application/x-www-form-urlencoded"
        }
        login_result = UriHandler.open(login_url, data=login_data, no_cache=True, additional_headers=headers)
        result = JsonHelper(login_result)
        account = result.get_value("profile", "email")

        self.__extract_token_info(result)

        return AuthenticationResult(username=account)

    def active_authentication(self) -> AuthenticationResult:
        login_token_cookie = UriHandler.get_cookie(f"glt_{self.__api_key_4}", domain=f".{self.realm}")
        if not login_token_cookie:
            return AuthenticationResult(None)

        profile_data = {
            "include": "profile,data",
            "lang": "en",
            "APIKey": self.__api_key_4,
            "sdk": "js_latest",
            "login_token": login_token_cookie.value,
            "authMode": "cookie",
            # "pageURL": "",
            "sdkBuild": 15627,
            "format": "json",
        }
        headers = {
            "content-type": "application/x-www-form-urlencoded"
        }
        data = UriHandler.open("https://gigya-merge.videoland.com/accounts.getAccountInfo", additional_headers=headers, data=profile_data)
        json_data = JsonHelper(data)
        if json_data.get_value("errorCode"):
            error = json_data.get_value("statusReason")
            error = json_data.get_value("errorMessage", fallback=error)
            Logger.error(f"Gigya: getAccountInfo failed: {error}")
            return AuthenticationResult(None)

        username = json_data.get_value("profile", "email")
        self.__extract_token_info(json_data)
        return AuthenticationResult(username, existing_login=True)

    def log_off(self, username) -> bool:
        UriHandler.delete_cookie(domain=".gigya.com")
        UriHandler.delete_cookie(domain=f".{self.realm}")
        return True

    def get_authentication_token(self) -> Optional[str]:
        url = "https://front-auth.videoland.bedrock.tech/v2/platforms/m6group_web/getJwt"
        headers = {
            "x-auth-device-id": self._device_id,
            "x-auth-gigya-signature": self.__uid_signature,
            "x-auth-gigya-signature-timestamp": str(self.__uid_signature_timestamp),
            "x-auth-gigya-uid": self.__uid
        }

        token = UriHandler.open(url, additional_headers=headers, no_cache=True)
        if token:
            return JsonHelper(token).get_value("token")
        return None

    def __extract_token_info(self, token: JsonHelper) -> None:
        self.__uid = token.get_value("UID")
        self.__uid_signature = token.get_value("UIDSignature")
        self.__uid_signature_timestamp = token.get_value("signatureTimestamp")