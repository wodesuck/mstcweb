# -*- coding: utf8 -*-
from nose.tools import (assert_raises, assert_equals,
        assert_is_instance, assert_sequence_equal)
import datetime
import MySQLdb
import json

import routes
ctx = routes.app.app_context()
ctx.push()

routes.init()
from flask import g
from models import form

conn = g.conn
cursor = g.cursor

now = datetime.datetime.now()
timeDelta = datetime.timedelta(minutes = 10)

formFields = []
formFields.append(form.FieldDescription(u'短文本(4 - 10)', 'input', 4, 10))
formFields.append(form.FieldDescription(u'长文本', 'textarea'))
formFields.append(form.FieldDescription(u'数字(-10 - 10)', 'number', min_val = -10, max_val = 10))
formFields.append(form.FieldDescription(u'布尔', 'bool'))

validSubmitContent = [u'短文本内容', u'长文本内容', 5, True]

content_fields_str = json.dumps(map(lambda x: x.to_dict(), formFields))
before = (now - timeDelta).strftime('%Y-%m-%d %H:%M:%S')
after = (now + timeDelta).strftime('%Y-%m-%d %H:%M:%S')

cursor.executemany(
        """INSERT INTO events
        (name, content_fields, start_time, end_time)
        VALUES (%s, %s, %s, %s)""", [
            ('test0', '[]', 0, 0),
            ('test1', '[]', 0, 0),
            ('testQueryForm', '[]', 0, 0),
            ('testDeleteEvent', '[]', 0, 0),
            ('testForm', content_fields_str, before, after),
            ('testFormNotStarted', content_fields_str, after, after),
            ('testFormEnded', content_fields_str, before, before)
            ]
        )
conn.commit()

cursor.execute("SELECT id FROM events WHERE name = 'testDeleteEvent'")
deleteEventId = cursor.fetchone()[0]

cursor.execute("SELECT id FROM events WHERE name = 'testQueryForm'")
testQueryId = cursor.fetchone()[0]

def insert_form(x):
    cursor.execute(
            """INSERT INTO forms_data
            (event_id, name, email, content, status)
            VALUES (%s, %s, %s, %s, %s)""", x)
    return cursor.lastrowid

changeStatueFormId = insert_form((0, u'测试', 'xxx@xxx.com', '[]', 0))
deleteFormId = insert_form((0, u'测试', 'xxx@xxx.com', '[]', 0))

queryFormIds = map(
        lambda i: insert_form(
            (testQueryId, u'测试', 'xxx@xxx.com', '[]', i)),
        [1, 1, 0, 0, 0])

conn.commit()

def teardown():
    cursor.execute("DELETE FROM events WHERE name LIKE 'test%'")
    cursor.execute(u"DELETE FROM forms_data WHERE name LIKE '测试%'")
    conn.commit()
    routes.teardown()
    ctx.pop()

def testGetEvent():
    eventObj = form.Event.get('test0')
    assert_equals(eventObj.name, 'test0')

def testNewEvent():
    eventObj = form.Event(
            name = 'testNewEvent',
            content_fields = formFields,
            start_time = now - timeDelta,
            end_time = now + timeDelta)
    eventObj.save()

    assert hasattr(eventObj, 'id')

def testNewEventError():
    eventObj = form.Event(
            name = 'test0',
            content_fields = formFields,
            start_time = now - timeDelta,
            end_time = now + timeDelta)
    assert_raises(form.NameExisted, eventObj.save)

def testEditEvent():
    eventObj = form.Event.get('test0')
    eventObj.start_time = now
    eventObj.end_time = now
    eventObj.save()

    assert_equals(form.Event.get('test0').start_time.ctime(), now.ctime())

def testDeleteEventByName():
    form.Event.delete_event(name = 'test1')

    cursor.execute("SELECT COUNT(*) FROM `events` WHERE `name` = 'test1'")
    assert_equals(cursor.fetchone()[0], 0)

def testDeleteEventById():
    form.Event.delete_event(event_id = deleteEventId)

    cursor.execute(
            "SELECT COUNT(*) FROM `events` WHERE `id` = %s", deleteEventId)
    assert_equals(cursor.fetchone()[0], 0)

def testSubmitForm():
    eventObj = form.Event.get('testForm')
    assert_is_instance(
            eventObj.submit(
                u'测试',
                'abc.def+ghi@mail2.sysu.edu.cn',
                validSubmitContent),
            long)

def testSubmitFormInvalidEmail():
    eventObj = form.Event.get('testForm')
    assert_raises(form.InvalidSubmit, eventObj.submit,
            u'测试', 'abc.def+ghi#mail2.sysu.edu.cn', validSubmitContent)

def testSubmitFormInvalidTextLength():
    eventObj = form.Event.get('testForm')
    assert_raises(form.InvalidSubmit, eventObj.submit,
            u'测试', 'abc.def+ghi@mail2.sysu.edu.cn',
            [u'过短', u'长文本内容', 5, True])
    assert_raises(form.InvalidSubmit, eventObj.submit,
            u'测试', 'abc.def+ghi@mail2.sysu.edu.cn',
            [u'过长过长过长过长过长过长', u'长文本内容', 5, True])

def testSubmitFormInvalidNumber():
    eventObj = form.Event.get('testForm')
    assert_raises(form.InvalidSubmit, eventObj.submit,
            u'测试', 'abc.def+ghi@mail2.sysu.edu.cn',
            [u'短文本内容', u'长文本内容', -20, True])

def testSubmitFormNotStarted():
    eventObj = form.Event.get('testFormNotStarted')
    assert_raises(form.NotStartYet, eventObj.submit,
            u'测试', 'abc.def+ghi@mail2.sysu.edu.cn', validSubmitContent)

def testSubmitFormEnded():
    eventObj = form.Event.get('testFormEnded')
    assert_raises(form.Ended, eventObj.submit,
            u'测试', 'abc.def+ghi@mail2.sysu.edu.cn', validSubmitContent)

def testChangeFormStatus():
    form.Event.change_form_status(changeStatueFormId, 1)

    cursor.execute("SELECT `status` FROM `forms_data` WHERE `id` = %s",
            changeStatueFormId)
    assert_equals(cursor.fetchone()[0], 1)

def testDeleteForm():
    form.Event.delete_form(deleteFormId)

    cursor.execute("SELECT COUNT(*) FROM `forms_data` WHERE `id` = %s",
            deleteFormId)
    assert_equals(cursor.fetchone()[0], 0)

def testQueryForm():
    eventObj = form.Event.get('testQueryForm')

    ids = map(lambda x: x.form_id, eventObj.query())
    assert_sequence_equal(ids, queryFormIds)

    ids = map(lambda x: x.form_id, eventObj.query(2, 1))
    assert_sequence_equal(ids, queryFormIds[2:4])

    ids = map(lambda x: x.form_id, eventObj.query(status = 1))
    assert_sequence_equal(ids, queryFormIds[0:2])

def testQueryOneForm():
    assert_equals(queryFormIds[0],
            form.Event.query_one(queryFormIds[0]).form_id)
