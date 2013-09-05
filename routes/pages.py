# -*- coding: utf8 -*-
from routes import app
from models.page import Page, NoSuchPage
from flask import render_template, abort
from jinja2.exceptions import TemplateNotFound


@app.route('/pages/<name>')
def show_page(name):
    try:
        page = Page.get(name)
        return render_template('layouts/%s.html' % page.layout,
                               **page.__dict__)
    except NoSuchPage:
        abort(404)
    except TemplateNotFound:
        abort(404)
