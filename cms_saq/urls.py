from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^submit/$', 'cms_saq.views.submit', name='cms_saq_submit'),
    url(r'^scores/$', 'cms_saq.views.scores', name='cms_saq_scores'),
)

