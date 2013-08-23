from common.db import connect_db


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
        Initialize a Page object by given name.
        Create an empty object if `name` is omitted or None.

        Raises `NoSuchPage` if such page doesn't exist.
        """
        sql = "SELECT %s FROM pages WHERE name = %%s" % ','.join(cls.prop)
        if not cls.cursor.execute(sql, name):
            raise NoSuchPage
        return cls(**dict(zip(cls.prop, cls.cursor.fetchone())))


class NoSuchPage(Exception):
    pass
