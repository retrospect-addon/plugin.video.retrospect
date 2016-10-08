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

    def __init__(self, version=None, major=None, minor=None, build=None, revision=None, buildType=None):
        """ Initialises a new version number

        Keyword arguments:
        version  : String  - Version string
        major    : Integer - The Major build number
        minor    : Integer - The Minor build number
        revision : Integer - The Revision number
        build    : Integer - The Build number
        buildType: String  - None, Alpha, Beta etc

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
        if buildType is not None:
            self.buildType = buildType.lower()
        else:
            self.buildType = None

        if version:
            self.__ExtractVersion(version)

    def EqualBuilds(self, other):
        """ Checks if two versions have the same version up until the revision 
        part of the version 
        
        Arguments:
        other : Version - The version to compare with.
        
        Returns:
        True or False
        
        """

        if other is None:
            return False

        # thisVersion = Version(major=self.major, minor=self.minor, revision=self.build)
        # otherVersion = Version(major=other.major, minor=other.minor, revision=other.build)
        return self.major == other.major and self.minor == other.minor and self.build == other.build

    def __ExtractVersion(self, version):
        """ Extracts the Major, Minor, Revision and Buildnumber from a version string
        
        Arguments:
        version : String - The version string
        
        """

        if "~" in version:
            version, self.buildType = version.split("~")

        split = str(version).split('.')
        if len(split) > 0:
            self.major = int(split[0])
        if len(split) > 1:
            self.minor = int(split[1])
        if len(split) > 2:
            self.build = int(split[2])
        if len(split) > 3:
            self.revision = int(split[3])

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

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        """ String representation """

        if self.major is None:
            return "None"

        if self.buildType:
            if self.minor is None:
                return "%s~%s" % (self.major, self.buildType)
            elif self.build is None:
                return "%s.%s~%s" % (self.major, self.minor, self.buildType)
            elif self.revision is None:
                return "%s.%s.%s~%s" % (self.major, self.minor, self.build, self.buildType)
            else:
                return "%s.%s.%s.%s~%s" % (self.major, self.minor, self.build, self.revision, self.buildType)
        else:
            if self.minor is None:
                return str(self.major)
            elif self.revision is None:
                return "%s.%s" % (self.major, self.minor)
            elif self.revision is None:
                return "%s.%s.%s" % (self.major, self.minor, self.build)
            else:
                return "%s.%s.%s.%s" % (self.major, self.minor, self.build, self.revision)

    def __lt__(self, other):
        """ Tests two versios for 'Lower Then' 
        
        Arguments:
        other : Version - The version to compare with.
        
        Returns:
        True or False

        """

        versionTypes = ["alpha", "beta"]

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
        if not self.__NoneIsZero(self.build) == self.__NoneIsZero(other.build):
            return self.__NoneIsZero(self.build) < self.__NoneIsZero(other.build)

        if self.buildType is None and other.buildType is None:
            # they are the same
            return False

        if self.buildType is None and other.buildType is not None:
            # one has beta/alpha, the other None, so the other is larger
            return False

        if self.buildType is not None and other.buildType is None:
            return True

        # we have 2 build types
        selfBuildName = self.buildType.rstrip("0123456789")
        selfBuildNameNumber = self.buildType.lstrip("".join(versionTypes))
        otherBuildName = other.buildType.rstrip("0123456789")
        otherBuildNameNumber = other.buildType.lstrip("".join(versionTypes))

        if selfBuildName == otherBuildName:
            return selfBuildNameNumber < otherBuildNameNumber

        return versionTypes.index(selfBuildName) < versionTypes.index(otherBuildName)
