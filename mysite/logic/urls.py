from django.conf.urls.defaults import *
from django.views.generic import DetailView, ListView


urlpatterns = patterns('',
    url(r'^filelist/$', 'logic.views.filelist'),
    url(r'^createaccount/$', 'logic.views.createaccount'),
  
)
