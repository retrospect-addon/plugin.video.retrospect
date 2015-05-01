#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

from sqlite3 import dbapi2 as sqlite

from logger import Logger
from config import Config


# noinspection PyTypeChecker,PyArgumentEqualDefault
class DatabaseHandler:
    """Database handler class. Handles SQLLite database actions"""

    def __init__(self):
        """initialize the DB connection"""

        # SQL lite explorer tool:
        # http://www.sqliteexpert.com/

        # get the user profile folder
        Logger.Info("Opening %s as DB", Config.retroDb)
        self.retroDatabase = sqlite.connect(Config.retroDb)
        self.__CheckDatabaseExistence()
        self.__Encoding = 'utf-8'
        pass

    def __del__(self):
        """ Closes the connection """

        Logger.Info("Closing database connection")
        self.retroDatabase.close()
        pass

    def __CheckDatabaseExistence(self):
        """Checks if the database exists, if not, it will be created."""

        # sql = "PRAGMA table_info('favorites')"
        # results = self.__ExecuteQuery(sql)
        #
        # # check if DB exists
        # if len(results) < 1:
        #     self.__CreateDatabase()
        #     # reload the query
        #     results = self.__ExecuteQuery(sql)
        #
        # # Check for GUID column
        # columnGuidExists = False
        # for result in results:
        #     if result[1] == "guid":
        #         Logger.Debug("Database: Guid column already present in favorites table.")
        #         columnGuidExists = True
        #         break
        # if not columnGuidExists:
        #     Logger.Info("Database: Creating column guid")
        #     sql = "ALTER TABLE favorites ADD COLUMN guid"
        #     self.__ExecuteNonQuery(sql, commit=True)
        return

    #==============================================================================
    def __CreateDatabase(self):
        """Creates a functional database"""

        Logger.Info("Creating Database")
        # sql = 'PRAGMA encoding = "UTF-16"'
        # self.__ExecuteNonQuery(sql, True)
        # sql = "CREATE TABLE favorites (channel string, name string, url string)"
        # self.__ExecuteNonQuery(sql)
        # sql = "CREATE TABLE settings (setting string, value string)"
        # self.__ExecuteNonQuery(sql)

    #==============================================================================
    def __ExecuteNonQuery(self, query, commit=True, params=None):
        """Executes and commits (if true) a sql statement to the database.

        Arguments:
        query  : string - the query to execute

        Keyword Arguments:
        commit : boolean        - indicates whether the transaction should be
                                  committed or not.
        params : tupple(string) - the parameters to substitute into the query

        Returns nothing, as it does not expect any results

        """

        if params is None:
            params = []

        # decode to unicode
        uParams = []
        for param in params:
            uParams.append(param.decode(self.__Encoding))

        cursor = self.retroDatabase.cursor()
        if len(params) > 0:
            cursor.execute(query, uParams)
        else:
            cursor.execute(query)

        if commit:
            self.retroDatabase.commit()

        cursor.close()

    def __ExecuteQuery(self, query, commit=False, params=None):
        """Executs and commits (if true) a sql statement to the database.

        Arguments:
        query  : string - the query to execute

        Keyword Arguments:
        commit : boolean        - indicates whether the transaction should be
                                  committed or not.
        params : tupple(string) - the parameters to substitute into the query

        Returns a row-set.

        """

        if params is None:
            params = []

        # decode to unicode
        uParams = []
        for param in params:
            # uParams.append(param.decode('iso-8859-1'))
            uParams.append(param.decode(self.__Encoding))

        cursor = self.retroDatabase.cursor()
        if len(params) > 0:
            cursor.execute(query, uParams)
        else:
            cursor.execute(query)

        if commit:
            self.retroDatabase.commit()

        results = cursor.fetchall()
        cursor.close()

        return results
