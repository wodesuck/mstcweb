from flask import Flask, g, session, request, abort, render_template
import uuid
import MySQLdb
from functools import wraps
from common.db import connect_db
from common.config import SESSION_KEY
from common.userauth import check_auth

app = Flask(__name__,
        template_folder = '../layouts',
        static_folder = '../static')
app.secret_key = SESSION_KEY

@app.before_request
def init():
    init_db()

    if (request.method in ['POST', 'PUT'] and
            request.endpoint not in csrf_white_list):
        s_token = session.pop('CSRF_TOKEN', None)
        r_token = request.form.get('CSRF_TOKEN',
                request.headers.get('X-CSRFToken'))

        if not s_token or s_token != r_token:
            abort(403)

@app.after_request
def after_request(req):
    if hasattr(g, 'update_csrf_token') and g.update_csrf_token:
        req.set_cookie('X-CSRFToken', session['CSRF_TOKEN'])
    return req

@app.teardown_request
def teardown(e):
    if hasattr(g, 'conn'):
        g.conn.close()

def init_db():
    g.conn = connect_db()
    g.cursor = g.conn.cursor()

@app.route('/admin')
def admin_index():
    if check_auth():
        return render_template('admin_index.html')
    else:
        return render_template('admin_login.html')

#For CSRF protection
def gen_csrf_token(refresh = False):
    if refresh or 'CSRF_TOKEN' not in session:
        session['CSRF_TOKEN'] = uuid.uuid4().hex
        g.update_csrf_token = True
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
