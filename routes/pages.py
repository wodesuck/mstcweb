from routes import app
from models import page


@app.route('/pages/<name>')
def show_page(name):
    return 'Hello %s!' % name
