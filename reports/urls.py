from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^builds/([0-9]+)/$', views.builds, name='builds'),
    url(r'^tests/([0-9]+)/$', views.tests, name='tests'),
    url(r'^logs/([0-9]+)/$', views.logs, name='logs'),
]
