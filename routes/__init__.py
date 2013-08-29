from flask import Flask
from common.config import SESSION_KEY

app = Flask(__name__)
app.secret_key = SESSION_KEY

import routes.pages
import routes.forms
