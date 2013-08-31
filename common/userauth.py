import MySQLdb
import bcrypt
import hashlib
import uuid
from flask import session, request, jsonify, abort
from common.db import connect_db

__all__ = ['User']

class User(object):

    conn = connect_db()
    cursor = conn.cursor()

    def __init__(self, username, pwhash):
        self.username = username
        self.pwhash = pwhash

    def login(self):
        if 'SESSION_SALT' not in session:
            abort(400)

        if not self.cursor.execute(
                "SELECT `pwhash` FROM `users` WHERE `username` = %s",
                self.username):
            abort(403)

        if self.pwhash != bcrypt.hashpw(
                self.cursor.fetchone()[0], session['SESSION_SALT']):
            abort(403)

        token = uuid.uuid4().hex
        self.cursor.execute(
                "UPDATE `users` SET `token` = %s, `client_feature` = %s",
                token, _get_client_feature())

        session['USERNAME'] = self.username
        session['TOKEN'] = token
        session.pop('SESSION_SALT')

        return jsonify(err_code = 0)

    def change_password(self, old_pwhash, new_pwhash):
        pass

    @classmethod
    def logout(cls):
        pass

    @classmethod
    def check_auth(cls):
        pass

    @staticmethod
    def _get_client_feature():
        m = hashlib.md5()
        m.update(request.user_agent.string)
        m.update(request.remote_addr)
        return m.hexdigest()

    @staticmethod
    def gen_session_salt():
        session['SESSION_SALT'] = bcrypt.gensalt(8)
        return session['SESSION_SALT']

