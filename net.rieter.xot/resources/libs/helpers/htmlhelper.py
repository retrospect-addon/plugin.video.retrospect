#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons 
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a 
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California 94105, USA.
#===============================================================================

from regexer import Regexer
from helpers import taghelperbase
#from logger import Logger


class HtmlHelper(taghelperbase.TagHelperBase):
    """Class that could help with parsing of simple HTML"""
    
    def GetTagContent(self, tag, *args, **kwargs):        
        """Gets the content of an HTML <tag> 
        
        Arguments:
        tag    : string     - name of tag to search for.
        **args : dictionary - each argument is interpreted as a html 
                              attribute. 'cls' is translated to class 
                              attribute. The attribute with value None 
                              is retrieved.
        
        Keyword Arguments:
        firstOnly : [opt] boolean - only return the first result. Default: True
        
        Returns:
        The content of the found tag. If no match is found an empty string is 
        returned.
        
        Example: ('div', {'cls':'test'}, {'id':'divTest'}) will match 
        <div class="test" id="divTest">...content...</div> 
        
        """
        
        firstOnly = True
        if kwargs.keys().count("firstOnly") > 0:
            firstOnly = kwargs["firstOnly"]
            #Logger.Trace("Setting 'firstOnly' to '%s'", firstOnly)
            
        htmlRegex = "<%s" % (tag,)
                
        #Logger.Debug(args)
        for arg in args:
            name = arg.keys()[0]
            value = arg[arg.keys()[0]]
            #Logger.Debug("Name: %s, Value: %s", name, value)
            
            # to keep working with older versions where class could not be passed
            if name == "cls":
                name = "class"

            htmlRegex += '[^>]*%s\W*=\W*["\']%s["\']' % (name, value)

        htmlRegex += "[^>]*>([^<]+)</"
        #Logger.Debug("HtmlRegex = %s", htmlRegex)
        
        result = Regexer.DoRegex(htmlRegex, self.data)
        if len(result) > 0:
            if firstOnly:
                return result[0].strip()
            else:
                return result
        else:
            return ""
