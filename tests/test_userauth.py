from nose.tools import (assert_raises, assert_equals,
        assert_is_instance, assert_sequence_equal)
import bcrypt
import json
import uuid
from routes import app
from flask import session
from common.db import connect_db

def setUp():
    conn = connect_db()
    cursor = conn.cursor()

    salt = bcrypt.gensalt(8)
    pwhash = bcrypt.hashpw('test', salt)
    cursor.executemany("""INSERT INTO `users`
        (`username`, `salt`, `pwhash`) VALUES (%s, %s, %s)""",
        [('test', salt, pwhash), ('test2', salt, pwhash)])
    conn.commit()
    conn.close()

    app.testing = True

def teardown():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM `users` WHERE `username` LIKE 'test%'")
    conn.commit()
    conn.close()

def login(test_client, username = 'test', passwd = 'test'):
    respon = test_client.get('/admin/login?username=' + username)
    if respon.status_code != 200:
        return respon
    respon = json.loads(respon.data)

    pwhash = bcrypt.hashpw(passwd, respon['account_salt'])
    pwhash = bcrypt.hashpw(pwhash, respon['session_salt'])

    respon = test_client.post('/admin/login',
            data = {'username': username, 'pwhash': pwhash})
    
    return respon

def test_login():
    with app.test_client() as c:
        respon = login(c)
        assert_equals(respon.status_code, 200)

def test_auth_check():
    with app.test_client() as c:
        respon = c.get('/admin/login/test').data
        assert_equals(respon, '0')

        if login(c).status_code != 200:
            return

        respon = c.get('/admin/login/test').data
        assert_equals(respon, '1')

        with c.session_transaction() as sess:
            sess['TOKEN'] = uuid.uuid4().hex
        respon = c.get('/admin/login/test').data
        assert_equals(respon, '0')

def test_login_failed():
    with app.test_client() as c:
        respon = login(c, 'test', 'wrong_pw')
        assert_equals(respon.status_code, 403)

def test_logout():
    with app.test_client() as c:
        if login(c).status_code != 200:
            return

        c.get('/admin/logout')

        respon = c.get('/admin/login/test').data
        assert_equals(respon, '0')

def test_change_passwd():
    with app.test_client() as c:
        if login(c, username = 'test2').status_code != 200:
            return

        respon = c.get('/admin/login?username=test2')
        respon = json.loads(respon.data)
        oldpwhash = bcrypt.hashpw('test', respon['account_salt'])
        newpwhash = bcrypt.hashpw('newpw', respon['session_salt'])

        respon = c.post('/admin/change_passwd',
                data = {'oldpwhash': oldpwhash, 'newpwhash': newpwhash})

        assert_equals(respon.status_code, 200)
        respon = json.loads(respon.data)
        assert_equals(respon['err_code'], 0)

        assert_equals(login(c, 'test2', 'test').status_code, 403)
        assert_equals(login(c, 'test2', 'newpw').status_code, 200)

def test_change_passwd_error():
    with app.test_client() as c:
        if login(c, username = 'test2').status_code != 200:
            return

        respon = c.get('/admin/login?username=test2')
        respon = json.loads(respon.data)
        oldpwhash = bcrypt.hashpw('wrong_old_pw', respon['account_salt'])
        newpwhash = bcrypt.hashpw('newpw', respon['session_salt'])

        respon = c.post('/admin/change_passwd',
                data = {'oldpwhash': oldpwhash, 'newpwhash': newpwhash})
        respon = json.loads(respon.data)

        assert_equals(respon['err_code'], -1)

        assert_equals(login(c, 'test2', 'newpw').status_code, 403)
        assert_equals(login(c, 'test2', 'test').status_code, 200)
