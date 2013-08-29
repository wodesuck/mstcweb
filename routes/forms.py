# -*- coding: utf8 -*-
from routes import app
from models import form
import json

from flask import (request, jsonify, render_template, abort)

@app.route('/forms/<name>', methods = ['GET', 'POST'])
def forms(name):
    try:
        eventObj = form.Event.get(name)
    except form.NoSuchEvent:
        abort(404)

    if request.method == 'GET':
        return render_template('form.html', **eventObj.__dict__)
    else:
        try:
            print request.form['content']
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
    return render_template('event_new.html')

@app.route('/admin/forms/<name>', methods = ['DELETE'])
def admin_forms_delete(name):
    # I think this is unnecessary
    try:
        eventObj = form.Event.get(name)
    except form.NoSuchEvent:
        return jsonify(err_code = -1, msg = u'报名事件（%s）不存在' % name)
    #
    form.Event.delete_event(name = name)
    return jsonify(err_code = 0, msg = u'报名事件（%s）已删除' % name)

@app.route('/admin/forms/<name>/edit')
def admin_forms_edit(name):
    try:
        eventObj = form.Event.get(name)
    except form.NoSuchEvent:
        abort(404)

    return render_template('event_edit.html', **eventObj.__dict__)

@app.route('/admin/forms', methods = ['PATCH', 'POST'])
def admin_forms_save():
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
    try:
        eventObj = form.Event.get(name)
    except form.NoSuchEvent:
        abort(404)

    forms = eventObj.query()
    for formObj in forms:
        formObj.created_time = formObj.created_time.strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(err_code = 0, result = [formObj.__dict__ for formObj in forms])

@app.route('/admin/forms/query/<int:form_id>')
def admin_forms_query_by_id(form_id):
    try:
        formObj = form.Event.query_one(form_id)
    except form.NoSuchForm:
        abort(404)

    formObj.created_time = formObj.created_time.strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(err_code = 0, result = formObj.__dict__)

@app.route('/admin/forms/<int:form_id>/status/<int:status>', methods = ['POST'])
def admin_forms_change_status(form_id, status):
    try:
        form.Event.change_form_status(form_id, status)
    except form.NoSuchForm:
        return jsonify(err_code = -1, msg = u'报名表不存在')
    else:
        return jsonify(err_code = 0,
                msg = u'修改成功，报名表（%d）当前状态为：%d' % (form_id, status))
