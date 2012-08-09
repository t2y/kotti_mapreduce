$(function() {

    $('select[name="action_type"]').change(function() {
        var selected = $(this).attr('value');
        console.log(selected);
        switch (selected) {
            case 'hadoop':
                set_default_path('s3n://elasticmapreduce/bootstrap-actions/configure-hadoop');
                enable_optional_args('--site-key-value io.file.buffer.size=65536');
                break;
            case 'daemon':
                set_default_path('s3n://elasticmapreduce/bootstrap-actions/configure-daemons');
                enable_optional_args('--namenode-opts=-XX:GCTimeRatio=19');
                break;
            case 'ganglia':
                set_default_path('s3n://elasticmapreduce/bootstrap-actions/install-ganglia');
                disable_optional_args();
                break;
            case 'memory':
                set_default_path('s3n://elasticmapreduce/bootstrap-actions/configurations/latest/memory-intensive');
                disable_optional_args();
                break;
            case 'runif':
                set_default_path('s3n://elasticmapreduce/bootstrap-actions/run-if');
                enable_optional_args('instance.isMaster=true echo Running on master node');
                break;
            case 'custom':
                set_default_path('s3n://');
                enable_optional_args('');
                break;
            default:
                set_default_path('');
                disable_optional_args();
                break;
        }
    });
    console.log('hello');
});

function set_default_path(value) {
    $('input[name="path_uri"]').val(value);
}

function enable_optional_args(value) {
    $('textarea[name="optional_args"]').removeAttr('disabled');
    if (value != undefined) {
        $('textarea[name="optional_args"]').val(value);
    }
}

function disable_optional_args() {
    $('textarea[name="optional_args"]').attr('value', '');
    $('textarea[name="optional_args"]').attr('disabled', 'disabled');
}
