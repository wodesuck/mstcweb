from routes import app
from common.userauth import User
from flask import request, jsonify

@app.route('/login', methods = ['GET', 'POST']):
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

@app.route('/logout'):
    if User.logout():
        return jsonify(err_code = 0)
    else:
        return jsonify(err_code = -1)
