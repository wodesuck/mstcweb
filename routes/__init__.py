from flask import Flask
app = Flask(__name__, template_folder = '../layouts')

import routes.pages
import routes.forms
