# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import chn_class
from resources.lib.channelinfo import ChannelInfo


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channel_info: ChannelInfo):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "de-schatkamer-image.jpg"
