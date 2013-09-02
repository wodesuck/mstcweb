from routes import app
from common.userauth import User
from flask import request, jsonify

@app.route('/admin/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        salt = User.get_salt(request.args['username'])
        salt['err_code'] = 0
        return jsonify(**salt)
    else:
        userObj = User(request.form['username'], request.form['pwhash'])
        if userObj.login():
            return jsonify(err_code = 0)
        else:
            return jsonify(err_code = -1)

@app.route('/admin/logout')
def logout():
    if User.logout():
        return jsonify(err_code = 0)
    else:
        return jsonify(err_code = -1)

@app.route('/admin/login/test')
def login_test():
    return str(int(User.check_auth()))
