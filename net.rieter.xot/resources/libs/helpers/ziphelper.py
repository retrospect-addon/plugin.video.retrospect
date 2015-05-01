#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
import os
import shutil
import zipfile

from logger import Logger


class ZipHelper:
    def __init__(self):
        pass

    @staticmethod
    def Unzip(path, destination):
        """ Unzips a file <path> to the folder <destination>

        @param path:        The path to the zipfile
        @param destination: The folder ot extract to

        """

        zipFile = None
        try:
            zipFile = zipfile.ZipFile(path)

            # now extract
            first = True
            Logger.Debug("Extracting %s to %s", path, destination)
            for name in zipFile.namelist():
                if first:
                    folder = os.path.split(name)[0]
                    if os.path.exists(os.path.join(destination, folder)):
                        shutil.rmtree(os.path.join(destination, folder))
                    first = False

                if not name.endswith("/") and not name.endswith("\\"):
                    fileName = os.path.join(destination, name)
                    path = os.path.dirname(fileName)
                    if not os.path.exists(path):
                        os.makedirs(path)
                    Logger.Debug("Extracting %s", fileName)
                    outfile = open(fileName, 'wb')
                    outfile.write(zipFile.read(name))
                    outfile.close()
        except zipfile.BadZipfile:
            Logger.Error("Invalid zipfile: %s", path, exc_info=True)
            if os.path.isfile(path):
                os.remove(path)
        except:
            Logger.Error("Error extracting file: %s", path, exc_info=True)
        finally:
            if zipFile:
                Logger.Debug("Closing zipfile: %s", path)
                zipFile.close()
