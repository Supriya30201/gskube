from django.conf.urls import url
from django.conf.urls import include
from . import views


urlpatterns = [
    url(r'^create_project/$', views.create_project, name='create_project'),
    url(r'^delete_project/', include([
        url(r'^$', views.delete_project, name="delete_project"),
        url(r'^(?P<project_id>[\w\d-]+)/$', views.delete_project, name="delete_project")
    ])),
    url(r'^delete_project/(?P<project_id>[\w\d.-]+)/$', views.delete_project, name='delete_project'),
    url(r'^load_hypervisor_projects/$', views.load_hypervisor_projects, name='load_hypervisor_projects'),
    url(r'^mark_project_selection/$', views.mark_project_selection, name='mark_project_selection'),


]
