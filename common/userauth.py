import MySQLdb
import bcrypt
import hashlib
import uuid
from flask import session, request, jsonify, abort

__all__ = ['login', 'logout', 'check_auth']

def login(username, pwhash):
    pass

def logout():
    pass

def check_auth():
    pass

def change_password(username, oldpwhash, newpwhash):
    pass
