# -*- coding: utf8 -*-
from routes import app
from models.page import Page, NoSuchPage
from common.userauth import check_auth
from flask import render_template, abort, jsonify
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


@app.route('/admin/pages/new')
def admin_pages_new(name):
    if not check_auth():
        abort(403)

    return render_template('page_new.html')


@app.route('/admin/pages/<name>', method=['DELETE'])
def admin_pages_delete(name):
    if not check_auth():
        abort(403)

    Page.delete(name)
    return jsonify(err_code=0, msg=u'页面（%s）已删除' % name)
