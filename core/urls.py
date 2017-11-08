from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^sol_users/$', views.list_sol_users, name='sol_users'),
    url(r'^create_user/$', views.create_user, name='create_user'),
    url(r'^active_directory/$', views.active_directory_configuration, name='active_directory'),
    url(r'^openvpn_configuration/$', views.openvpn_configuration, name="openvpn_configuration"),
    url(r'^change_user_status/(?P<username>[\w-]+)/$', views.change_user_status, name="change_user_status"),
    url(r'^delete_user/(?P<username>[\w-]+)/$', views.delete_user, name="delete_user"),
    url(r'^modify_user/(?P<username>[\w-]+)/$', views.list_active_directory_group, name="modify_user"),
    url(r'^add_remove_ad_group/(?P<username>[\w-]+)/(?P<add_group>[\w-]+)/$', views.add_remove_ad_group,
        name="add_remove_ad_group"),
]