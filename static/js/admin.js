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

    var _extra_properties = field.children('.extra-properties').val().split(',');
    var extra_properties = [];
    for(var i = 0; i < _extra_properties.length; ++i) {
      if(_extra_properties[i].trim())
        extra_properties.push(_extra_properties[i].trim());
    }
    if(field_data.field_type == 'input' || field_data.field_type == 'textarea') {
      if(extra_properties.length == 2) {
        field_data.min_len = Number(extra_properties[0]);
        field_data.max_len = Number(extra_properties[1]);
      }
    }
    if(field_data.field_type == 'number') {
      if(extra_properties.length == 2) {
        field_data.min_val = Number(extra_properties[0]);
        field_data.max_val = Number(extra_properties[1]);
      }
    }
    if(field_data.field_type == 'select') {
      if(extra_properties.length)
        field_data.option_list = extra_properties;
      else
        return true;
    }

    content_fields.push(field_data);
  });

  data.content_fields = JSON.stringify(content_fields);

  $.post(location.href, data, function(respon) {
    if(respon.err_code == 0) {
      $('#edit-form .alert-success').text(respon.msg).show(200);
      setTimeout(function() {location.href = '/admin' }, 800);
    }
    else {
      $('#edit-form .alert-danger').text(respon.msg).show(200);
    }
  }).fail(function() {
    $('#edit-form .alert-danger').text('未登录或登录失效！请重新登录再试。').show(200);
  });
}

function query_forms(by) {
  if(by == 'event_name') {
    var event_name = $('#query-by-event-name select').val();

    $.get('/admin/forms/' + event_name + '/query', function(respon) {
      if(respon.err_code == 0)
        show_query_forms_result(respon.result);
    }).fail(function() {
      show_query_forms_result([]);
    })
  }
  else if(by == 'form_id') {
    var form_id = $('#query-by-form-id input').val();

    $.get('/admin/forms/query/' + form_id, function(respon) {
      if(respon.err_code == 0)
        show_query_forms_result([respon.result]);
    }).fail(function() {
      show_query_forms_result([]);
    });
  }
}

function format_string(str, data) {
  return str.replace(/\{(.+?)\}/g, function(s, k) { return data[k]; });
}

function show_query_forms_result(result) {
  $('#forms-query-result').empty();
  if(!result.length) {
    $('#forms-query-result').append(
      $.parseHTML('<div class="alert alert-warning">找不到对应的结果！</div>')
    );
  }
  $.each(result, function(i, form) {
    var content = [];
    $.each(form.content, function(i, v) {
      content.push(
        format_string('<li>{name}：{value}</li>',
                      { name: v[0], value: v[1] }));
    });
    form.other = content.join('\n');

    var form_str = '\
    <div class="panel panel-default">\
    <div class="panel-heading">\
        <h3 class="panel-title pull-left">{name}</h3>\
        <button class="btn btn-danger btn-xs pull-right delete-form-by-id" data-form-id="{form_id}">\
            <span class="glyphicon glyphicon-remove"></span> 删除\
        </button>\
        <div class="clearfix"></div>\
    </div>\
    <div class="panel-body">\
        <ul>\
        <li>报名表编号：{form_id}</li>\
        <li>电子邮件：{email}</li>\
        <li>报名时间：{created_time}</li>\
        {other}\
    </div>';
    $('#forms-query-result').append($.parseHTML(format_string(form_str, form)));
  });

  $('button.delete-form-by-id').each(function(i, v) {
    $(v).popover({
      html: true,
      placement: 'bottom',
      title: '删除确认',
      container: 'body',
      content: format_string('<p>55555不要删我～～～</p>\
                             <button class="btn btn-default" onclick="delete_form_by_id(\'{form_id}\', true);">删掉</button>\
                             <button class="btn btn-primary" onclick="delete_form_by_id(\'{form_id}\', false);">放开他</button>',
                             {form_id: $(v).data('form-id')})
    });
  });
}

function delete_page(name, ensure) {
  if(ensure)
    $.post('/admin/pages/' + name + '/delete', function(respon) {
      if(respon.err_code == 0)
        $('button.delete-page[data-name="' + name + '"]').parents('tr').remove();
    });

  $('button.delete-page[data-name="' + name + '"]').popover('toggle');
}

function delete_form(name, ensure) {
  if(ensure)
    $.post('/admin/forms/' + name + '/delete', function(respon) {
      if(respon.err_code == 0) {
        $('button.delete-form[data-name="' + name + '"]').parents('tr').remove();
        delete_page(name, ensure);
      }
    });

  $('button.delete-form[data-name="' + name + '"]').popover('toggle');
}

function delete_form_by_id(form_id, ensure) {
  if (ensure)
    $.post('/admin/forms/delete/' + form_id, function(respon) {
      if (respon.err_code == 0) {
        $('button.delete-form-by-id[data-form-id="' + form_id + '"]').parents('div.panel').remove();
      }
    });

  $('button.delete-form-by-id[data-form-id="' + form_id + '"]').popover('toggle');
}

function on_field_type_changed(the_input, new_type) {
  the_input.val('');
  switch(new_type) {
    case 'input':
    case 'textarea':
      the_input.attr('placeholder', '长度范围(默认0,65536)');
      break;
    case 'number':
      the_input.attr('placeholder', '值范围(默认-65536,65535)');
      break;
    case 'select':
      the_input.attr('placeholder', '选项列表(英文逗号分隔)');
      break;
    default:
      the_input.attr('placeholder', '(留空)'); break;
  }
}

$(function() {
  //Register ajaxPrefilter for CSRF protection
  $.ajaxPrefilter(function(options, oriOptions, jqXHR) {
    if(oriOptions.type == 'post') {
      var cookies = document.cookie.split(';');
      var cookie_match = false;
      for(var i = 0; i < cookies.length; ++i) {
        cookie_match = cookies[i].trim().match(/X-CSRFToken=(.+)/);
        if(cookie_match)
          break;
      }
      if(cookie_match)
        jqXHR.setRequestHeader('X-CSRFToken', cookie_match[1]);
    }
  });

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

  //Register events for the edit page
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
    field_form.children('.field-type').change(function() {
      on_field_type_changed(field_form.children('.extra-properties'), $(this).val());
    });
    $('.content-field').last().after(field_form);
  });

  $('select.field-type').change(function() {
    var the_input = $(this).parent('.content-field').children('.extra-properties');
    on_field_type_changed(the_input, $(this).val());
  });

  //Register events for the query page
  $('#query-by-event-name button').click(function() {
    query_forms('event_name');
  })

  $('#query-by-form-id button').click(function() {
    query_forms('form_id');
  })

  //Register events for the delete buttons
  $('button.delete-page').each(function(i, v) {
    $(v).popover({
      html: true,
      placement: 'bottom',
      title: '删除确认',
      container: 'body',
      content: format_string('<p>55555不要删我～～～</p>\
                             <button class="btn btn-default" onclick="delete_page(\'{name}\', true);">删掉</button>\
                             <button class="btn btn-primary" onclick="delete_page(\'{name}\', false);">放开他</button>',
                             {name: $(v).data('name')})
    });
  });

  $('button.delete-form').each(function(i, v) {
    $(v).popover({
      html: true,
      placement: 'bottom',
      title: '删除确认',
      container: 'body',
      content: format_string('<p>55555不要删我～～～</p>\
                             <button class="btn btn-default" onclick="delete_form(\'{name}\', true);">删掉</button>\
                             <button class="btn btn-primary" onclick="delete_form(\'{name}\', false);">放开他</button>',
                             {name: $(v).data('name')})
    });
  });
});
