$(function() {
    $('#show_aws_secret_btn').click(function() {
        toggle_show_or_hide($(this));
        $('#turned_letter_aws_secret').toggleClass('toggle-display');
        $('#actual_letter_aws_secret').toggleClass('toggle-display');
    });

    $('#show_ec2_keyfile_btn').click(function() {
        toggle_show_or_hide($(this));
        $('#turned_letter_ec2_keyfile').toggleClass('toggle-display');
        $('#actual_letter_ec2_keyfile').toggleClass('toggle-display');
    });

});

function toggle_show_or_hide(btn) {
    var btn_name = btn.text();
    if (btn_name == 'show') {
        btn.text('hide');
    } else {
        btn.text('show');
    }
}
