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

function save_form() {
  tinymce.editors.content.save();
  $('#edit-form .alert').hide(100);

  var data = {};
  $.each($('#edit-form').serializeArray(), function(i, field) {
    data[field.name] = field.value;
  });

  var content_fields = [];
  $('.content-field').each(function(i, v) {
    var field = $(v);
    var field_data = {
      field_name: field.children('.field-name').val(),
      field_type: field.children('.field-type').val(),
    };
    if(!field_data.field_name)
      return true;

    var lower = field.children('.lower-bound').val();
    var upper = field.children('.upper-bound').val();
    if(field_data.field_type == 'input' || field_data.field_type == 'textarea') {
      if(lower)
        field_data.min_len = lower;
      if(upper)
        field_data.max_len = upper;
    }
    if(field_data.field_type == 'number') {
      if(lower)
        field_data.min_val = lower;
      if(upper)
        field_data.max_val = upper;
    }

    content_fields.push(field_data);
  });

  if(content_fields.length)
    data.content_fields = JSON.stringify(content_fields);

  $.post(location.href, data, function(respon) {
    if(respon.err_code == 0) {
      $('#edit-form .alert-success').text(respon.msg).show(200);
    }
    else {
      $('#edit-form .alert-danger').text(respon.msg).show(200);
    }
  }).fail(function() {
    $('#edit-form .alert-danger').text('未登录或登录失效！请重新登录再试。').show(200);
  });
}

$(function() {
  //Register events for login page
  $('#main-login-form button').click(function(e) {
    e.preventDefault();
    login();
  });

  //Register events for datetime picker
  $('input.date').datetimepicker({
    autoclose: true,
    todayBtn: true,
  });

  //Register events for the forms
  $('#edit-form').submit(function(e) {
    e.preventDefault();
    save_form();
  });

  $('.content-fields .remove-field').click(function() {
    $(this).parent().remove();
  });

  $('.content-fields .add-field').click(function() {
    var field_form = $('.content-field').last().clone();
    field_form.children('.form-control').val('');
    field_form.children('.remove-field').click(function() {
      field_form.remove();
    });
    $('.content-field').last().after(field_form);
  });
});
