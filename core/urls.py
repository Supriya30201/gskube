from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^sol_users/$', views.list_sol_users, name='sol_users'),
]
