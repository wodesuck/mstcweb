import MySQLdb
import json, re
from datetime import datetime
from common.db import connect_db

__all__ = ['Event', 'FormData', 'FieldDescription',
'InvalidSubmit', 'NameExisted', 'NoSuchForm', 'NoSuchName',
'NotStartYet', 'Ended']

class Event(object):
    conn = connect_db()
    cursor = conn.cursor()

    def __init__(self, **kwargs):
        """
        Initialize a form model object according to the keyword arguments.
        The keyword arguments should contain the following keys.

        name: the event name
        content_fields: a list of FieldDescription objects
        start_time: the start time of the event
        end_time: the end time of the event
        """
        self.__dict__ = kwargs

    def save(self):
        """
        Save a new event
        """
        keys = ['name', 'content_fields', 'start_time', 'end_time']
        values = [self.name,
                json.dumps(map(lambda x: x.to_dict(), self.content_fields)),
                self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                self.end_time.strftime('%Y-%m-%d %H:%M:%S')]
		
        if hasattr(self, 'id'):
            #update
            sql = """UPDATE events SET
            name=%s, content_fields=%s, start_time=%s, end_time=%s WHERE id = %s""" 
            self.cursor.execute(sql, tuple(values + [self.id]))

        else:
            #insert
            sql = """INSERT INTO events (name, content_fields, start_time, end_time)
            VALUES (%s, %s, %s, %s)"""

            try:
                self.cursor.execute(sql, tuple(values))
                self.id = self.cursor.lastrowid
                self.created_time = datetime.now()
            except MySQLdb.IntegrityError as err:
                if err[0] == 1062:
                    raise NameExisted
                else:
                    raise err

        self.conn.commit()

    def submit(self, name, email, content):
        """
        Submit an application form to the event.

        Raises `InvalidSubmit` if the submited data are invalid
        or the model object is not initialized as an existing
        event.
        Raises `NotStartYet` if the event has not started yet.
        Raises `Ended` if the event has ended already.

        Returns the id of the new application form.
        """
        if not self.id:
            raise InvalidSubmit
        
        matchName = re.match(u'[\u4e00-\u9fa5]{2,4}', name)
        matchEmail = re.match(
                '\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*', email)

        if matchName is None or matchEmail is None:
            raise InvalidSubmit

        validContent = True
        for field, value in zip(self.content_fields, content):
            contentType = field.field_type

            if contentType in ['input', 'textarea']:
                validContent = field.min_len <= len(value) <= field.max_len
            elif contentType == 'number':
                validContent = field.min_val <= value <= field.max_val

            if not validContent:
                raise InvalidSubmit

        submitTime = datetime.now()
        if submitTime < self.start_time:
            raise NotStartYet
        if submitTime > self.end_time:
            raise Ended

        self.cursor.execute(
                """INSERT INTO `forms_data`
                (`event_id`, `name`, `email`, `content`)
                VALUES (%s, %s, %s, %s)""",
                (self.id, name, email, json.dumps(zip(
                    map(lambda x: x.field_name, self.content_fields),
                        content))))
        self.conn.commit()
        return self.cursor.lastrowid

    def query(self, items_per_page = 0, page = 0, status = None):
        """
        Query the application forms of the event.
        Data are filtered by `status` if it is not None.

        Returns a list containing the application forms.
        Each form is presented as an instance of `FormData`.
        """
        sql = """SELECT `id`, `event_id`,
        `name`, `email`, `content`, `status`, `created_time`
        FROM `forms_data` WHERE `event_id` = %d""" % self.id
        if status is not None:
            sql += " AND `status` = %s" % MySQLdb.string_literal(status)
        if items_per_page:
            sql += " LIMIT %d, %d" % (items_per_page * page, items_per_page)

        self.cursor.execute(sql)
        return map(lambda row: FormData(*row), self.cursor.fetchall())

    @classmethod
    def query_one(cls, form_id):
        """
        Query one application forms by the form id.
        *This is a class method.*

        Raises `NoSuchForm` if there doesn't exist such an application form.
        """
        sql = """SELECT `id`, `event_id`,
        `name`, `email`, `content`, `status`, `created_time`
        FROM `forms_data` WHERE `id` = %s"""

        if not cls.cursor.execute(sql, form_id):
            raise NoSuchForm

        return FormData(*cls.cursor.fetchone())

    @classmethod
    def get(cls, name):
        """
        Fetch data from database then create a form model object according to
        the event name.
        *This is a class method.*

        Raises `NoSuchForm` if such a form doesn't exist.
        """
        fields_name = ['id', 'name', 'content_fields',
                'start_time', 'end_time', 'created_time']

        sql = "SELECT %s FROM `events` WHERE `name` = %s" % (
                ', '.join(fields_name), MySQLdb.string_literal(name))
        if not cls.cursor.execute(sql):
            raise NoSuchEvent

        result = dict(zip(fields_name, cls.cursor.fetchone()))
        result['content_fields'] = map(
                lambda x: FieldDescription(**x),
                json.loads(result['content_fields']))

        return cls(**result)

    @classmethod
    def delete_event(cls, event_id = None, name = None):
        """
        Delete the event with the given event id or name.
        Either `event_id` or `name` must be specified.
        *This is a class method.*
        """
        if event_id is not None:
            sql = "DELETE FROM `events` WHERE `id` = %s"
            cls.cursor.execute(sql, event_id)
        elif name is not None:
            sql = "DELETE FROM `events` WHERE `name` = %s"
            cls.cursor.execute(sql, name)
        else:
            raise TypeError('Either `event_id` or `name` must be specified')
        cls.conn.commit()

    @classmethod
    def delete_form(cls, form_id):
        """
        Delete the form with the given form id.
        *This is a class method.*
        """
        cls.cursor.execute("DELETE FROM `forms_data` WHERE `id` = %s", form_id)
        cls.conn.commit()

    @classmethod
    def change_form_status(cls, form_id, new_status):
        """
        Change the status of a specified application form.

        Raises `NoSuchForm` if there doesn't exist such an application form.
        *This is a class method.*
        """
        if not cls.cursor.execute(
                "UPDATE `forms_data` SET `status` = %s WHERE `id` = %s",
                (new_status, form_id)):
            raise NoSuchForm
        cls.conn.commit()


class FormData(object):
    def __init__(self,
            form_id, event_id, name, email, content, status, created_time):
        self.form_id = form_id
        self.event_id = event_id
        self.name = name
        self.email = email
        if not isinstance(content, list):
            self.content = json.loads(content)
        else:
            self.content = content
        self.status = status
        self.created_time = created_time


class FieldDescription(object):
    """
    A class for defining a data field of a form content.

    The argument `field_type` can be
    'input': short text with the length between min_len and max_len
    'textarea': long text with the length between min_len and max_len
    'number': number between min_val and max_val
    'bool': boolean value.
    """
    def __init__(self, field_name, field_type = 'input',
            min_len = 0, max_len = 65536,
            min_val = -65535, max_val = 65535):
        self.field_name = field_name
        self.field_type = field_type
        self.min_len = min_len
        self.max_len = max_len
        self.min_val = min_val
        self.max_val = max_val

    def to_dict(self):
        if self.field_type == 'input' or self.field_type == 'textarea':
            return {
                'field_name': self.field_name,
                'field_type': self.field_type,
                'min_len': self.min_len,
                'max_len': self.max_len}
        elif self.field_type == 'number':
            return {
                'field_name': self.field_name,
                'field_type': 'number',
                'min_val': self.min_val,
                'max_val': self.max_val}
        else: 
            return {
                'field_name': self.field_name,
                'field_type': 'bool'}


class NoSuchForm(Exception):
    pass

class NoSuchEvent(Exception):
    pass

class NameExisted(Exception):
    pass

class InvalidSubmit(Exception):
    pass

class NotStartYet(Exception):
    pass

class Ended(Exception):
    pass
