function login() {
  var username = $('#main-login-form input[type="text"]').val();
  var password = $('#main-login-form input[type="password"]').val();
  var hasher = new bCrypt();

  $('#main-login-form .alert').hide(100);

  $.get('/admin/login', { username: username }, function(result) {
    hasher.hashpw(password, result.account_salt, function(pwhash1) {
      hasher.hashpw(pwhash1, result.session_salt, function(pwhash2) {
        $.post('/admin/login', { username: username, pwhash: pwhash2 }, function(result) {
          if(result.err_code == 0)
            location.reload();
        }).fail(function() {
          $('#main-login-form input[type="password"]').val('').focus();
          $('#main-login-form .alert').show(200);
        });
      });
    });
  });
}

function logout() {
  $.get('/admin/logout', function() {
    location.href = '/admin';
  });
}

$(function() {
  //Register events for login page
  $('#main-login-form button').click(function(e) {
    e.preventDefault();
    login();
  });
});
