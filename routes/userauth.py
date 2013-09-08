from routes import app
from common import userauth
from flask import request, jsonify

@app.route('/admin/login', methods = ['GET', 'POST'])
def login():
    """
    Login.

    GET: Get the account salt of the specified user and the session salt.
        Username should be a query string argument with the name `username`.

    POST: Login. Username and password hash should be specified in the post
        data. Password hash is calculated by the following formula.

        hash_0 = Bcrypt(password, account_salt)
        hash = Bcrypt(hash_0, session_salt)
    """
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
    """
    Logout.
    """
    if userauth.logout():
        return jsonify(err_code = 0)
    else:
        return jsonify(err_code = -1)

@app.route('/admin/login/test')
def login_test():
    """
    An interface for unit test.
    Return '1' if the user is authorized and return '0' otherwise.
    """
    return str(int(userauth.check_auth()))

@app.route('/admin/change_passwd', methods = ['POST'])
def change_passwd():
    """
    Change password.
    Before changing password, the user should login successfully,
    then GET the /admin/login interface again to get the salts.

    The client should provide `oldpwhash` and `newpwhash`.

    `oldpwhash` is the hash of the old password calculated with
    the original account salt.
    `newpwhash` is the hash of the new password calculated with
    the *session salt*. So, the *session salt* will be the new
    account salt.
    """
    if userauth.change_passwd(
            request.form['oldpwhash'],
            request.form['newpwhash']):
        return jsonify(err_code = 0)
    else:
        return jsonify(err_code = -1)
