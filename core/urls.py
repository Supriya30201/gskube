from django.conf.urls import url
from django.conf.urls import include
from . import views


urlpatterns = [
    url(r'^sol_users/$', views.list_sol_users, name='sol_users'),
    url(r'^create_user/$', views.create_user, name='create_user'),
    url(r'^active_directory/$', views.active_directory_configuration, name='active_directory'),
    url(r'^openvpn_configuration/$', views.openvpn_configuration, name="openvpn_configuration"),
    url(r'^generate_openvpn_certificate/', include([
        url(r'^$', views.generate_openvpn_certificate, name="generate_openvpn_certificate"),
        url(r'^(?P<username>[\w\d-]+)/$', views.generate_openvpn_certificate, name="generate_openvpn_certificate")
    ])),
    url(r'^change_user_status/(?P<username>[\w\d-]+)/$', views.change_user_status, name="change_user_status"),
    url(r'^delete_user/(?P<username>[\w\d-]+)/$', views.delete_user, name="delete_user"),
    url(r'^modify_user/(?P<username>[\w\d-]+)/$', views.list_active_directory_group, name="modify_user"),
    url(r'^add_remove_ad_group/(?P<username>[\w\d-]+)/(?P<add_group>[\w-]+)/$', views.add_remove_ad_group,
        name="add_remove_ad_group"),
    url(r'^hypervisor_management/', include([
        url(r'^$', views.hypervisor_management, name='hypervisor_management'),
    ])),
    url(r'^create_hypervisor/$', views.create_hypervisor, name="create_hypervisor"),
    url(r'^load_hosts/$', views.load_hosts, name="load_hosts"),

    # url for getting list of user for any hypervisor, adding and removing user from hypervisor
    url(r'^assign_hypervisor/', include([
        url(r'^$', views.assign_hypervisor, name="add_hypervisor_user"),
        url(r'^(?P<hypervisor_id>[\d]+)/', include([
            url(r'^$', views.assign_hypervisor, name="load_hypervisor_user"),
            url(r'^(?P<username>[\w\d-]+)/$', views.assign_hypervisor, name="remove_hypervisor_user")
        ])),
    ])),
    url(r'^load_projects/', include([
        url(r'^$', views.load_projects, name='load_projects'),
        url(r'^(?P<host>[\w\d.]+)/$', views.load_projects, name='hypervisor_login')
    ])),
    url(r'^smtp_configuration/$', views.smtp_configuration, name='smtp_configuration'),
    url(r'^change_password/$', views.change_password, name="change_password"),
    url(r'^hypervisor_user_management/', include([
        url(r'^(?P<username>[\w\d-]+)/$', views.hypervisor_user_management, name="hypervisor_user_management")
    ])),
    url(r'^create_hypervisor_user/', include([
        url('^$', views.hypervisor_user_management, name="create_hypervisor_user"),
        url('(P<host>[\w\d.-_]+)/(?P<username>[\w\d-]+)/$', views.hypervisor_user_management, name="create_hypervisor_user"),
    ])),
    url(r'^generate_report/$', views.get_report, name="generate_report"),
]
