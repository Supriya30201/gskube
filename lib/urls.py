from django.conf.urls import url
from django.conf.urls import include
from . import views


urlpatterns = [
    url(r'^create_project/$', views.create_project, name='create_project'),
    url(r'^delete_project/', include([
        url(r'^$', views.delete_project, name="delete_project"),
        url(r'^(?P<project_id>[\w\d-]+)/$', views.delete_project, name="delete_project")
    ])),
    url(r'^project_member/', include([
        url(r'^$', views.project_member_management, name="project_member"),
        url(r'^(?P<project_id>[\w\d-]+)/$', views.project_member_management, name="project_member"),
        url(r'^(?P<user_id>[\w\d,-]+)/(?P<add>[\w\d,-]+)/$', views.project_member_management,
            name="project_member")
    ])),
    url(r'^load_hypervisor_projects/$', views.load_hypervisor_projects, name='load_hypervisor_projects'),
    url(r'^mark_project_selection/$', views.mark_project_selection, name='mark_project_selection'),
    url(r'^manage_instances/$', views.manage_instances, name='manage_instances'),
    url(r'^create_instance/$', views.create_instance, name='create_instance'),
    url(r'hypervisor_preference/', include([
        url(r'^$', views.hypervisor_preference, name="hypervisor_preference"),
        url(r'^(?P<host>[\w\d._-]+)/$', views.hypervisor_preference, name="hypervisor_preference")
    ])),
    url(r'instance_request/$', views.instance_request, name="instance_request"),
    url(r'instance_action/(?P<instance_id>[\w\d._-]+)/(?P<action>[\w]+)/$', views.instance_action,
        name="instance_action"),
    url(r'^extend_expiry/$', views.get_instances_for_extend_expiry, name="extend_expiry"),
    url(r'^manage_quota/', include([
        url(r'^$', views.manage_quota, name="manage_quota"),
        url(r'^(?P<project_id>[\w\d-]+)/$', views.manage_quota, name="manage_quota")
    ])),
]
