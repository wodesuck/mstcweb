from common.db import connect_db
import MySQLdb
from datetime import datetime


class Page(object):
    """
    Page model
    """

    conn = connect_db()
    cursor = conn.cursor()

    props = ['name', 'title', 'content', 'layout']
    fields = props + ['id', 'created_time', 'updated_time']

    def __init__(self, **kwargs):
        """
        Initialize a Page object.
        Assign object attributes by kwargs.
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
        """
        Save a Page object to database.

        Raises `PageNameExist` if `name` duplicated when saving a new record.
        """
        keys = self.props[:]
        values = [getattr(self, x) for x in keys]

        if self.is_new():
            # insert

            # assigning NULL to a NOT NULL TIMESTAMP field
            # it will assign the current timestamp instead
            keys += ['created_time', 'updated_time']
            values += [None, None]

            sql = ("INSERT INTO pages (%s) VALUES (%s)" %
                   (','.join(keys), ('%s,' * len(keys))[0:-1]))
            try:
                self.cursor.execute(sql, tuple(values))
                self.id = self.cursor.lastrowid
                # time maybe not same as db's, ignore...
                self.created_time = self.updated_time = datetime.now()
            except MySQLdb.IntegrityError as err:
                if err[0] == 1062:  # mysql error 1062: Duplicate entry
                    raise PageNameExist
                else:
                    raise err
        else:
            # update
            sql = ("UPDATE pages SET %s WHERE id = %%s" %
                   ','.join([x + '=%s' for x in keys]))
            if self.cursor.execute(sql, tuple(values + [self.id])):
                # time maybe not same as db's, ignore...
                self.updated_time = datetime.now()

        self.conn.commit()

    def is_new(self):
        return not hasattr(self, 'id')

    @classmethod
    def create(cls, **kwargs):
        """
        Initialize a Page object and save it to database.
        Return the new object.
        Assign object attributes by kwargs.
        *this is a class method*

        Raises `PageNameExist` if `name` duplicated.
        """
        obj = cls(**kwargs)
        obj.save()
        return obj

    def update(self, **kwargs):
        """
        Modify a Page object and save it to database.
        Assign object attributes by kwargs.
        """
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
        self.save()

    def destroy(self):
        """
        Delete the page.
        """
        self.cursor.execute("DELETE FROM pages WHERE id = %s", self.id)
        self.conn.commit()
        del self.id
        del self.created_time
        del self.updated_time


class NoSuchPage(Exception):
    pass


class PageNameExist(Exception):
    pass
