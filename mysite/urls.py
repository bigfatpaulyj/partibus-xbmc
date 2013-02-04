# This also imports the include function
from django.conf.urls.defaults import *
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^createaccount/$', 'logic.views.createaccount'),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^$', 'logic.views.filelist'),
                       url(r'^editserver/', 'logic.views.editserver'),
                       url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
                       url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': 'logout.html'}),

)

urlpatterns += staticfiles_urlpatterns()
print urlpatterns
