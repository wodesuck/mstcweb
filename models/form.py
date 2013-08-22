import json, datetime, re
import MySQLdb
from common.db import connect_db

__all__ = ['Form', 'FormData', 'FieldDescription',
'InvalidSubmit', 'NameExisted', 'NoSuchForm', 'NoSuchName',
'NotStartYet', 'Ended']

class Form(object):
    conn = connect_db()
    cursor = conn.cursor()

    def __init__(self, name = None):
        """
        Initialize a model object by the given event name.
        Create an empty model object if `name` is omitted or None.
        
        Raises `NoSuchName` if there doesn't exist such an event.
        """
        if name is not None:
            #self.conn = connect_db()
            #self.cursor = self.conn.cursor()

            if not self.cursor.execute(
                    """SELECT `id`, `name`, `content_fields`, `start_time`,
                    `end_time`, `created_time` FROM `events`
                    WHERE `name` = %s""", name):
                raise NoSuchForm

            (self.id, self.name, self.content_fields, self.start_time,
                    self.end_time, self.created_time) = self.cursor.fetchone()
            self.content_fields = map(
                    lambda x: FieldDescription(**x),
                    json.loads(self.content_fields))

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
        
        matchName = re.match('[\u4e00-\u9fa5]{2,4}', name)
        matchEmail = re.match('\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*', email)

        validContent = True
        for field in self.content_fields:
            contentType = field.field_type
            value = content[field.column_name]
            if contentType == 'input' or contentType == 'textarea':
                if len(value) < field.min_len or len(value) > field.max_len:
                    validContent = False
            elif contentType == 'number':
                if value < field.min_val or value > field.max_val:
                    validContent = False

        if matchName == None or matchEmail == None or validContent == False:
            raise InvalidSubmit

        submitTime = datetime.today()
        if submitTime < self.start_time:
            raise NotStartYet
        if submitTime > self.end_time:
            raise Ended

        self.cursor.execute(
				"INSERT INTO forms_data (event_id, name, email, content) VALUES (%d, '%s', '%s', '%s')",
				self.id, name, email, json.dumps(content))

    def query(self, items_per_page = 0, page = 0, status = None):
        """
        Query the application forms of the event.
        Data are filtered by `status` if it is not None.

        Returns a list containing the application forms.
        Each form is presented as an instance of `FormData`.
        """
        sql = """SELECT `id`, `event_id`,
        `name`, `email`, `content`, `status`, `created_time`
        FROM `forms_data`"""
        if status is not None:
            sql += " WHERE `status` = %s" % MySQLdb.string_literal(status)
        if items_per_page:
            sql += ' LIMIT %d, %d' % (items_per_page * page, items_per_page)

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
    def create_event(cls, name, content_fields, start_time, end_time):
        """
        Create an event and create an model object for the
        new event.
        *This is a class method.*

        Raises `NameExisted` if the name has already existed.

        `start_time` and `end_time` are `datetime.datetime` objects.
        """
        pass

    @classmethod
    def delete_event(cls, event_id = None, name = None):
        """
        Delete an event with the given event id or name.
        Either `event_id` or `name` must be specified.
        *This is a class method.*
        """
        pass

    @classmethod
    def change_form_status(cls, form_id, new_status):
        """
        Change the status of a specified application form.

        Raises `NoSuchForm` if there doesn't exist such an application form.
        *This is a class method.*
        """
        pass


class FormData(object):
    def __init__(self,
            form_id, event_id, name, email, content, status, created_time):
        self.form_id = form_id
        self.event_id = event_id
        self.name = name
        self.email = email
        if isinstance(content, str):
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
    def __init__(self, column_name, field_type = 'input',
            min_len = 0, max_len = 65536,
            min_val = -65535, max_val = 65535):
        self.column_name = column_name
        self.field_type = field_type
        self.min_len = min_len
        self.max_len = max_len
        self.min_val = min_val
        self.max_val = max_val

    def to_json(self):
        if self.field_type == 'input' or self.field_type == 'textarea':
            return json.dumps({
                'column_name': self.column_name,
                'field_type': self.field_type,
                'min_len': self.min_len,
                'max_len': self.max_len})
        elif self.field_type == 'number':
            return json.dumps({
                'column_name': self.column_name,
                'field_type': 'number',
                'min_val': self.min_val,
                'max_val': self.max_val})
        else: 
            return json.dumps({
                'column_name': self.column_name,
                'field_type': 'bool'})


class NoSuchForm(Exception):
    pass

class NoSuchName(Exception):
    pass

class NameExisted(Exception):
    pass

class InvalidSubmit(Exception):
    pass

class NotStartYet(Exception):
    pass

class Ended(Exception):
    pass
