from typing import List
import base64
import json
from dataclasses import dataclass
from typing import Dict
from typing import Literal
from typing import Optional
from typing import TYPE_CHECKING
from urllib.parse import quote
from urllib.parse import urlencode

from resources.lib.addonsettings import AddonSettings
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper

if TYPE_CHECKING:
    from resources.lib.mediaitem import MediaStream

KeyType = Literal["R", "A", "B", "D", "b"]


@dataclass
class InputStreamAdaptiveDrmConfig:
    license_type: Literal["com.widevine.alpha", "com.microsoft.playready", "org.w3.clearkey"]
    server_url: str
    server_certificate: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    params: Optional[str] = None
    data: Optional[Dict[str, str]] = None
    wrapper: Optional[Literal["base64", "urlenc", "none"]] = None
    unwrappers: Optional[List[Literal["auto", "base64", "json", "xml", "none"]]] = None
    unwrapper_params: Optional[Dict[str, str]] = None
    key_ids: Optional[Dict[str, str]] = None
    key_type: KeyType = "R"
    init_data: Optional[str] = None
    persistent_storage: Optional[bool] = None
    force_single_session: Optional[bool] = None
    optional_key_req_params: Optional[Dict[str, str]] = None


class InputStream:
    addon: str

    def __init__(self, addon: str = "inputstream.adaptive"):
        self.addon = addon

    def set_input_stream_addon_input(
            self,
            strm: "MediaStream",
            drm_config: Optional[InputStreamAdaptiveDrmConfig] = None,

            max_bit_rate: Optional[int] = 0,

            stream_headers: Optional[Dict[str, str]] = None,
            stream_parameters: Optional[Dict[str, str]] = None,

            manifest_params: Optional[Dict[str, str]] = None,
            manifest_headers: Optional[Dict[str, str]] = None,
            manifest_upd_params: Optional[Dict[str, str]] = None,
            manifest_update_params: Optional[str] = None
        ) -> "MediaStream":

        """ Updates an existing stream with parameters for the inputstream adaptive add-on.

        :param strm:                    The MediaStream to update.
        :param drm_config:              A DRM Configuration object (optional).
        :param max_bit_rate:            The maximum bitrate to use (optional).

        :param stream_headers:          Possible HTTP Headers for the stream.
        :param stream_parameters:       The stream parameters.
        :param manifest_headers:        The headers to add to the manifest request.
        :param manifest_params:         The parameters to asdd to the manifest request.
        :param manifest_upd_params:     The request parameters for the manifest update
                                        requests (Available in Omega and up)
        :param manifest_update_params:  How should the manifest be updated ("full"). This parameter
                                        is unavailable in Omega and later.

        :return: An updated stream.

        Can be used like this:

            stream = item.add_stream(stream_url, 0)
            M3u8.set_input_stream_addon_input(stream)
            item.complete = True

        if maxBitRate is not set, the bitrate will be configured via the normal generic Retrospect
        or channel settings.

        https://github.com/xbmc/inputstream.adaptive/wiki/Integration

        """

        strm.Adaptive = True  # NOSONAR

        # License Stuff for Piers and later
        if drm_config and AddonSettings.is_min_version(AddonSettings.KodiPiers):
            # https://github.com/xbmc/inputstream.adaptive/wiki/Integration-DRM
            drm_configs = {
                drm_config.license_type: {
                    "license": {
                        "server_certificate": drm_config.server_certificate,
                        # Server URL
                        # URL: it can also override the one embedded in the manifest, if any4
                        # URI "data" scheme: Only ClearKey DRM, example data:application/json;base64,CK_LICENSE_AS_BASE64
                        # {CHA-B64U} To inject to the URL the DRM Challenge as base64, URL encoded
                        # {CHA-MD5} To inject to the URL the DRM Challenge hashed as MD5
                        "server_url": drm_config.server_url,
                        "req_headers": urlencode(drm_config.headers) if drm_config.headers else None,
                        "req_params": drm_config.params,
                        "req_data": base64.b64encode(json.dumps(drm_config.data).encode("utf-8")).decode("utf-8") if drm_config.data else None,
                        "wrapper": drm_config.wrapper,  # Widevine only
                        "unwrapper": ",".join(drm_config.unwrappers) if drm_config.unwrappers else None,  # Widevine only
                        "unwrapper_params": drm_config.unwrapper_params,  # Widevine only
                        "keyids": drm_config.key_ids  # ClearKey DRM
                    },
                    # Init Data: Base64 data. For the Widevine PSSH case, two placeholders
                    # {KID} to inject the KID as bytes
                    # {UUID} to inject the KID as UUID string
                    "init_data": drm_config.init_data,
                    "persistent_storage": drm_config.persistent_storage,
                    "force_single_session": drm_config.force_single_session,
                    "optional_key_req_params": drm_config.optional_key_req_params
                }
            }

            def remove_none(data: dict) -> dict:
                """ Removes None values from a dict """
                return {
                    key: remove_none(value) if isinstance(value, dict) else value
                    for key, value in data.items()
                    if value is not None
                }

            drm_config_json = json.dumps(remove_none(drm_configs))
            strm.add_property("inputstream.adaptive.drm", drm_config_json)

        # Pre-Piers License configuration
        elif drm_config:
            strm.add_property("inputstream.adaptive.license_type", drm_config.license_type)

            json_filter: str = ""
            if drm_config.unwrappers and drm_config.unwrapper_params:
                json_filters = [w[0].upper() for w in drm_config.unwrappers]
                json_property = drm_config.unwrapper_params.get("path_data")
                json_filter = f"{''.join(json_filters)}{json_property}" if json_filters and json_property else ""

            license_key = self.__get_license_server_format(
                license_server_url=drm_config.server_url,
                key_type=drm_config.key_type,
                key_headers=drm_config.headers,
                key_value=drm_config.params or "",
                json_filter=json_filter
            )
            strm.add_property("inputstream.adaptive.license_key", license_key)

        strm.add_property("inputstream", self.addon)

        if max_bit_rate:
            strm.add_property("inputstream.adaptive.chooser_bandwidth_max", str(max_bit_rate * 1000))

        # InputStream Adaptive non-DRM stuff
        if stream_headers:
            # On Kodi v20 (Nexus): Specifies the HTTP headers to be used to download manifests
            # and streams (audio/video/subtitles).
            # NOTE: Use this property to set headers to the manifests is a deprecated behavior,
            # use inputstream.adaptive.manifest_headers instead.

            # From Kodi v21 (Omega) or above:
            # Specifies the HTTP headers to be used to download streams (audio/video/subtitles) only.

            # pyrefly: ignore [bad-argument-type]
            params = urlencode(stream_headers, quote_via=quote)
            strm.add_property("inputstream.adaptive.stream_headers", params)

        if stream_parameters:
            # pyrefly: ignore [bad-argument-type]
            params = urlencode(stream_parameters, quote_via=quote)
            strm.add_property("inputstream.adaptive.stream_params", params)

        # Manifest stuff
        if manifest_params:
            # pyrefly: ignore [bad-argument-type]
            params = urlencode(manifest_params, quote_via=quote)
            strm.add_property("inputstream.adaptive.manifest_params", params)

        if manifest_headers:
            # pyrefly: ignore [bad-argument-type]
            params = urlencode(manifest_headers, quote_via=quote)
            strm.add_property("inputstream.adaptive.manifest_headers", params)

        elif stream_headers:
            # Fallback to stream headers.
            # pyrefly: ignore [bad-argument-type]
            params = urlencode(stream_headers, quote_via=quote)
            strm.add_property("inputstream.adaptive.manifest_headers", params)

        if manifest_update_params and not AddonSettings.is_min_version(AddonSettings.KodiOmega):
            # Works on Nexus (v20) and below and can set
            strm.add_property("inputstream.adaptive.manifest_update_parameter", manifest_update_params)

        if manifest_upd_params and AddonSettings.is_min_version(AddonSettings.KodiOmega):
            # pyrefly: ignore [bad-argument-type]
            params = urlencode(manifest_upd_params, quote_via=quote)
            strm.add_property("inputstream.adaptive.manifest_upd_params", params)

        return strm

    def __get_license_server_format(self, license_server_url: str,
                                    key_type: KeyType = "R",
                                    key_headers: Optional[Dict[str, str]] = None,
                                    key_value: str = "", json_filter: str = ""):
        """ Generates a property license key value

        # A{SSM} -> not implemented
        # R{SSM} -> raw format
        # B{SSM} -> base64 format URL encoded (b{ssmm} will not URL encode)
        # D{SSM} -> decimal format

        The generic format for a LicenseKey is:
        |<url>|<headers>|<key with placeholders>|<optional json filter>

        The Widevine Decryption Key Identifier (KID) can be inserted via the placeholder {KID}

        :param license_server_url:  The URL where the license key can be obtained.
        :param key_type:            The key type (A, R, B or D).
        :param key_headers:         A dictionary that contains the HTTP headers to pass.
        :param key_value:           The value that is being passed on as the key value.
        :param json_filter:         If specified selects that json element to extract the
                                    key response. Should describe a sequence: JB<tag> for JSON  and then
                                    B type.

        :return: A formatted license string that can be passed to the adaptive input add-on.
        :rtype: str

        """

        # [R/b/B/D]{SSM} placeholder to transport the DRM Challenge
        # With it you can use also other optional placeholders as:
        # [R/b/B]{SID} placeholder to transport the DRM Session ID
        # [R/H]{KID} placeholder to transport the DRM Key ID
        # [b/B]{PSSH} placeholder to transport the initial PSSH (Android only)
        #
        # R - The data will be kept as is raw
        # b - The data will be base64 encoded
        # B - The data will be base64 encoded and URL encoded
        # D - The data will be decimal converted (each char converted as integer concatenated by comma)
        # H - The data will be hexadecimal converted (each character converted as hexadecimal and concatenated)
        header = ""
        if key_headers:
            for k, v in key_headers.items():
                header = "{0}&{1}={2}".format(header, k, HtmlEntityHelper.url_encode(v))

        if key_type in ("A", "R", "B"):
            key_value = "{0}{{SSM}}".format(key_type)
        elif key_type == "D":
            if key_value and "D{SSM}" not in key_value:
                raise ValueError("Missing D{SSM} placeholder")
            key_value = HtmlEntityHelper.url_encode(key_value)

        return "{0}|{1}|{2}|{3}".format(license_server_url, header.strip("&"), key_value, json_filter)
