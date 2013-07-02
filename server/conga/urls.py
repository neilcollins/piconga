from django.conf.urls import patterns, url

from conga import views
from conga import rest

urlpatterns = patterns('',
    # GUI URLs
    url(r'^$', views.index, name='index'),
    url(r'^signin', views.signin, name='signin'),
    url(r'^signout', views.signout, name='signout'),
    url(r'^main', views.main, name='main'),
    url(r'^error', views.error, name='error'),

    # JSON URLs - done in a reasonably RESTful way
    url(r'^user/(.*)', rest.user, name='user'),
    url(r'^status', rest.status, name='status'),
)
