from common.db import connect_db
import MySQLdb
from datetime import datetime


class Page(object):
    """Page model"""

    conn = connect_db()
    cursor = conn.cursor()

    prop = ['id', 'name', 'title', 'content', 'layout',
            'created_time', 'updated_time']

    def __init__(self, **kwargs):
        """
        Initialize a Page object.
        Assign object attribute by kwargs
        """
        self.__dict__ = kwargs

    @classmethod
    def get(cls, name):
        """
        Fetch a Page object from database by given name.
        *This is a class method*

        Raises `NoSuchPage` if such page doesn't exist.
        """
        sql = "SELECT %s FROM pages WHERE name = %%s" % ','.join(cls.prop)
        if not cls.cursor.execute(sql, name):
            raise NoSuchPage
        return cls(**dict(zip(cls.prop, cls.cursor.fetchone())))

    def save(self):
        keys, values = zip(*self.__dict__.items())
        if hasattr(self, 'id'):  # update
            pass  # TODO
        else:  # insert
            keys += ('created_time', 'updated_time')
            values += (None, None)
            sql = ("INSERT INTO pages (%s) VALUES (%s)" %
                   (','.join(keys), ('%s,' * len(keys))[0:-1]))
            try:
                self.cursor.execute(sql, values)
                self.id = self.cursor.lastrowid
                # time maybe not same as db's, ignore...
                self.created_time = self.updated_time = datetime.now()
            except MySQLdb.IntegrityError as err:
                if err[0] == 1062:  # mysql error 1062: Duplicate entry
                    raise PageNameExist
                else:
                    raise err
        self.conn.commit()


class NoSuchPage(Exception):
    pass


class PageNameExist(Exception):
    pass
