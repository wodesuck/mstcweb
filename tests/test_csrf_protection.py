from nose.tools import assert_equals
from routes import app, disable_csrf_protection, gen_csrf_token
from flask import session, render_template_string, request
import uuid

def setUp():
    app.testing = True

    @app.route('/csrf_test', methods = ['GET', 'POST'])
    def csrf_t():
        if request.method == 'GET':
            return gen_csrf_token()
        else:
            return ''

def test_check_pass_in_form():
    with app.test_client() as c:
        respon = c.get('/csrf_test')
        assert_equals(respon.status_code, 200)

        respon = c.post('/csrf_test', data = {'CSRF_TOKEN': respon.data})
        assert_equals(respon.status_code, 200)

def test_check_pass_in_headers():
    with app.test_client() as c:
        respon = c.get('/csrf_test')
        assert_equals(respon.status_code, 200)

        respon = c.post('/csrf_test', headers = [('X-CSRFToken', respon.data)])
        assert_equals(respon.status_code, 200)

def test_check_fail_without_token():
    with app.test_client() as c:
        respon = c.post('/csrf_test')
        assert_equals(respon.status_code, 403)

        c.get('/csrf_test')
        respon = c.post('/csrf_test')
        assert_equals(respon.status_code, 403)

def test_check_fail_wrong_token_in_form():
    with app.test_client() as c:
        c.get('/csrf_test')

        respon = c.post('/csrf_test', data = {'CSRF_TOKEN': uuid.uuid4().hex})
        assert_equals(respon.status_code, 403)

def test_check_fail_wrong_token_in_header():
    with app.test_client() as c:
        c.get('/csrf_test')

        respon = c.post('/csrf_test',
                headers = [('X-CSRFToken', uuid.uuid4().hex)])
        assert_equals(respon.status_code, 403)

def test_white_list():

    @app.route('/csrf_test/white_list', methods = ['POST'])
    @disable_csrf_protection
    def white_list_view_func():
        return ''

    with app.test_client() as c:
        respon = c.post('/csrf_test/white_list')
        assert_equals(respon.status_code, 200)

def test_token_rendered_in_template():
    app.add_url_rule('/csrf_test/template', view_func =
            lambda: render_template_string("{{ CSRF_TOKEN() }}"))

    with app.test_client() as c:
        respon_data = c.get('/csrf_test/template').data
        assert_equals(respon_data, session['CSRF_TOKEN'])

def test_token_passed_in_cookies():
    with app.test_client() as c:
        respon = c.get('/csrf_test')
        set_cookie_header = 'X-CSRFToken=' + respon.data

        assert any(map(
            lambda x: x[1].startswith(set_cookie_header),
            respon.headers))
