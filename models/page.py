from flask import g
from datetime import datetime
import MySQLdb


class Page(object):
    """
    Page model
    """

    props = ['name', 'title', 'content', 'layout']
    fields = props + ['id', 'created_time', 'updated_time']

    def __init__(self, **kwargs):
        """
        Initialize a Page object.
        Assign object attributes by kwargs.

        name: the page name
        title: the page title
        content: the page content
        layout: the layout used by the page
        """
        self.__dict__ = kwargs

    def is_new(self):
        """
        Recognize whether the page had been inserted into database.
        """
        return not hasattr(self, 'id')

    @classmethod
    def get(cls, name):
        """
        Fetch a Page object from database by given name.
        *This is a class method*

        Raises `NoSuchPage` if such page doesn't exist.
        """
        sql = "SELECT %s FROM pages WHERE name = %%s" % ','.join(cls.fields)
        if not g.cursor.execute(sql, name):
            raise NoSuchPage
        return cls(**dict(zip(cls.fields, g.cursor.fetchone())))

    def save(self):
        """
        Save a Page object to database.

        Raises `PageNameExist` if `name` duplicated when saving a new record.
        """
        if not hasattr(self, 'layout') or not self.layout:
            self.layout = 'default'

        keys = self.props[:]
        values = [getattr(self, x) for x in keys]

        if self.is_new():
            # insert

            # assigning NULL to a NOT NULL TIMESTAMP field
            # it will assign the current timestamp instead
            keys += ['created_time', 'updated_time']
            values += [None, None]

            sql = (u"INSERT INTO pages (%s) VALUES (%s)" %
                   (','.join(keys), ('%s,' * len(keys))[0:-1]))
            try:
                g.cursor.execute(sql, tuple(values))
                self.id = g.cursor.lastrowid
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
            if g.cursor.execute(sql, tuple(values + [self.id])):
                # time maybe not same as db's, ignore...
                self.updated_time = datetime.now()

        g.conn.commit()

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
        g.cursor.execute("DELETE FROM pages WHERE id = %s", self.id)
        g.conn.commit()
        del self.id
        del self.created_time
        del self.updated_time

    @classmethod
    def delete(cls, name):
        """
        Delete a page from database by given name.
        Return the number of pages deleted.
        *This is a class method*
        """
        ret = g.cursor.execute("DELETE FROM pages WHERE name = %s", name)
        g.conn.commit()
        return ret

    @classmethod
    def get_pages_list(cls, items_per_page = 0, page = 0):
        """
        Get a list of the pages.
        Return a list Page objects.
        *This is a class method.*
        """
        sql = """SELECT %s FROM pages
        ORDER BY created_time DESC""" % ', '.join(cls.fields)
        if items_per_page:
            sql += ' LIMIT %d, %d' % (items_per_page * page, items_per_page)
        g.cursor.execute(sql)

        return [Page(**dict(zip(cls.fields, row)))
                for row in g.cursor.fetchall()]


class NoSuchPage(Exception):
    pass


class PageNameExist(Exception):
    pass
