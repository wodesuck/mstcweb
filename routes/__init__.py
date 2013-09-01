from flask import Flask
app = Flask(__name__, template_folder = '../layouts')

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
