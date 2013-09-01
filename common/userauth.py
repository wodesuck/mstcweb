import bcrypt
import hashlib
import uuid
from flask import session, request, jsonify, abort, g
from common.db import connect_db

__all__ = ['User']

class User(object):

    def __init__(self, username, pwhash):
        self.username = username
        self.pwhash = pwhash

    def login(self):
        if 'SESSION_SALT' not in session:
            abort(400)

        if not g.cursor.execute(
                "SELECT `pwhash` FROM `users` WHERE `username` = %s",
                self.username):
            abort(403)

        if self.pwhash != bcrypt.hashpw(
                g.cursor.fetchone()[0], session['SESSION_SALT']):
            abort(403)

        token = uuid.uuid4().hex
        g.cursor.execute(
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
        if not ('USERNAME' in session and
                'TOKEN' in session):
            return False

        if g.cursor.execute(
            """SELECT `token`, `client_feature`
            FROM `users` WHERE `username` = %s""",
            session['USERNAME']):
            return False
        token, client_feature = g.cursor.fetchone()

        return (token == session['TOKEN'] and
                client_feature == cls._get_client_feature())

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

