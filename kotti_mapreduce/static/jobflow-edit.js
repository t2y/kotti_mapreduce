$(function() {

    for (var i=1; i<17; i++) {
        $('select[name="bootstrap' + i + '_id"]').change(function() {
            var cur_id = $(this).attr('name').replace(/bootstrap/, '').replace(/_id/, '');
            var next_id = Number(cur_id) + 1;
            if ($(this).attr('value') == '') {
                for (var j=next_id; j<17; j++) {
                    $('select[name="bootstrap' + j + '_id"]').attr('value', '');
                    $('select[name="bootstrap' + j + '_id"]').attr('disabled', 'disabled');
                }
            } else {
                $('select[name="bootstrap' + next_id + '_id"]').removeAttr('disabled');
            }
        });
    }

    // initialize
    disable_bootstraps();
});

function disable_bootstraps() {
    $('select[name="bootstrap2_id"]').attr('disabled', 'disabled');
    $('select[name="bootstrap3_id"]').attr('disabled', 'disabled');
    $('select[name="bootstrap4_id"]').attr('disabled', 'disabled');
    $('select[name="bootstrap5_id"]').attr('disabled', 'disabled');
    $('select[name="bootstrap6_id"]').attr('disabled', 'disabled');
    $('select[name="bootstrap7_id"]').attr('disabled', 'disabled');
    $('select[name="bootstrap8_id"]').attr('disabled', 'disabled');
    $('select[name="bootstrap9_id"]').attr('disabled', 'disabled');
    $('select[name="bootstrap10_id"]').attr('disabled', 'disabled');
    $('select[name="bootstrap11_id"]').attr('disabled', 'disabled');
    $('select[name="bootstrap12_id"]').attr('disabled', 'disabled');
    $('select[name="bootstrap13_id"]').attr('disabled', 'disabled');
    $('select[name="bootstrap14_id"]').attr('disabled', 'disabled');
    $('select[name="bootstrap15_id"]').attr('disabled', 'disabled');
    $('select[name="bootstrap16_id"]').attr('disabled', 'disabled');
}
