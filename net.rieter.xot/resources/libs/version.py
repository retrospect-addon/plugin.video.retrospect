#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons 
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a 
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California 94105, USA.
#===============================================================================


class Comparable:
    """ 
    Base Class for a simple comparison class. A derived class only needs to
    implement an __lt__(self, other) method. All the other required methods are
    implemented by this Comparable class and are based on the __lt__ method.
    
    """

    def __init__(self):
        pass

    def __eq__(self, other):
        """ Test two objects 'for Equality'
        
        Arguments:
        other : Object - The other object.
        
        Returns:
        True or False
        
        """

        if other is None:
            return False

        return not self < other and not other < self

    def __ne__(self, other):
        """ Test two objects 'for non-equality'  
        
        Arguments:
        other : Object - The other object.
        
        Returns:
        True or False
        
        """

        #print "__ne__"
        return not self.__eq__(other)

    def __gt__(self, other):
        """ Test two objects for 'greater than'
        
        Arguments:
        other : Object - The other object.
        
        Returns:
        True or False
        
        """

        #print "__gt__"
        return other < self

    def __ge__(self, other):
        """ Test two objects for 'greater or equal than'  
        
        Arguments:
        other : Object - The other object.
        
        Returns:
        True or False
        
        """

        #print "__ge__"
        return not self < other

    def __le__(self, other):
        """ Test two objects for 'less than or equal'
        
        Arguments:
        other : Object - The other object.
        
        Returns:
        True or False
        
        """

        #print "__le__"
        return not other < self


class Version(Comparable):
    """ Class representing a version number """

    def __init__(self, version=None, major=None, minor=None, revision=None, build=None):
        """ Initialises a new version number

        Keyword arguments:
        version  : String  - Version string
        major    : Integer - The Major build number
        minor    : Integer - The Minor build number
        revision : Integer - The Revision number
        build    : Integer - The Build number

        """

        Comparable.__init__(self)

        if version is None and major is None and minor is None and revision is None and build is None:
            raise ValueError("Either a version string or a set of version numbers should be provided.")

        if version and not (major is None and minor is None and revision is None and build is None):
            raise ValueError("Only a complete version or a set of version numbers should be provided, not both.")

        if major is None and not (minor is None and revision is None and build is None):
            raise ValueError("A Major version must be provided if a minor, revision or build is provided.")

        if minor is None and not (revision is None and build is None):
            raise ValueError("A Minor version must be provided if a revision or build is provided.")

        if revision is None and build is not None:
            raise ValueError("A Revision number must be provided if a build is provided.")

        self.major = major
        self.minor = minor
        self.revision = revision
        self.build = build
        if version:
            self.__ExtractVersion(version)

    def EqualRevisions(self, other):
        """ Checks if two versions have the same version up until the revision 
        part of the version 
        
        Arguments:
        other : Version - The version to compare with.
        
        Returns:
        True or False
        
        """

        if other is None:
            return False

        thisVersion = Version(major=self.major, minor=self.minor, revision=self.revision)
        otherVersion = Version(major=other.major, minor=other.minor, revision=other.revision)

        return thisVersion == otherVersion

    def __ExtractVersion(self, version):
        """ Extracts the Major, Minor, Revision and Buildnumber from a version string
        
        Arguments:
        version : String - The version string
        
        """

        split = str(version).split('.')
        if len(split) > 0:
            self.major = int(split[0])
        if len(split) > 1:
            self.minor = int(split[1])
        if len(split) > 2:
            self.revision = int(split[2])
        if len(split) > 3:
            self.build = int(split[3])

    def __NoneIsZero(self, value):
        """ Returns 0 if a value is None. This is needed for comparison. As None
        should be interpreted as Zero. 
        
        Arguments: 
        value : Integer - The value to check for None
        
        """

        if value is None:
            #print "None -> zero"
            return 0
        return int(value)

    def __str__(self):
        """ String representation """

        if self.major is None:
            return "None"
        elif self.minor is None:
            return str(self.major)
        elif self.revision is None:
            return "%s.%s" % (self.major, self.minor)
        elif self.build is None:
            return "%s.%s.%s" % (self.major, self.minor, self.revision)
        else:
            return "%s.%s.%s.%s" % (self.major, self.minor, self.revision, self.build)

    def __lt__(self, other):
        """ Tests two versios for 'Lower Then' 
        
        Arguments:
        other : Version - The version to compare with.
        
        Returns:
        True or False
        
        """

        if not self.__NoneIsZero(self.major) == self.__NoneIsZero(other.major):
            #print "Match major"
            return self.__NoneIsZero(self.major) < self.__NoneIsZero(other.major)

        if not self.__NoneIsZero(self.minor) == self.__NoneIsZero(other.minor):
            #print "Match minor"
            return self.__NoneIsZero(self.minor) < self.__NoneIsZero(other.minor)

        if not self.__NoneIsZero(self.revision) == self.__NoneIsZero(other.revision):
            #print "Match revision"
            return self.__NoneIsZero(self.revision) < self.__NoneIsZero(other.revision)

        #print "Match build: %s < %s" % (self.__NoneIsZero(self.build), self.__NoneIsZero(other.build))         
        return self.__NoneIsZero(self.build) < self.__NoneIsZero(other.build)


if __name__ == "__main__":
    # version = Version()
    # version = Version(version="2.1.2.0", major=2, minor=1, revision=2, build=0)
    # version = Version(major=2, minor=None, revision=2, build=0)
    # version = Version(major=2, minor=None, revision=2, build=None)
    # version = Version(major=2, minor=1, revision=2, build=0)
    # version = Version(version="2.1.2.0")
    # version = Version(version="2.1.2")
    # version = Version(version="2.1")
    # version = Version(version="2")

    lowestVersion = Version(major=2, minor=1, revision=2, build=1)
    middleVersion = Version(version="2.1.3.1")
    highestVersion = Version(version="2.1.3.5")
    print "%s <  %s = %s" % (lowestVersion, middleVersion, lowestVersion < middleVersion)
    if not lowestVersion < middleVersion:
        raise ArithmeticError()

    print "%s <= %s = %s" % (lowestVersion, middleVersion, lowestVersion <= middleVersion)
    if not lowestVersion <= middleVersion:
        raise ArithmeticError()

    print "%s <= %s = %s" % (lowestVersion, lowestVersion, lowestVersion <= lowestVersion)
    if not lowestVersion <= lowestVersion:
        raise ArithmeticError()

    print "%s == %s = %s" % (lowestVersion, middleVersion, lowestVersion == middleVersion)
    if lowestVersion == middleVersion:
        raise ArithmeticError()

    print "%s == %s = %s" % (lowestVersion, lowestVersion, lowestVersion == lowestVersion)
    if not lowestVersion == lowestVersion:
        raise ArithmeticError()

    print "%s >= %s = %s" % (lowestVersion, middleVersion, lowestVersion >= middleVersion)
    if lowestVersion >= middleVersion:
        raise ArithmeticError()

    print "%s >= %s = %s" % (lowestVersion, lowestVersion, lowestVersion >= lowestVersion)
    if not lowestVersion >= lowestVersion:
        raise ArithmeticError()

    print "%s >  %s = %s" % (lowestVersion, middleVersion, lowestVersion > middleVersion)
    if lowestVersion > middleVersion:
        raise ArithmeticError()

    print "%s != %s = %s" % (lowestVersion, middleVersion, lowestVersion != middleVersion)
    if not lowestVersion != middleVersion:
        raise ArithmeticError()

    print "%s EqualRevisions %s = %s" % (lowestVersion, middleVersion, lowestVersion.EqualRevisions(middleVersion))
    if lowestVersion.EqualRevisions(middleVersion):
        raise ArithmeticError()

    print "%s EqualRevisions %s = %s" % (middleVersion, highestVersion, middleVersion.EqualRevisions(highestVersion))
    if not middleVersion.EqualRevisions(highestVersion):
        raise ArithmeticError()
