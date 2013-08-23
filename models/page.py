from common.db import connect_db


class Page(object):
    """Page model"""

    conn = connect_db()
    cursor = conn.cursor()

    prop = ['id', 'name', 'title', 'content', 'layout',
            'created_time', 'updated_time']

    def __init__(self, name=None):
        """
        Initialize a Page object by given name.
        Create an empty object if `name` is omitted or None.

        Raises `NoSuchPage` if such page doesn't exist.
        """
        if name is not None:
            sql = "SELECT %s FROM pages WHERE name = \%s" % ','.join(self.prop)
            if not self.cursor.execute(sql, name):
                raise NoSuchPage
            self.__dict__ = dict(zip(self.prop, self.cursor.fetchone()))


class NoSuchPage(Exception):
    pass
