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
    pass

@app.route('/admin/forms/<name>', methods = ['DELETE'])
def admin_forms_delete(name):
    pass

@app.route('/admin/forms/<name>/edit')
def admin_forms_edit(name):
    pass

@app.route('/admin/forms', methods = ['PATCH', 'POST'])
def admin_forms_save():
    pass

@app.route('/admin/forms/<name>/query')
def admin_forms_query(name):
    pass

@app.route('/admin/forms/query/<int:form_id>')
def admin_forms_query_by_id(form_id):
    pass

@app.route('/admin/forms/<int:form_id>/status/<int:status>', methods = ['POST'])
def admin_forms_change_status(form_id, status):
    pass
