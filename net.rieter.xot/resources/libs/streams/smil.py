#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons 
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a 
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California 94105, USA.
#===============================================================================
import string

from regexer import Regexer

#===============================================================================
# Make global object available
#===============================================================================
#from logger import Logger


class Smil:
    """Class that could help with parsing of simple Smil files"""
    
    def __init__(self, data):
        """Creates a class object with Smil <data>
        
        Arguments:
        data : string - Smil data to parse
        
        Example data:
        
        <smil xmlns="http://www.w3.org/2001/SMIL20/Language">
        <head>
           <meta name="title" content="myStream"/>
           <meta name="httpBase" content="http://mydomain.com/"/>
           <meta name="rtmpPlaybackBase" content="http://mydomain.com/"/>
        </head>
        <body>
           <switch>
              <video src="myStream500K@54552" system-bitrate="500000"/>
              <video src="myStream900K@54552" system-bitrate="900000"/>
              <video src="myStream1500K@54552" system-bitrate="1500000"/>
           </switch>
        </body>
        
        """
        
        self.data = data
    
    def GetBaseUrl(self):
        """Retrieves the BaseUrl from the Smil data.
        
        From the example data it would be http://mydomain.com
        
        """
        
        regex = '<meta base="([^"]+)" />'
        results = Regexer.DoRegex(regex, self.data)
        if len(results) > 0:
            return results[0]
        else:
            regex = '<meta name="httpBase" content="([^"]+)"\W*/>'
            results = Regexer.DoRegex(regex, self.data)
            if len(results) > 0:
                return results[0]
            else:            
                return ""
    
    def GetBestVideo(self):
        """Returns a list of video's with the highest quality.
        
        In this case: myStream1500K@54552
        
        """
        
        urls = self.GetVideosAndBitrates()
        if urls is None:
            return ""
        
        urls.sort(lambda x, y: int(y[1]) - int(x[1]))
        return urls[0][0]
    
    def GetVideosAndBitrates(self):
        """Returns a list of all video's and bitrates in the Smil file. 
        
        In this case:
            ["myStream500K@54552", "500000"]
            ["myStream900K@54552", "900000"]
            ["myStream1500K@54552", "1500000"]
        
        """
        
        regex = '<video src="([^"]+)"[^>]+system-bitrate="([^"]+)"'
        results = Regexer.DoRegex(regex, self.data)
        if len(results) > 0:
            return results
        else:
            return None
    
    def GetSubtitle(self):
        """ Retrieves the URL of the included subtitle"""
        
        regex = '<param\W*name="subtitle"[^>]*value="([^"]+)'
        urls = Regexer.DoRegex(regex, self.data)
        
        for url in urls:
            if "http:" in url:            
                return url
            else:
                return "%s/%s" % (self.GetBaseUrl().rstrip("/"), url.lstrip("/"))
        
        return ""
    
    def StripTypeStart(self, url):
        """Strips the first part of an URL up to the first /
        
        Arguments: 
        url : string - the URL to strip
        
        Returns:
        The stripped URL, duh!
        
        Example:
        mp4:/mp4root/2009-04-14/pid201_671978_T1L__671978_T6MP48_.mp4 -> /mp4root/2009-04-14/pid201_671978_T1L__671978_T6MP48_.mp4 
           
        """
        
        pos = string.find(url, '/')
        return url[pos:] 