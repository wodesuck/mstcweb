# -*- coding: utf8 -*-
from nose.tools import (assert_raises, assert_equals,
        assert_is_instance, assert_sequence_equal, assert_items_equal)
import datetime
import MySQLdb
import json

import routes
from flask import g
from models import form

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

def setUp():
    routes.app.testing = True
    global ctx
    ctx = routes.app.app_context()
    ctx.push()
    routes.init_db()

    g.cursor.executemany(
            """INSERT INTO events
            (name, content_fields, start_time, end_time)
            VALUES (%s, %s, %s, %s)""", [
                ('test0', '[]', 0, 0),
                ('test1', '[]', 0, 0),
                ('testQueryForm', '[]', 0, 0),
                ('testDeleteEvent', '[]', 0, 0),
                ('testForm', content_fields_str, before, after),
                ('testFormNotStarted', content_fields_str, after, after),
                ('testFormEnded', content_fields_str, before, before),
                ('testEventsList0', '[]', after, after),
                ('testEventsList1', '[]', before, after),
                ('testEventsList2', '[]', before, before),
                ]
            )

    g.cursor.executemany(
            """INSERT INTO pages
            (name, title, content, layout)
            VALUES (%s, %s, %s, %s)""", [
                ('testEventsList0', '', '', ''),
                ('testEventsList1', '', '', ''),
                ('testEventsList2', '', '', ''),
                ('testEventsListNot', '', '', ''),
                ]
            )

    g.cursor.execute("SELECT id FROM events WHERE name = 'testDeleteEvent'")
    global deleteEventId
    deleteEventId = g.cursor.fetchone()[0]

    g.cursor.execute("SELECT id FROM events WHERE name = 'testQueryForm'")
    global testQueryId
    testQueryId = g.cursor.fetchone()[0]

    global changeStatusFormId
    changeStatusFormId = insert_form((0, u'测试', 'xxx@xxx.com', '[]', 0))
    global deleteFormId
    deleteFormId = insert_form((0, u'测试', 'xxx@xxx.com', '[]', 0))

    global queryFormIds
    queryFormIds = map(
            lambda i: insert_form(
                (testQueryId, u'测试', 'xxx@xxx.com', '[]', i)),
            [1, 1, 0, 0, 0])

    g.conn.commit()

def insert_form(x):
    g.cursor.execute(
            """INSERT INTO forms_data
            (event_id, name, email, content, status)
            VALUES (%s, %s, %s, %s, %s)""", x)
    return g.cursor.lastrowid

def teardown():
    g.cursor.execute("DELETE FROM events WHERE name LIKE 'test%'")
    g.cursor.execute("DELETE FROM pages WHERE name LIKE 'test%'")
    g.cursor.execute(u"DELETE FROM forms_data WHERE name LIKE '测试%'")
    g.conn.commit()
    routes.teardown(None)
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

    g.cursor.execute("SELECT COUNT(*) FROM `events` WHERE `name` = 'test1'")
    assert_equals(g.cursor.fetchone()[0], 0)

def testDeleteEventById():
    form.Event.delete_event(event_id = deleteEventId)

    g.cursor.execute(
            "SELECT COUNT(*) FROM `events` WHERE `id` = %s", deleteEventId)
    assert_equals(g.cursor.fetchone()[0], 0)

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
    form.Event.change_form_status(changeStatusFormId, 1)

    g.cursor.execute("SELECT `status` FROM `forms_data` WHERE `id` = %s",
            changeStatusFormId)
    assert_equals(g.cursor.fetchone()[0], 1)

def testDeleteForm():
    form.Event.delete_form(deleteFormId)

    g.cursor.execute("SELECT COUNT(*) FROM `forms_data` WHERE `id` = %s",
            deleteFormId)
    assert_equals(g.cursor.fetchone()[0], 0)

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

def testEventsList():
    assert_sequence_equal(
            map(lambda x: (x['name'], x['status']), form.Event.get_events_list()),
            [('testEventsList2', 1), ('testEventsList1', 0),
                ('testEventsList0', -1)])

    assert_sequence_equal(
            map(lambda x: x['name'], form.Event.get_events_list(2, 1)),
            ['testEventsList0'])
