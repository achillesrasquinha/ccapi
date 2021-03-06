# imports - standard imports
import os.path as osp
import sqlite3

# imports - module imports
from ccapi.__attr__     import __name__ as NAME
from ccapi.constant     import PATH
from ccapi.util.string  import strip
from ccapi.util.system  import makedirs, read
from cc                 import config, log

logger = log.get_logger()

IntegrityError      = sqlite3.IntegrityError
OperationalError    = sqlite3.OperationalError

def _get_queries(buffer):
    queries = [ ]
    lines   = buffer.split(";")

    for line in lines:
        line = strip(line)
        queries.append(line)

    return queries

class DB:
    def __init__(self, path, timeout = 10):
        self.path        = path
        self._connection = None
        self.timeout     = timeout

    @property
    def connected(self):
        _connected = bool(self._connection)
        return _connected

    def connect(self, bootstrap = True):
        if not self.connected:
            self._connection = sqlite3.connect(self.path,
                timeout = self.timeout
            )
            self._connection.row_factory = sqlite3.Row

    def query(self, *args, **kwargs):
        if not self.connected:
            self.connect()

        cursor  = self._connection.cursor()
        cursor.execute(*args, **kwargs)
        self._connection.commit()

        results = cursor.fetchall()
        results = [dict(result) for result in results]

        if len(results) == 1:
            results = results[0]

        cursor.close()

        return results

_CONNECTION = None

def get_connection(bootstrap = True):
    global _CONNECTION

    if not _CONNECTION:
        logger.info("Establishing a DataBase connection...")

        basepath    = osp.join(osp.expanduser("~"), ".%s" % NAME)
        makedirs(basepath, exist_ok = True)

        abspath     = osp.join(basepath, "db.db")

        _CONNECTION = DB(abspath)
        _CONNECTION.connect()

        if bootstrap:
            logger.info("Bootstrapping DataBase...")

            abspath = osp.join(PATH["DATA"], "bootstrap.sql")
            buffer  = read(abspath)

            queries = _get_queries(buffer)

            for query in queries:
                _CONNECTION.query(query)

    return _CONNECTION