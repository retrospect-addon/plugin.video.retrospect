#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons 
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a 
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California 94105, USA.
#===============================================================================


class ContextMenuItem:
    """Context menu item class that is used to pass on contextmenu items."""

    def __init__(self, label, functionName, itemTypes=None):
        """Instantiation of the class. 
        
        Arguments:
        label          : string - The label/name of the item
        functionName   : string - The name of the method that is called when the item is selcted
        
        Keyword Arguments:
        itemTypes      : list[string] - The MediaItem types for which the contextitem 
                                        should be shown [optional]
        completeStatus : boolean      - Indication whether the item should only 
                                        be shown if the MediaItem.status equals 
                                        this value.

        """

        self.label = label
        self.functionName = functionName
        self.itemTypes = itemTypes

    def __str__(self):
        """Returns the string representation of the contextmenu item"""

        return "%s (%s), Types:%s" % (
            self.label, self.functionName, self.itemTypes)
