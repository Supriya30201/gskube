from django.db import models
from django.utils import timezone


class ConfigMaster(models.Model):
    """
        This model can be used to store any type of key-value pair data.
        Current plan is to store - Mail, AD, Open VPN etc configuration.
    """
    key = models.CharField(max_length=255, primary_key=True)
    value = models.CharField(max_length=255)


class Hypervisor(models.Model):
    """
        Hypervisor model will store the details of any hypervisor.
        We have specifically taken type column to decide the type of hypervisor (openstack, kvm etc.)
    """
    host = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    port = models.IntegerField(null=True, blank=True)
    protocol = models.CharField(max_length=50)


class Project(models.Model):
    """
        Project model will store the details of any project belongs to any hypervisor.
    """
    hypervisor = models.ForeignKey(Hypervisor, on_delete=models.DO_NOTHING, null=True)
    project_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)


class User(models.Model):
    """
        User model will store the details of each user who has access to SOL.
        if user gets deleted, we will not delete user from the SOL database.
        we'll just mark user deleted using deleted flag.
    """
    username = models.CharField(max_length=255, primary_key=True)
    full_name = models.CharField(max_length=255)
    email_id = models.CharField(max_length=255)
    default_project = models.ForeignKey(Project, on_delete=models.DO_NOTHING, null=True)
    active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)


class UserCredential(models.Model):
    """
        UserCredential model will be used to store any user's credentials of a hypervisor.
    """
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    hypervisor = models.ForeignKey(Hypervisor, on_delete=models.DO_NOTHING, null=True)
    domain = models.CharField(max_length=255, null=True)
    username = models.CharField(max_length=255, )
    password = models.CharField(max_length=255)


class Instance(models.Model):
    """
        Instance model will store details of each instance created using SOL.
    """
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING, null=True)
    instance_name = models.CharField(max_length=255)
    instance_id = models.CharField(max_length=255, blank=True, null=True)
    key = models.CharField(max_length=255, blank=True, null=True)
    doc = models.DateField()
    doe = models.DateField()
    flavor = models.CharField(max_length=255)
    network = models.CharField(max_length=255)
    image = models.CharField(max_length=255)
    requested = models.BooleanField(default=False)


class HypervisorUser(models.Model):
    """
        HypervisorUser model will be used to map access details of user.
    """
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    hypervisor = models.ForeignKey(Hypervisor, on_delete=models.DO_NOTHING, null=True)
    hypervisor_user_id = models.CharField(max_length=255, blank=True, null=True)
    has_access = models.BooleanField(default=False)


class HypervisorReport(models.Model):
    """
        HypervisorReport model will be used to store hypervisor level data of any hypervisor.
    """
    hypervisor = models.ForeignKey(Hypervisor, on_delete=models.DO_NOTHING, null=True)
    time = models.DateTimeField(default=timezone.now())
    name = models.CharField(max_length=250)
    type = models.CharField(max_length=250)
    total_memory = models.FloatField()
    total_cpu = models.FloatField()
    total_disk = models.FloatField()
    used_memory = models.FloatField()
    used_cpu = models.FloatField()
    used_disk = models.FloatField()


class ProjectReport(models.Model):
    """
        ProjectReport model will be used to store project level report of any hypervisor.
    """
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING, null=True)
    time = models.DateTimeField(default=timezone.now())
    total_hours = models.FloatField()
    total_memory = models.FloatField()
    total_cpu = models.FloatField()
    total_disk = models.FloatField()
    used_memory = models.FloatField()
    used_cpu = models.FloatField()
    used_disk = models.FloatField()


class UserReport(models.Model):
    """
        User Report model will be used to store user level report of a hypervisor.
    """
    time = models.DateTimeField(default=timezone.now())
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    project_report = models.ForeignKey(ProjectReport, on_delete=models.DO_NOTHING, null=True)
    total_memory = models.FloatField()
    total_cpu = models.FloatField()
    total_disk = models.FloatField()
    used_memory = models.FloatField()
    used_cpu = models.FloatField()
    used_disk = models.FloatField()


class VMReport(models.Model):
    """
        VMReport model will be used to store VM level report of a hypervisor.
    """
    time = models.DateTimeField(default=timezone.now())
    instance = models.ForeignKey(Instance, on_delete=models.DO_NOTHING, null=True)
    total_hours = models.FloatField()
    total_memory = models.FloatField()
    total_cpu = models.FloatField()
    total_disk = models.FloatField()
    used_memory = models.FloatField()
    used_cpu = models.FloatField()
    used_disk = models.FloatField()
