from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('kotti_mapreduce')


def kotti_configure(settings):
    settings['kotti.includes'] += ' kotti_mapreduce.views'
    settings['kotti.available_types'] = settings['kotti.available_types'] \
        + ' kotti_mapreduce.resources.JobContainer' \
        + ' kotti_mapreduce.resources.EMRJobResource' \
        + ' kotti_mapreduce.resources.JobService' \
        + ' kotti_mapreduce.resources.JobFlow' \
        + ' kotti_mapreduce.resources.Bootstrap' \
        + ' kotti_mapreduce.resources.JobStep'
