from routes import app
from models import form

@app.route('/forms/<name>', methods = ['GET', 'POST'])
def forms(name):
    pass

@app.route('/admin/forms/new')
def admin_forms_new():
    pass

@app.route('/admin/forms/<name>', methods = ['DELETE'])
def admin_forms_delete(name):
    pass

@app.route('/admin/forms/<name>/edit')
def admin_forms_edit(name):
    pass

@app.route('/admin/forms/save', methods = ['PATCH', 'POST'])
def admin_forms_save():
    pass

@app.route('/admin/forms/<name>/query')
def admin_forms_query(name):
    pass

@app.route('/admin/forms/query/<int:form_id>')
def admin_forms_query_by_id(form_id):
    pass

@app.route('/admin/forms/<int:form_id>/status/<int:status>', methods ['POST'])
def admin_forms_change_status(form_id, status):
    pass
