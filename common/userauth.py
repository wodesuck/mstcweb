import MySQLdb
import bcrypt
import hashlib
import uuid
from flask import session, request, jsonify, abort
from common.db import connect_db

__all__ = ['gen_session_salt', 'login', 'logout', 'check_auth']

def gen_session_salt():
    session['SESSION_SALT'] = bcrypt.gensalt(8)
    return session['SESSION_SALT']

def login(username, pwhash):
    if 'SESSION_SALT' not in session:
        abort(400)

    conn = connect_db()
    cursor = conn.cursor()

    if not cursor.execute(
            "SELECT `pwhash` FROM `users` WHERE `username` = %s", username):
        abort(403)

    if pwhash != bcrypt.hashpw(cursor.fetchone()[0], session['SESSION_SALT']):
        abort(403)

    token = uuid.uuid4().hex
    cursor.execute(
            "UPDATE `users` SET `token` = %s, `client_feature` = %s",
            token, _get_client_feature())

    session['USERNAME'] = username
    session['TOKEN'] = token
    session.pop('SESSION_SALT')

    return jsonify(err_code = 0)

def logout():
    pass

def check_auth():
    pass

def change_password(username, oldpwhash, newpwhash):
    pass

def _get_client_feature():
    m = hashlib.md5()
    m.update(request.user_agent.string)
    m.update(request.remote_addr)
    return m.hexdigest()
