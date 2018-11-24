#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import pyamf
from pyamf import remoting
import httplib

# prevent cpyamf to be the main PyAMF module (See #720)
import sys
sys.modules['cpyamf'] = sys.modules['pyamf']


class BrightCove:
    """ BrightCove is used to get video info of videos that use the
    BrightCover SWF player.

    """

    def __init__(self, logger, player_key, content_id, url, seed,
                 experience_id=0, amf_version=3, proxy=None):
        """ Initializes the BrightCove class """

        self.playerKey = player_key
        self.contentId = content_id
        self.url = url
        self.seed = seed
        self.experienceId = experience_id
        self.amfVersion = amf_version

        self.proxy = proxy

        self.logger = logger
        self.data = self.__get_bright_cove_data()
        return

    def get_description(self):
        """ Retrieves the full description """

        description = self.data['longDescription']

        if description:
            # The result is Unicode, so we should encode it.
            return self.data['longDescription']
        return ""

    def get_stream_info(self, renditions="renditions"):
        """ Returns the streams in the form of a list of
        tuples (streamUrl, bitrate).

        """

        streams = []
        stream_data = self.data[renditions]
        for stream in stream_data:
            bitrate = int(stream['encodingRate']) / 1000
            # The result is Unicode, so we should encode it.
            strm = stream['defaultURL']
            streams.append((strm, bitrate))

        return streams

    def __get_bright_cove_data(self):
        """ Retrieves the Url's from a brightcove stream

        Arguments:
        playerKey : string - Key identifying the current request
        contentId : int    - ID of the content to retrieve
        url       : string - Url of the page that calls the video SWF
        seed      : string - Constant which depends on the website

        Keyword Arguments:
        experienceId : id     - <unknown parameter>

        Returns a dictionary with the data

        """

        # Seed = 61773bc7479ab4e69a5214f17fd4afd21fe1987a
        envelope = self.__build_bright_cove_amf_request(self.playerKey, self.contentId, self.url, self.experienceId, self.seed)

        if self.proxy:
            connection = httplib.HTTPConnection(self.proxy.Proxy, self.proxy.Port)
        else:
            connection = httplib.HTTPConnection("c.brightcove.com")

        connection.request("POST", "http://c.brightcove.com/services/messagebroker/amf?playerKey=" + self.playerKey, str(remoting.encode(envelope).read()), {'content-type': 'application/x-amf'})
        response = connection.getresponse().read()
        response = remoting.decode(response).bodies[0][1].body

        if self.logger:
            self.logger.trace(response)

        return response['programmedContent']['videoPlayer']['mediaDTO']

    def __build_bright_cove_amf_request(self, player_key, content_id, url, experience_id, seed):
        """ Builds a AMF request compatible with BrightCove

        Arguments:
        playerKey : string - Key identifying the current request
        contentId : int    - ID of the content to retrieve
        url       : string - Url of the page that calls the video SWF
        seed      : string - Constant which depends on the website

        Keyword Arguments:
        experienceId : id     - <unknown parameter>

        Returns a valid Brightcove request

        """

        if self.logger:
            self.logger.debug("Creating BrightCover request for ContentId=%s, Key=%s, ExperienceId=%s, url=%s", content_id, player_key, experience_id, url)

        pyamf.register_class(ViewerExperienceRequest, 'com.brightcove.experience.ViewerExperienceRequest')
        pyamf.register_class(ContentOverride, 'com.brightcove.experience.ContentOverride')

        content_overrides = [ContentOverride(str(content_id))]
        viewer_experience_request = ViewerExperienceRequest(url, content_overrides, int(experience_id), player_key)

        envelope = remoting.Envelope(amfVersion=self.amfVersion)
        remoting_request = remoting.Request(target="com.brightcove.experience.ExperienceRuntimeFacade.getDataForExperience", body=[seed, viewer_experience_request], envelope=envelope)
        envelope.bodies.append(("/1", remoting_request))

        return envelope


class ViewerExperienceRequest(object):
    """ Class needed for brightcove AMF requests """
    def __init__(self, url, content_overrides, experience_id, player_key, ttl_token=''):
        self.TTLToken = ttl_token
        self.URL = url
        self.deliveryType = float(0)
        self.contentOverrides = content_overrides
        self.experienceId = experience_id
        self.playerKey = player_key


class ContentOverride(object):
    """ Class needed for brightcove AMF requests """
    def __init__(self, content_id, content_type=0, target='videoPlayer'):
        self.contentType = content_type
        self.contentId = content_id
        self.target = target
        self.contentIds = None
        self.contentRefId = None
        self.contentRefIds = None
        self.contentType = 0
        self.featureId = float(0)
        self.featuredRefId = None
