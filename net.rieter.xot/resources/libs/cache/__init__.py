#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons 
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a 
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California 94105, USA.
#===============================================================================
__all__ = ["cachedhttpresponse", "cachehandler", "cachehttphandler"
           "filecache", "memeorycache", "cachebase"]

if __name__ == "__main__":
    import urllib2
    import datetime

    from memorycache import MemoryCache
    from filecache import FileCache
    from cachehttphandler import CacheHttpHandler
    from cachehandler import CacheHandler

    # noinspection PyUnusedLocal
    class DummyLogger:
        """ Just a dummy logger class that can be used to test"""
        
        def __init__(self):
            pass
        
        def Error(self, message, *args, **kwargs):
            message = "Dummy ERROR >> %s" % (message,)
            print message % args
        
        def Debug(self, message, *args, **kwargs):
            message = "Dummy>> %s" % (message,)
            print message % args
    
    cacheObject = MemoryCache(maxExpiredTime=300, logger=DummyLogger())
    #cacheObject = FileCache(cachePath = "d:\\temp\\www\\", maxExpiredTime=300, logger=DummyLogger())
    
    #@CacheHandler(cacheObject=cacheObject, logger=DummyLogger())
    # noinspection PyUnusedLocal
    def OpenUrl(url, headerOnly=False, params=""):
        print "OpenUrl :: Opening: %s [headerOnly=%s]" % (url, headerOnly)
        proxyHandler = urllib2.ProxyHandler({"http": "http://localhost:8888"})
        
        cacheHandler = CacheHttpHandler(cacheObject, logger=DummyLogger())
        opener = urllib2.build_opener(proxyHandler, cacheHandler)
        
        #opener = urllib2.build_opener(proxyHandler)
        handle = opener.open(url)
        return handle
    
    start = datetime.datetime.now()
    
    for i in range(0, 2):
        #OpenUrl("http://www.nu.nl").read()
        #print OpenUrl("http://beta.uitzendinggemist.nl/programmas?page=1&toon=nieuwste_eerst&weergave=lijst").info() # must validate
        DummyLogger().Debug("=============================================================")
        OpenUrl("http://www.net5.nl/programmas/het-blok/videos/")  # expires in 15 minutes
        #time.sleep(20)
    
    print "Time Taken: %s" % (datetime.datetime.now() - start,)
