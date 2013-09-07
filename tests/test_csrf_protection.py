from nose.tools import assert_equals
from routes import app, disable_csrf_protection, gen_csrf_token
from flask import session

def setUp():
    pass

def test_check_pass_in_form():
    pass

def test_check_pass_in_headers():
    pass

def test_check_fail_without_token():
    pass

def test_check_fail_wrong_token_in_form():
    pass

def test_check_fail_wrong_token_in_header():
    pass

def test_white_list():
    pass

def test_token_generator():
    pass

def test_token_rendered_in_template():
    pass

def test_token_passed_in_cookies():
    pass
