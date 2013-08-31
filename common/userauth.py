import MySQLdb
import bcrypt
import hashlib
import uuid
from flask import session, request, jsonify, abort

__all__ = ['gen_session_salt', 'login', 'logout', 'check_auth']

def gen_session_salt():
    session['SESSION_SALT'] = bcrypt.gensalt(8)
    return session['SESSION_SALT']

def login(username, pwhash):
    pass

def logout():
    pass

def check_auth():
    pass

def change_password(username, oldpwhash, newpwhash):
    pass
