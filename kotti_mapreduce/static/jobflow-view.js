$(document).ready(function(){
    $('#spinner').bind('ajaxSend', function() {
        $(this).show();
    }).bind('ajaxStop', function() {
        $(this).hide();
    }).bind('ajaxError', function() {
        $(this).hide();
    });
});

$(function() {
    $('#resource_btn').click(function() {
        $('#resource_info').toggleClass('toggle-display');
    });

    $('#bootstrap_btn').click(function() {
        $('#bootstrap_info').toggleClass('toggle-display');
    });

    $('#runjobflow_btn').click(function() {
        $('#jobflow_list tbody *').remove();
        ajax_request($(this), {'type': 'runjobflow'}, append_jobflow_table);
        return false;
    });

    $('#refresh_btn').click(function() {
        $('#jobflow_list tbody *').remove();
        ajax_request($(this), {'type': 'refresh'}, append_jobflow_table);
        return false;
    });

    $('#terminate_btn').click(function() {
        $('#jobflow_list tbody *').remove();
        ajax_request($(this), {'type': 'terminate'}, append_jobflow_table);
        return false;
    });

    $('#getlog_btn').click(function() {
        $('#logfile tbody *').remove();
        ajax_request($(this), {'type': 'getlog'}, append_logfile_table);
        return false;
    });

    // initialize
    ajax_request($('#refresh_btn'), {'type': 'refresh'}, append_jobflow_table);

});


function ajax_request(btn, data, suc_callback, err_callback) {
    btn.button('loading');
    $.ajax({
        'type': 'POST',
        'url': window.location.href,
        'data': data,
        'dataType': 'json',
        'success': function(response) {
            console.log(response);
            if (suc_callback) {
                suc_callback(response);
            }
            btn.button('reset');
        },
        'error': function(xhr, text_status, err_thrown) {
            console.log(xhr);
            if (err_callback) {
                err_callback(response);
            }
            btn.button('reset');
        },
    });

    return true;
}

function append_jobflow_table(response) {
    var i, j, row, steps, bootstraps, rowspan;
    for (i in response) {
        row = '<tr><th>Job Flow</th><td>' +
                response[i]['jobflowid'] + '</td><td>' +
                response[i]['state'] + '</td><td>' +
                response[i]['keepjobflowalivewhennosteps']   + '</td><td>' +
                response[i]['creationdatetime']  + '</td><td>' +
                response[i]['startdatetime']  + '</td><td>' +
                response[i]['enddatetime']    + '</td></tr>';
        bootstraps = response[i]['bootstrapactions'];
        steps = response[i]['steps'];

        // bootstraps
        rowspan = bootstraps.length + 1;
        row = row + '<tr><th rowspan=' + rowspan + '>Bootstraps</th>' +
                '<th>' + $('#bootstrap_name').text() + '</th>' + 
                '<th colspan=3>' + $('#bootstrap_path').text() + '</th>' + 
                '<th colspan=2>' + $('#bootstrap_args').text() + '</th></tr>';
        for (j in bootstraps) {
            row = row + '<tr><td>' + bootstraps[j]['name'] +
                    '</td><td colspan=3>' + bootstraps[j]['path'] +
                    '</td><td colspan=2>' + bootstraps[j]['args'] +
                    '</td></tr>';
        }

        // job steps
        rowspan = steps.length + 1;
        row = row + '<tr><th rowspan=' + rowspan + '>Steps</th>' + 
                '<th>' + $('#jobstep_name').text() + '</th>' + 
                '<th>' + $('#jobstep_state').text() + '</th>' + 
                '<th>' + $('#jobstep_jar').text() + '</th>' + 
                '<th>' + $('#jobstep_args').text() + '</th>' + 
                '<th>' + $('#jobstep_startdate').text() + '</th>' + 
                '<th>' + $('#jobstep_enddate').text() + '</th></tr>';
        for (j in steps) {
            row = row + '<tr><td>' + steps[j]['name'] + '</td><td>' + 
                    steps[j]['state'] + '</td><td>' + 
                    steps[j]['jar'] + '</td><td>' + 
                    steps[j]['args'] + '</td><td>' + 
                    steps[j]['startdatetime'] + '</td><td>' + 
                    steps[j]['enddatetime'] + '</td></tr>';
        }

        $('#jobflow_list tbody').append(row);
    }

    return true;
}

function append_logfile_table(response) {
    var name, a_tag, row;
    var bucket_name = response['bucket_name'];
    var keys = response['keys'];
    for (i in keys) {
        name = keys[i]['name'];
        a_tag = '<a target="_blank" class="btn btn-small" href="' +
                window.location.href + '?type=download&bucket=' +
                bucket_name + '&key=' + name +
                '" title="Download" alt="Download"><i class="icon-download"></i></a>';
        row = '<tr><td>' + a_tag + '</td><td>' + name + '</td><td>'
                + keys[i]['size'] + '</td></tr>';
        $('#logfile tbody').append(row);
    }
    return true;
}
