from flask import Flask, g
import MySQLdb
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

import routes.userauth
import routes.pages
import routes.forms
