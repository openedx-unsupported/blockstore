""" API v1 URLs. """
from django.conf.urls import url
from . import views

UUID_PATTERN = r'(?P<pk>{0})'.format('-'.join(5*['[a-f0-9]+']))
NAME_PATTERN = r'(?P<name>[\w\d ]+)'

urlpatterns = [
    url(r'^tags/?', views.TagList.as_view(), name='tags'),
    url(r'^tag/new/?', views.TagNew.as_view(), name='tag.new'),
    url(r'^tag/{0}/?$'.format(NAME_PATTERN), views.TagGetOrUpdate.as_view(), name='tag'),
    url(r'^tag/{0}/units/?$'.format(NAME_PATTERN), views.TagUnits.as_view(), name='tag.units'),
    
    url(r'^units/?', views.UnitList.as_view(), name='units'),
    url(r'^unit/new/?', views.UnitNew.as_view(), name='unit.new'),
    url(r'^unit/{0}/?$'.format(UUID_PATTERN), views.UnitGetOrUpdate.as_view(), name='unit'),
    url(r'^unit/{0}/pathways/?$'.format(UUID_PATTERN), views.UnitPathways.as_view(), name='unit.pathways'),
    
    url(r'^pathways/?', views.PathwayList.as_view(), name='pathways'),
    url(r'^pathway/new/?', views.PathwayNew.as_view(), name='pathway.new'),
    url(r'^pathway/{0}/?$'.format(UUID_PATTERN), views.UnitGetOrUpdate.as_view(), name='pathway'),
]
