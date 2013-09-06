from flask import Flask, g, session
import uuid
import MySQLdb
from functools import wraps
from common.db import connect_db
from common.config import SESSION_KEY

app = Flask(__name__, template_folder = '../layouts')
app.secret_key = SESSION_KEY

@app.before_request
def init():
    g.conn = connect_db()
    g.cursor = g.conn.cursor()

@app.teardown_request
def teardown(e):
    if hasattr(g, 'conn'):
        g.conn.close()

def gen_csrf_token(refresh = False):
    if refresh or 'CSRF_TOKEN' not in session:
        session['CSRF_TOKEN'] = uuid.uuid4().hex
    return session['CSRF_TOKEN']

app.jinja_env.globals['CSRF_TOKEN'] = gen_csrf_token

def _build_csrf_white_list():
    white_list = set()

    def decorator(func):
        white_list.add(func.__name__)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return white_list, decorator

csrf_white_list, disable_csrf_protection = _build_csrf_white_list()

import routes.userauth
import routes.pages
import routes.forms
