from common.db import connect_db
import MySQLdb
from datetime import datetime


class Page(object):
    """Page model"""

    conn = connect_db()
    cursor = conn.cursor()

    props = ['name', 'title', 'content', 'layout']
    fields = props + ['id', 'created_time', 'updated_time']

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
        sql = "SELECT %s FROM pages WHERE name = %%s" % ','.join(cls.fields)
        if not cls.cursor.execute(sql, name):
            raise NoSuchPage
        return cls(**dict(zip(cls.fields, cls.cursor.fetchone())))

    def save(self):
        keys = self.props[:]
        values = [getattr(self, x) for x in keys]
        if hasattr(self, 'id'):
            # update
            sql = ("UPDATE pages SET %s WHERE id = %%s" %
                   ','.join([x + '=%s' for x in keys]))
            self.cursor.execute(sql, tuple(values + [self.id]))
        else:
            # insert
            keys += ['created_time', 'updated_time']
            values += [None, None]
            sql = ("INSERT INTO pages (%s) VALUES (%s)" %
                   (','.join(keys), ('%s,' * len(keys))[0:-1]))
            try:
                self.cursor.execute(sql, tuple(values))
                self.id = self.cursor.lastrowid
                # time maybe not same as db's, ignore...
                self.created_time = datetime.now()
            except MySQLdb.IntegrityError as err:
                if err[0] == 1062:  # mysql error 1062: Duplicate entry
                    raise PageNameExist
                else:
                    raise err

        self.updated_time = datetime.now()
        self.conn.commit()


class NoSuchPage(Exception):
    pass


class PageNameExist(Exception):
    pass
