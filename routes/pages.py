# -*- coding: utf8 -*-
from routes import app, gen_csrf_token
from models.page import Page, NoSuchPage, PageNameExist
from common.userauth import check_auth
from flask import render_template, abort, jsonify, request
from jinja2.exceptions import TemplateNotFound
import MySQLdb


@app.route('/pages')
def show_pages_list():
    return render_template('pages.html', pageList = Page.get_pages_list())

@app.route('/about/<name>')
def about():
    """
    Static pages.
    """
    return render_template('%s.html' % name)

@app.route('/pages/<name>')
def show_page(name):
    try:
        page = Page.get(name)
        return render_template('%s.html' % page.layout,
                               **page.__dict__)
    except NoSuchPage:
        abort(404)
    except TemplateNotFound:
        abort(404)


@app.route('/admin/pages')
def admin_pages():
    if not check_auth():
        abort(403)

    items_list = filter(lambda x: x.layout != 'form_page', Page.get_pages_list())
    return render_template('admin_pages.html',
            items_list = items_list)


@app.route('/admin/pages/new', methods=['GET', 'POST'])
def admin_pages_new():
    """
    Create a new page.
    Administrator should have logged in to access this page.

    GET: Show the 'create page' page.

    POST: Save the new page. Return one of the following messages.

        same name exist (err_code = -1)
        database error  (err_code = -2)
        success         (err_code =  0)
    """
    if not check_auth():
        abort(403)

    if request.method == 'GET':
        return render_template('admin_pages_new.html')
    else:
        try:
            name = request.form['name']
            Page.create(name = request.form['name'],
                    title = request.form['title'],
                    content = request.form['content'],
                    layout = "pure_page")
        except PageNameExist:
            gen_csrf_token()
            return jsonify(err_code=-1, msg=u'页面名称（%s）已存在' % name)
        except MySQLdb.IntegrityError:
            gen_csrf_token()
            return jsonify(err_code=-2, msg=u'数据库错误')

        return jsonify(err_code=0, msg=u'页面新建成功')


@app.route('/admin/pages/<name>/edit', methods=['GET', 'POST'])
def admin_pages_edit(name):
    """
    Change an existing page.
    Administrator should have logged in to access this page.
    If argument 'name' is not an existing page name, abort 404

    GET: Show the 'edit page' page.

    POST: Save the change.
    """
    if not check_auth():
        abort(403)

    try:
        page = Page.get(name)
    except NoSuchPage:
        abort(404)

    if request.method == 'GET':
        return render_template('admin_pages_edit.html', **page.__dict__)
    else:
        page.update(name = request.form['name'],
                    title = request.form['title'],
                    content = request.form['content'],
                    layout = 'pure_page')
        return jsonify(err_code=0, msg=u'修改保存成功')


@app.route('/admin/pages/<name>/delete', methods=['POST'])
def admin_pages_delete(name):
    """
    Delete the specific page.
    Administrator should have logged in to access this page.
    """
    if not check_auth():
        abort(403)

    Page.delete(name)
    return jsonify(err_code=0, msg=u'页面（%s）已删除' % name)
