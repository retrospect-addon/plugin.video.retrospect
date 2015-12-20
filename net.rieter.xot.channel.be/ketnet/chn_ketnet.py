# coding:Cp1252
import urlparse

import mediaitem
import chn_class

from helpers import htmlhelper
from regexer import Regexer
from logger import Logger
from urihandler import UriHandler


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channelInfo):
        """Initialisation of the class.

        Arguments:
        channelInfo: ChannelInfo - The channel info object to base this channel on.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channelInfo)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============

        if self.channelCode == "redactie":
            self.noImage = "redactieimage.png"
            self.mainListUri = "http://www.deredactie.be/cm/vrtnieuws/mediatheek"
            self.baseUrl = "http://www.deredactie.be"

        elif self.channelCode == "ketnet":
            self.noImage = "ketnetimage.png"
            self.mainListUri = "http://video.ketnet.be/cm/ketnet/ketnet-mediaplayer"
            self.baseUrl = "http://video.ketnet.be"

        elif self.channelCode == "sporza":
            self.noImage = "sporzaimage.png"
            self.mainListUri = "http://www.sporza.be/cm/sporza/videozone"
            self.baseUrl = "http://www.sporza.be"

        elif self.channelCode == "cobra":
            self.noImage = "cobraimage.png"
            self.mainListUri = "http://www.cobra.be/cm/cobra/cobra-mediaplayer"
            self.baseUrl = "http://www.cobra.be"

        self.swfUrl = "%s/html/flash/common/player.swf" % (self.baseUrl,)

        # setup the main parsing data
        self.episodeItemRegex = '<div><a href="(/cm(?:/[^/"]+){3})" [^>]+>(?:([^<]+)|<img [^>]+alt="([^"]+)"/>)</a></div>'
        self.videoItemRegex = '(?:<h3><[^>]+><strong>([^<]+)</strong></h3>|(<div class="mediaItem"[\W\w]+?</div>))'
        self.mediaUrlRegex = "Server'] = '([^']+)';\W+[^]]+Path'] = '([^']+)';"
        self.pageNavigationRegex = '<a href="([^"]+\?page=\d+)"[^>]+>(\d+)'
        self.pageNavigationRegexIndex = 1

        # ====================================== Actual channel setup STOPS here =======================================
        return
    
    # def ParseMainList(self, returnData=False):
    #     """Parses the mainlist of the channel and returns a list of MediaItems
    #
    #     This method creates a list of MediaItems that represent all the different
    #     programs that are available in the online source. The list is used to fill
    #     the ProgWindow.
    #
    #     Keyword parameters:
    #     returnData : [opt] boolean - If set to true, it will return the retrieved
    #                                  data as well
    #
    #     Returns a list of MediaItems that were retrieved.
    #
    #     """
    #
    #     (items, data) = chn_class.Channel.ParseMainList(self, returnData=True)
    #
    #     if not data == "":
    #         # if data was retrieved, fetch the child items
    #         for item in items:
    #             urlPart = urlparse.urlsplit(item.url)[2]
    #             subRegex = '<a href="(%s/[^"]+)" title\W+"([^"]+)' % (urlPart, )
    #             results = Regexer.DoRegex(subRegex, data)
    #             for resultSet in results:
    #                 subItem = self.CreateFolderItem(resultSet)
    #                 subItem.parent = item
    #                 item.items.append(subItem)
    #
    #     if returnData:
    #         return items, data
    #     else:
    #         return items

    def CreateEpisodeItem(self, resultSet):
        """Creates a new MediaItem for an episode
        
        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex
        
        Returns:
        A new MediaItem of type 'folder'
        
        This method creates a new MediaItem from the Regular Expression 
        results <resultSet>. The method should be implemented by derived classes 
        and are specific to the channel.
         
        """
        
        url = "%s%s" % (self.baseUrl, resultSet[0])
        if resultSet[1] == "":
            name = resultSet[2]
        else:
            name = resultSet[1]
        
        item = mediaitem.MediaItem(name.capitalize(), url)
        item.icon = self.icon
        item.type = "folder"
        item.complete = True
        return item
    
    def CreateFolderItem(self, resultSet):
        """Creates a MediaItem of type 'folder' using the resultSet from the regex.
        
        Arguments:
        resultSet : tuple(strig) - the resultSet of the self.folderItemRegex
        
        Returns:
        A new MediaItem of type 'folder'
        
        This method creates a new MediaItem from the Regular Expression 
        results <resultSet>. The method should be implemented by derived classes 
        and are specific to the channel.
         
        """
        
        name = "%s%s" % (resultSet[1][0].upper(), resultSet[1][1:])                
        item = mediaitem.MediaItem(name, urlparse.urljoin(self.baseUrl, resultSet[0]))
        item.complete = True
        item.thumb = self.noImage
        return item
    
    def CreateVideoItem(self, resultSet):
        """Creates a MediaItem of type 'video' using the resultSet from the regex.
        
        Arguments:
        resultSet : tuple (string) - the resultSet of the self.videoItemRegex
        
        Returns:
        A new MediaItem of type 'video' or 'audio' (despite the method's name)
        
        This method creates a new MediaItem from the Regular Expression 
        results <resultSet>. The method should be implemented by derived classes 
        and are specific to the channel.
        
        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.UpdateVideoItem method is called if the item is focused or selected
        for playback.
         
        """

        html = htmlhelper.HtmlHelper(resultSet[1])
        url = html.GetTagAttribute("div", {"class": "mediaItem"}, {"id": None})
        if not ":" in url:
            url = "%s%s" % (self.baseUrl, url)
        
        name = html.GetTagAttribute("img", {"title": None})
        
        thumb = html.GetTagAttribute("img", {"src": None})
        if not ":" in thumb:
            thumb = "http://www.deredactie.be%s" % (thumb,)
        
        item = mediaitem.MediaItem(name, url)
        item.thumb = thumb
        item.description = name
        item.icon = self.icon
        item.type = 'video'
        item.complete = False
        return item
    
    def UpdateVideoItem(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL 
        and the Thumb! It should return a completed item. 
        """
        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        # noinspection PyStatementEffect
        """
        vars267354594['type'] = 'video';
        vars267354594['view'] = 'popupPlayer';
        vars267354594['divId'] = 'div_267354594';
        vars267354594['flashId'] = 'flash_267354594';
        vars267354594['format'] = '';
        vars267354594['wmode'] = 'transparent';
        vars267354594['title'] = encodeURIComponent('De familievete van Marijke Pinoy en Dimitri Verhulst');
        vars267354594['rtmpServer'] = 'rtmp://vrt.flash.streampower.be/sporza';
        vars267354594['rtmpPath'] = '2011/07/121632590GINDSTUSS5088380.urlFLVLong.flv';
        vars267354594['rtmptServer'] = 'rtmpt://vrt.flash.streampower.be/sporza';
        vars267354594['rtmptPath'] = '2011/07/121632590GINDSTUSS5088380.urlFLVLong.flv';
        vars267354594['iphoneServer'] = 'http://iphone.streampower.be/vrtnieuws_nogeo/_definst_';
        vars267354594['iphonePath'] = '2011/07/121632590GINDSTUSS5088380.urlMP4_H.264.m4v';
        vars267354594['mobileServer'] = 'rtsp://mp4.streampower.be/vrt/vrt_mobile/sporza_nogeo';
        vars267354594['mobilePath'] = '2011/07/121632590GINDSTUSS5088380.url3GP_MPEG4.3gp';
        vars267354594['thumb'] = '/polopoly_fs/1.1066851!image/1223351651.png';
        """
        
        # now the mediaurl is derived. First we try WMV
        data = UriHandler.Open(item.url)
        
        descriptions = Regexer.DoRegex('<div class="longdesc"><p>([^<]+)</', data)
        for desc in descriptions:
            item.description = desc
            
        data = data.replace("\\/", "/")
        urls = Regexer.DoRegex(self.mediaUrlRegex, data)
        part = item.CreateNewEmptyMediaPart()
        for url in urls:
            server = url[0]
            path = url[1]
            
            if server != "":
                if server.startswith("rtmp:") or server.startswith("rtmpt:"):
                    mediaUrl = "%s//%s" % (server, path)
                    mediaUrl = self.GetVerifiableVideoUrl(mediaUrl)
                    part.AppendMediaStream(mediaUrl, 800)
                elif "_definst_" in server:
                    continue
#                    #http://iphone.streampower.be/vrtnieuws_nogeo/_definst_/2011/07/151204967HOORENSVL2123520.urlMP4_H.264.m4v/playlist.m3u8
#                    bitrate = 1200
#                    mediaurl = mediaurl.replace("definst_//", "definst_/")+"/playlist.m3u8"
#                    mobileData = UriHandler.Open(mediaurl)
#                    mobileUrls = Regexer.DoRegex("BANDWIDTH=(\d+)\d{3}\W+(http://[^\n]+)", mobileData) @@ Use the M3u8
#                    parser for this
#                    for mobileUrl in mobileUrls:
#                        part.AppendMediaStream(mobileUrl[1], mobileUrl[0])
                else:
                    mediaUrl = "%s/%s" % (server, path)
                    part.AppendMediaStream(mediaUrl, 100)
                item.complete = True
        else:
            Logger.Debug("Media url was not found.")

        return item    
