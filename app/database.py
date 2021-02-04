import pymysql.cursors

class myMySQL:
    INSERT = {'insert':True}

    def __init__(self, **dns):
        self.dns = dns
        self.dbh = None

    def _open(self):
        self.dbh = pymysql.connect(**self.dns)

    def _close(self):
        self.dbh.close()

    def query(self, stmt, *args, **kwargs):
        self._open()
        with self.dbh.cursor() as cursor:
            cursor.execute(stmt,args)
            result = cursor.fetchall()
        self._close()
        return result

    def insert(self, stmt, *args, **kwargs):
        self._open()
        with self.dbh.cursor() as cursor:
            cursor.execute(stmt, args)
        self.dbh.commit()
        self._close()
