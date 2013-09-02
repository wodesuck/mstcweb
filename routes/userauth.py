from routes import app
from common import userauth
from flask import request, jsonify

@app.route('/admin/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        salt = userauth.get_salt(request.args['username'])
        salt['err_code'] = 0
        return jsonify(**salt)
    else:
        if userauth.login(request.form['username'], request.form['pwhash']):
            return jsonify(err_code = 0)
        else:
            return jsonify(err_code = -1)

@app.route('/admin/logout')
def logout():
    if userauth.logout():
        return jsonify(err_code = 0)
    else:
        return jsonify(err_code = -1)

@app.route('/admin/login/test')
def login_test():
    return str(int(userauth.check_auth()))

@app.route('/admin/change_passwd', methods = ['POST'])
def change_passwd():
    if userauth.change_passwd(
            request.form['oldpwhash'],
            request.form['newpwhash']):
        return jsonify(err_code = 0)
    else:
        return jsonify(err_code = -1)
