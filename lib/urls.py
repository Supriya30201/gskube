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
    url(r'^manage_instances/$', views.manage_instances, name='manage_instances'),
    url(r'^create_instance/$', views.create_instance, name='create_instance'),
    url(r'^hypervisor_preference/$', views.hypervisor_preference, name="hypervisor_preference"),
    url(r'hypervisor_preference_change/', include([
        url(r'^$', views.hypervisor_preference_change, name="hypervisor_preference_change"),
        url(r'^(?P<host>[\w\d._-]+)/$', views.hypervisor_preference_change, name="hypervisor_preference_host")
    ])),
    url(r'instance_request/$', views.instance_request, name="instance_request"),
    url(r'instance_action/(?P<instance_id>[\w\d._-]+)/(?P<action>[\w]+)/$', views.instance_action,
        name="instance_action"),
]
