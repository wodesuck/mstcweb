# -*- coding: utf-8 -*-
from routes import app, gen_csrf_token
from models import form
from models import page
import json
from common.userauth import check_auth
from datetime import datetime
from flask import (request, jsonify, render_template, abort, escape)

def _from_datetime_str(datetime_str):
    return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

@app.route('/forms/<name>', methods = ['GET', 'POST'])
def forms(name):
    """
    Show the entry form or deal with the submitted form.
    If argument 'name' is not an existing event name, abort 404.

    GET: Show the entry form.
	
    POST: Submit the entry form. Return one of the following messages.

        invalid content (err_code = -1)
        not started     (err_code = -2)
        ended           (err_code = -3)
        accepted        (err_code =  0)
    """
    try:
        eventObj = form.Event.get(name)
    except form.NoSuchEvent:
        abort(404)

    if request.method == 'GET':
        return render_template('form.html', **eventObj.__dict__)
    else:
        new_token = gen_csrf_token(True)
        try:
            form_id = eventObj.submit(
                    request.form['name'],
                    request.form['email'],
                    json.loads(request.form['content']))
        except form.InvalidSubmit, e:
            if e.error_field == 'id':
                return jsonify(err_code = -1,
                        msg = u'报名事件不存在',
                        new_token = new_token)
            return jsonify(err_code = -1,
                    err_field = e.error_field,
                    msg = u'提交内容无效，请检查您的输入',
                    new_token = new_token)
        except form.NotStartYet:
            return jsonify(err_code = -2,
                    msg = u'该报名时间尚未开始',
                    new_token = new_token)
        except form.Ended:
            return jsonify(err_code = -3,
                    msg = u'该报名时间已结束',
                    new_token = new_token)
        else:
            return jsonify(err_code = 0,
                    msg = u'报名成功！报名编号：%d' % form_id)

@app.route('/admin/forms')
def admin_forms():
    if not check_auth():
        abort(403)

    return render_template('admin_forms.html',
            items_list = form.Event.get_events_list())

@app.route('/admin/forms/query')
def admin_forms_query():
    if not check_auth():
        abort(403)

    return render_template('admin_forms_query.html',
            events_list = form.Event.get_events_list())

@app.route('/admin/forms/new', methods = ['GET', 'POST'])
def admin_forms_new():
    """
    The edit page for creating new event.
    Administrator should have logged in to access this page.

    GET: Show the edit page.

    POST: Save the new event. Return one of the following messages.

        same name exist (err_code = -1)
        database error  (err_code = -2)
        success         (err_code =  0, with new event id)
    """
    if not check_auth():
        abort(403)

    if request.method == 'GET':
        return render_template('admin_forms_new.html')

    else:
        args = {'name': request.form['name'], 
                'content_fields': map(lambda x: form.FieldDescription(**x),
                    json.loads(request.form['content_fields'])),
                'start_time': _from_datetime_str(request.form['start_time']),
                'end_time': _from_datetime_str(request.form['end_time'])}
        eventObj = form.Event(**args)

        pageObj = page.Page(name = request.form['name'],
                title = request.form['title'],
                content = request.form['content'],
                layout = "form_page")

        try:
            eventObj.save()
            pageObj.save()
        except (form.NameExisted, page.PageNameExist):
            gen_csrf_token()
            return jsonify(err_code = -1, msg = u'此报名事件已存在')
        except form.MySQLdb.IntegrityError:
            gen_csrf_token()
            return jsonify(err_code = -2, msg = u'数据库错误')

        return jsonify(err_code = 0, msg = u'新报名事件创建成功 id：%d' % eventObj.id)

@app.route('/admin/forms/<name>/edit', methods = ['GET', 'POST'])
def admin_forms_edit(name):
    """
    The edit page for changing existing event.
    Administrator should have logged in to access this page.
    If argument 'name' is not an existing event name, abort 404.

    GET: Show the edit page.

    POST: Save the change.
    """
    if not check_auth():
        abort(403)

    try:
        eventObj = form.Event.get(name)
        pageObj = page.Page.get(name)
    except (form.NoSuchEvent, page.NoSuchPage):
        abort(404)

    if request.method == 'GET':
        ctx_data = page.Page.get(name).__dict__
        for k, v in eventObj.__dict__.items():
            ctx_data[k] = v
        return render_template('admin_forms_edit.html', **ctx_data)

    else:
        eventObj.name = request.form['name']
        eventObj.content_fields = map(lambda x: form.FieldDescription(**x),
                json.loads(request.form['content_fields']))
        eventObj.start_time = _from_datetime_str(request.form['start_time'])
        eventObj.end_time = _from_datetime_str(request.form['end_time'])
        eventObj.save()

        pageObj.update(name = request.form['name'],
                title = request.form['title'],
                content = request.form['content'],
                layout = 'form_page')

        return jsonify(err_code = 0, msg = u'修改保存成功')

@app.route('/admin/forms/<name>/delete', methods = ['POST'])
def admin_forms_delete(name):
    """
    Delete the specific event.
    Administrator should have logged in to access this page.
    """
    if not check_auth():
        abort(403)

    form.Event.delete_event(name = name)
    return jsonify(err_code = 0, msg = u'报名事件（%s）已删除' % name)

@app.route('/admin/forms/<name>/query')
def admin_forms_query_by_event_name(name):
    """
    Query forms of a specific event.
    Administrator should have logged in to access this page.
    If argument 'name' is not an existing event name, abort 404.

    Accept 3 optional request arguments:
        items  -- the number of forms showed in one page
        page   -- the index of page to show
        status -- the specify status of forms to show

    Return query results as json.
    """
    if not check_auth():
        abort(403)

    try:
        eventObj = form.Event.get(name)
    except form.NoSuchEvent:
        abort(404)

    try:
        items = int(request.args.get('items', 0))
        page = int(request.args.get('page', 0))
        status = request.args.get('status', None)
        if status is not None:
            status = int(status)
    except ValueError:
        abort(400)

    forms = eventObj.query(items, page, status)
    for formObj in forms:
        formObj.name = escape(formObj.name)
        formObj.email = escape(formObj.email)
        formObj.created_time = formObj.created_time.strftime('%Y-%m-%d %H:%M:%S')
        formObj.content = formObj.content
    return jsonify(err_code = 0, result = [formObj.__dict__ for formObj in forms])

@app.route('/admin/forms/query_by_form_id/<int:form_id>')
def admin_forms_query_by_id(form_id):
    """
    Query the form with the specific id.
    Administrator should have logged in to access this page.
    Abort 404 if there is no such form.
    Return the query result as json.
    """
    if not check_auth():
        abort(403)

    try:
        formObj = form.Event.query_one(form_id)
    except form.NoSuchForm:
        abort(404)

    formObj.content = formObj.content

    formObj.name = escape(formObj.name)
    formObj.email = escape(formObj.email)
    formObj.created_time = formObj.created_time.strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(err_code = 0, result = formObj.__dict__)

@app.route('/admin/forms/query_by_form_name/<form_name>')
def admin_forms_query_by_name(form_name):
    """
    Query the form with the specific name.
    Administrator should have logged in to access this page.
    Abort 404 if there is no such form.
    Return the query result as json.
    """
    if not check_auth():
        abort(403)
    try:
        form_data_list = form.FormData.query_form_data_by(form_name=form_name)
    except form.NoSuchForm:
        abort(404)
    except TypeError:
        abort(404)

    for form_data in form_data_list:
        form_data.name = escape(form_data.name)
        form_data.email = escape(form_data.email)
        form_data.created_time = form_data.created_time.strftime('%Y-%m-%d %H:%M:%S')
        form_data.content = form_data.content

    return jsonify(err_code = 0, result = [form_data.__dict__ for form_data in form_data_list])

@app.route('/admin/forms/query_by_form_email/<form_email>')
def admin_forms_query_by_email(form_email):
    """
    Query the form with the specific email.
    Administrator should have logged in to access this page.
    Abort 404 if there is no such form.
    Return the query result as json.
    """
    if not check_auth():
        abort(403)
    try:
        form_data_list = form.FormData.query_form_data_by(form_email=form_email)
    except form.NoSuchForm:
        abort(404)
    except TypeError:
        abort(404)

    for form_data in form_data_list:
        form_data.content = form_data.content
        form_data.name = escape(form_data.name)
        form_data.email = escape(form_data.email)
        form_data.created_time = form_data.created_time.strftime('%Y-%m-%d %H:%M:%S')

    return jsonify(err_code = 0, result = [form_data.__dict__ for form_data in form_data_list])

@app.route('/admin/forms/<int:form_id>/status/<int:status>', methods = ['POST'])
def admin_forms_change_status(form_id, status):
    """
    Change the status of the form with the specific id
    Administrator should have logged in to access this page.
    Abort 404 if there is no such form.
    Return new status.
    """
    if not check_auth():
        abort(403)

    try:
        form.Event.change_form_status(form_id, status)
    except form.NoSuchForm:
        abort(404)
    else:
        return jsonify(err_code = 0,
                msg = u'修改成功，报名表（%d）当前状态为：%d' % (form_id, status))

@app.route('/admin/forms/delete/<int:form_id>', methods = ['POST'])
def admin_forms_delete_by_id(form_id):
    """
    Delete the form with the specific id.
    Administrator should have logged in to access this page.
    Return the query result as json.
    """
    if not check_auth():
        abort(403)

    form.Event.delete_form(form_id)
    return jsonify(err_code = 0, msg = u'报名表（ %d）已删除' % form_id)
