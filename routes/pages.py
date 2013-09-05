# -*- coding: utf8 -*-
from routes import app
from models.page import Page, NoSuchPage, PageNameExist
from common.userauth import check_auth
from flask import render_template, abort, jsonify, request
from jinja2.exceptions import TemplateNotFound
import MySQLdb


@app.route('/pages/<name>')
def show_page(name):
    try:
        page = Page.get(name)
        return render_template('pages/%s.html' % page.layout,
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


@app.route('/admin/pages/<name>', methods=['DELETE'])
def admin_pages_delete(name):
    if not check_auth():
        abort(403)

    Page.delete(name)
    return jsonify(err_code=0, msg=u'页面（%s）已删除' % name)


@app.route('/admin/pages/<name>/edit')
def admin_pages_edit(name):
    if not check_auth():
        abort(403)

    try:
        page = Page.get(name)
        return render_template('page_edit.html', **page.__dict__)
    except NoSuchPage:
        abort(404)


@app.route('/admin/pages', methods=['PATCH', 'POST'])
def admin_pages_save():
    """
    accept requests from /admin/pages/new or /admin/pages/<name>/edit
    save changes to database
    return msg:
        -1 -- patched page doesn't exist / same name has existed
        -2 -- database error
        0 -- success
    POST: from /admin/pages/new, insert a new page to database
    PATCH: from /admin/pages/<name>/edit, change an existing entry in database
    """
    if not check_auth():
        abort(403)

    name = request.form['name']
    if request.method == 'PATCH':
        try:
            Page.get(name).update(**request.form)
        except NoSuchPage:
            return jsonify(err_code=-1, msg=u'页面（%s）不存在' % name)

        return jsonify(err_code=0, msg=u'修改保存成功')
    else:
        try:
            Page.create(**request.form)
        except PageNameExist:
            return jsonify(err_code=-1, msg=u'页面名称（%s）已存在' % name)
        except MySQLdb.IntegrityError:
            return jsonify(err_code=-1, msg=u'数据库错误')

        return jsonify(err_code=0, msg=u'页面新建成功')
