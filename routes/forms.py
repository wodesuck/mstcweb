# -*- coding: utf8 -*-
from routes import app
from models import form
import json
from common.userauth import check_auth

from flask import (request, jsonify, render_template, abort)

@app.route('/forms/<name>', methods = ['GET', 'POST'])
def forms(name):
    """
    a page for visitors to fill and submit entry forms
    abort 404 if the event name doesn't exist
    return msg when accept a post request:
        -1 -- invalid content
        -2 -- not started yet
        -3 -- ended
        0 -- success

    GET: show an entry form
    POST: submit an entry form to server
    """
    try:
        eventObj = form.Event.get(name)
    except form.NoSuchEvent:
        abort(404)

    if request.method == 'GET':
        return render_template('form.html', **eventObj.__dict__)
    else:
        try:
            form_id = eventObj.submit(
                    request.form['name'],
                    request.form['email'],
                    json.loads(request.form['content']))
        except form.InvalidSubmit:
            return jsonify(err_code = -1, msg = u'提交内容无效')
        except form.NotStartYet:
            return jsonify(err_code = -2, msg = u'该报名时间尚未开始')
        except form.Ended:
            return jsonify(err_code = -3, msg = u'该报名时间已结束')
        else:
            return jsonify(err_code = 0,
                    msg = u'报名成功！报名编号：%d' % form_id)

@app.route('/admin/forms/new')
def admin_forms_new():
    """
    a page for administrators to construct new events for registration

    GET: show the page
    """
    if not check_auth():
        abort(403)

    return render_template('event_new.html')

@app.route('/admin/forms/<name>', methods = ['DELETE'])
def admin_forms_delete(name):
    """
    accept DELETE requests and delete the corresponding events in database

    DELETE: delete an event
    """
    if not check_auth():
        abort(403)

    form.Event.delete_event(name = name)
    return jsonify(err_code = 0, msg = u'报名事件（%s）已删除' % name)

@app.route('/admin/forms/<name>/edit')
def admin_forms_edit(name):
    """
    a page for administrators to edit existing events
    abort 404 if the event name doesn't exist

    GET: show the page
    """
    if not check_auth():
        abort(403)

    try:
        eventObj = form.Event.get(name)
    except form.NoSuchEvent:
        abort(404)

    return render_template('event_edit.html', **eventObj.__dict__)

@app.route('/admin/forms', methods = ['PATCH', 'POST'])
def admin_forms_save():
    """
    accept requests from /admin/forms/new or /admin/forms/<name>/edit
    and save changes to database
    abort 404 if the name of the patched event doesn't exist
    return msg (PATCH/POST):
        -1 -- patched event doesn't exist / same name has existed
        -2 -- none / database error
        0 -- success

    POST: from /admin/forms/new, insert a new event to database
    PATCH: from /admin/forms/<name>/edit, change an existing entry in database
    """
    if not check_auth():
        abort(403)

    if request.method == 'PATCH':
        try:
            eventObj = form.Event.get(name)
        except form.NoSuchEvent:
            return jsonify(err_code = -1, msg = u'报名事件（%s）不存在' % name)

        eventObj.content_fields = map(lambda x: form.FieldDescription(**x),
                json.loads(request.form['content_fields']))
        eventObj.start_time = form.datetime(request.form['start_time'])
        eventObj.end_time = form.datetime(request.form['end_time'])
        eventObj.save()
        return jsonify(err_code = 0, msg = u'修改保存成功')

    else:
        args = { 'name': request.form['name'], 
                'content_fields': map(lambda x: form.FieldDescription(**x),
                    json.loads(request.form['content_fields'])),
                'start_time': form.datetime(request.form['start_time']),
                'end_time': form.datetime(request.form['end_time'])}
        eventObj = form.Event(**args)

        try:
            eventObj.save()
        except form.NameExisted:
            return jsonify(err_code = -1, msg = u'此报名事件已存在')
        except form.MySQLdb.IntegrityError:
            return jsonify(err_code = -2, msg = u'数据库错误')

        return jsonify(err_code = 0, msg = u'新报名事件创建成功 id：%d' % eventObj.id)

@app.route('/admin/forms/<name>/query')
def admin_forms_query(name):
    """
    a page for administrators to query forms of a specific event
    abort 404 if the event name doesn't exist
    accept 3 optional arguments:
        items -- the number of forms showed in one page
        page -- the index of page to show
        status -- specify status of forms to show
    return result as json

    GET: show the query result
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
        abort(404)

    forms = eventObj.query(items, page, status)
    for formObj in forms:
        formObj.created_time = formObj.created_time.strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(err_code = 0, result = [formObj.__dict__ for formObj in forms])

@app.route('/admin/forms/query/<int:form_id>')
def admin_forms_query_by_id(form_id):
    """
    query a form with a specific form_id
    abort 404 if there is no such form
    return result as json

    GET: show the query result
    """
    if not check_auth():
        abort(403)

    try:
        formObj = form.Event.query_one(form_id)
    except form.NoSuchForm:
        abort(404)

    formObj.created_time = formObj.created_time.strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(err_code = 0, result = formObj.__dict__)

@app.route('/admin/forms/<int:form_id>/status/<int:status>', methods = ['POST'])
def admin_forms_change_status(form_id, status):
    """
    change the status of a form with the specific form_id
    return msg:
        -1 -- form doesn't exist
        0 -- success (with form_id and current status)

    POST: change a form to new status
    """
    if not check_auth():
        abort(403)

    try:
        form.Event.change_form_status(form_id, status)
    except form.NoSuchForm:
        return jsonify(err_code = -1, msg = u'报名表不存在')
    else:
        return jsonify(err_code = 0,
                msg = u'修改成功，报名表（%d）当前状态为：%d' % (form_id, status))
