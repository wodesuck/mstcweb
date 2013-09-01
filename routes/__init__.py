from flask import Flask, g
import MySQLdb
from common.db import connect_db

app = Flask(__name__)

@app.before_request
def init():
    g.conn = connect_db()
    g.cursor = g.conn.cursor()

@app.teardown_request
def teardown():
    if hasattr(g, 'conn'):
        g.conn.close()

import routes.pages
import routes.forms
