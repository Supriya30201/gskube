from . import models as sol_db
from core import constants
from datetime import datetime, timedelta


def get_hypervisors_with_soluser():
    user_credentials = sol_db.UserCredential.objects.filter(user=constants.HYPERVISOR_SOLUSER_NAME)
    if not user_credentials:
        return []
    return user_credentials.all()


def save_hypervisor_stats(hypervisor, timestamp, hypervisor_stats):
    db_hypervisor = sol_db.Hypervisor.objects.get(host=hypervisor)
    hypervisor_report = sol_db.HypervisorReport()
    hypervisor_report.hypervisor = db_hypervisor
    hypervisor_report.time = timestamp
    hypervisor_report.name = hypervisor_stats['name']
    hypervisor_report.type = hypervisor_stats[constants.TYPE]
    hypervisor_report.total_cpu = hypervisor_stats[constants.TOTAL_CPU]
    hypervisor_report.total_disk = hypervisor_stats[constants.TOTAL_DISK]
    hypervisor_report.total_memory = hypervisor_stats[constants.TOTAL_MEMORY]
    hypervisor_report.used_cpu = hypervisor_stats[constants.USED_CPU]
    hypervisor_report.used_disk = hypervisor_stats[constants.USED_DISK]
    hypervisor_report.used_memory = hypervisor_stats[constants.USED_MEMORY]
    hypervisor_report.save()


def save_project_stats(hypervisor, timestamp, project_id, project_stats):
    db_hypervisor = sol_db.Hypervisor.objects.get(host=hypervisor)
    db_project = sol_db.Project.objects.filter(hypervisor=db_hypervisor.id, project_id=project_id).first()
    project_report = sol_db.ProjectReport()
    project_report.project = db_project
    project_report.time = timestamp
    project_report.total_cpu = project_stats[constants.TOTAL_CPU]
    project_report.total_memory = project_stats[constants.TOTAL_MEMORY]
    project_report.used_cpu = project_stats[constants.USED_CPU]
    project_report.used_disk = project_stats[constants.USED_DISK]
    project_report.used_memory = project_stats[constants.USED_MEMORY]
    project_report.total_hours = project_stats[constants.TOTAL_HOURS]
    project_report.save()


def save_vm_stats(instance_id, timestamp, vm_stats):
    db_instance = sol_db.Instance.objects.filter(instance_id=instance_id)
    if db_instance:
        db_instance = db_instance.first()
    else:
        db_instance = None
    vm_report = sol_db.VMReport()
    vm_report.instance = db_instance
    vm_report.time = timestamp
    vm_report.total_cpu = vm_stats[constants.TOTAL_CPU]
    vm_report.total_memory = vm_stats[constants.TOTAL_MEMORY]
    vm_report.used_cpu = vm_stats[constants.USED_CPU]
    vm_report.used_disk = vm_stats[constants.USED_DISK]
    vm_report.used_memory = vm_stats[constants.USED_MEMORY]
    vm_report.total_hours = vm_stats[constants.TOTAL_HOURS]
    vm_report.save()


def get_start_time():
    start_date_data = sol_db.ProjectReport.objects.all().order_by('time')
    if start_date_data:
        start_date = start_date_data.first().time.replace(tzinfo=None)
    else:
        start_date = datetime.utcnow() - timedelta(days=10000)
    return start_date


def project_exist(project_id):
    project = sol_db.Project.objects.filter(project_id=project_id)
    if project:
        return True
    return False


def create_project(hypervisor, project_id, project_name):
    project = sol_db.Project()
    db_hypervisor = sol_db.Hypervisor.objects.get(host=hypervisor)
    project.hypervisor = db_hypervisor
    project.project_id = project_id
    project.name = project_name
    project.save()


def get_latest_time():
    latest_time = sol_db.HypervisorReport.objects.latest('time')
    if latest_time:
        return latest_time.time
    return None


def get_hypervisor_report(time):
    hypervisor_report = sol_db.HypervisorReport.objects.filter(time=time)
    if hypervisor_report:
        return hypervisor_report.all()
    return []


def get_project_report(time):
    project_report = sol_db.ProjectReport.objects.filter(time=time)
    if project_report:
        return project_report.all()
    return []


def get_vm_report(time):
    vm_report = sol_db.VMReport.objects.filter(time=time)
    if vm_report:
        return vm_report.all()
    return []