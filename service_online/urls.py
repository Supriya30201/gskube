"""service_online URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.conf.urls import include
from core import views as core_views
from core import reporting
from core import expiry_reminder
from core import vm_deletion
import socket

urlpatterns = [
    # Login URL
    url(r'^$', core_views.login, name='login'),
    url(r'^logout$', core_views.logout, name='logout'),
    url(r'^dashboard/$', core_views.load_dashboard, name='dashboard'),
    url(r'^django_admin/', include('core.urls')),
    url(r'^hypervisor_admin/', include('lib.urls')),
]

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 47200))
except socket.error:
    print("!!!scheduler already started, DO NOTHING")
else:
    print("Scheduling all jobs.")
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(reporting.load_report_data, 'interval', minutes=59)
    scheduler.add_job(expiry_reminder.reminder_expiry, 'cron', day="*", hour=6, minute=0)
    scheduler.add_job(vm_deletion.auto_vm_deletion, 'cron', day="*", hour=0, minute=1)
    scheduler.start()
