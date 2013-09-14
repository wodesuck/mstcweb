import bcrypt
import hashlib
import uuid
from flask import session, request, jsonify, abort, g
from common.db import connect_db

__all__ = ['login', 'logout', 'get_salt', 'check_auth', 'change_password']

def login(username, pwhash):
    if 'SESSION_SALT' not in session:
        abort(400)

    if not g.cursor.execute(
            "SELECT `pwhash` FROM `users` WHERE `username` = %s",
            username):
        abort(403)

    if pwhash != bcrypt.hashpw(
            g.cursor.fetchone()[0], session['SESSION_SALT']):
        abort(403)

    token = uuid.uuid4().hex
    g.cursor.execute(
            """UPDATE `users` SET `token` = %s, `client_feature` = %s
            WHERE `username` = %s""",
            (token, _get_client_feature(), username))
    g.conn.commit()

    session['USERNAME'] = username
    session['TOKEN'] = token
    session.pop('SESSION_SALT')

    return True

def change_passwd(old_pwhash, new_pwhash):
    if 'SESSION_SALT' not in session:
        abort(400)

    if not check_auth():
        abort(403)

    g.cursor.execute(
            "SELECT `pwhash` FROM `users` WHERE `username` = %s",
            session['USERNAME'])
    if g.cursor.fetchone()[0] != old_pwhash:
        return False

    g.cursor.execute(
            """UPDATE `users` SET `salt` = %s, `pwhash` = %s, `token` = %s
            WHERE `username` = %s""",
            (session['SESSION_SALT'], new_pwhash, uuid.uuid4().hex,
            session['USERNAME']))
    g.conn.commit()

    session.pop('TOKEN')
    session.pop('SESSION_SALT')
    return True

def logout():
    if check_auth():
        g.cursor.execute(
                "UPDATE `users` SET `token` = %s WHERE `username` = %s",
                (uuid.uuid4().hex, session['USERNAME']))
        g.conn.commit()

        session.pop('TOKEN')
        return True
    else:
        return False

def check_auth():
    if not ('USERNAME' in session and
            'TOKEN' in session):
        return False

    if not g.cursor.execute(
        """SELECT `token`, `client_feature`
        FROM `users` WHERE `username` = %s""",
        session['USERNAME']):
        return False
    token, client_feature = g.cursor.fetchone()

    return (token == session['TOKEN'] and
            client_feature == _get_client_feature())

def _get_client_feature():
    m = hashlib.md5()
    m.update(request.user_agent.string)
    if request.remote_addr is not None:
        m.update(request.remote_addr)
    return m.hexdigest()

def get_salt(username):
    if not g.cursor.execute(
            "SELECT `salt` FROM `users` WHERE `username` = %s", username):
        account_salt = bcrypt.gensalt(8)
    else:
        account_salt = g.cursor.fetchone()[0]

    session['SESSION_SALT'] = bcrypt.gensalt(8)

    return {'account_salt': account_salt,
            'session_salt': session['SESSION_SALT']}

