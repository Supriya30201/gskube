from db import report_service
from core import constants
import logging
from lib import factory
from datetime import datetime, timedelta
from core import services

logging.basicConfig()
logger = logging.getLogger(__name__)


def load_hypervisors_with_soluser():
    hypervisor_users = report_service.get_hypervisors_with_soluser()
    hypervisors = []
    for hypervisor_user in hypervisor_users:
        if not hypervisor_user.hypervisor.deleted:
            hypervisors.append({
                constants.TYPE: hypervisor_user.hypervisor.type,
                constants.PROTOCOL: hypervisor_user.hypervisor.protocol,
                constants.HOST: hypervisor_user.hypervisor.host,
                constants.PORT: hypervisor_user.hypervisor.port,
                constants.DOMAIN: hypervisor_user.domain,
                constants.USERNAME: hypervisor_user.username,
                constants.PASSWORD: services.decode(hypervisor_user.password)
            })

    return hypervisors


def load_hypervisors_stats(adapter, timestamp):
    logger.debug("loading hypervisor level stats.")
    try:
        hypervisors_list = adapter.load_hypervisors()
        for hypervisor in hypervisors_list:
            hypervisor_detail = adapter.get_hypervisor(hypervisor)
            hypervisor_stats = {
                constants.TOTAL_CPU: hypervisor_detail.vcpus,
                constants.TOTAL_DISK: hypervisor_detail.local_gb,
                constants.TOTAL_MEMORY: hypervisor_detail.memory_mb,
                constants.USED_CPU: hypervisor_detail.vcpus_used,
                constants.USED_DISK: hypervisor_detail.local_gb_used,
                constants.USED_MEMORY: hypervisor_detail.memory_mb_used,
                'name': hypervisor_detail.id,
                constants.TYPE: hypervisor_detail.hypervisor_type
            }
            report_service.save_hypervisor_stats(hypervisor=adapter.host, timestamp=timestamp,
                                                 hypervisor_stats=hypervisor_stats)
    except Exception as e:
        logger.error(e.message)
        logger.error(e)


def load_tenant_wise_report(adapter, timestamp):
    logger.debug("generating tenant wise report.")
    start_date = report_service.get_start_time()
    end_date = datetime.utcnow()
    try:
        all_tenant_usage = adapter.get_detailed_usage(start_date, end_date)
        for tenant_usage in all_tenant_usage:
            tenant_quota = adapter.get_quota_details(tenant_usage.tenant_id)
            total_used_mem, total_used_disk, total_used_cpu = 0, 0, 0
            for server_usage in tenant_usage.server_usages:
                vm_report = {
                    constants.TOTAL_CPU: server_usage['vcpus'],
                    constants.TOTAL_MEMORY: server_usage['memory_mb'],
                    constants.USED_CPU: server_usage['vcpus'],
                    constants.USED_DISK: server_usage['local_gb'],
                    constants.USED_MEMORY: server_usage['memory_mb'],
                    constants.TOTAL_HOURS: server_usage['hours']
                }
                total_used_cpu += int(server_usage['vcpus'])
                total_used_disk += int(server_usage['local_gb'])
                total_used_mem += int(server_usage['memory_mb'])
                report_service.save_vm_stats(server_usage['instance_id'], timestamp, adapter.host,
                                             tenant_usage.tenant_id, vm_report)
            project_report = {
                constants.TOTAL_CPU: tenant_quota.cores,
                constants.TOTAL_MEMORY: tenant_quota.ram,
                constants.USED_CPU: total_used_cpu,
                constants.USED_DISK: total_used_disk,
                constants.USED_MEMORY: total_used_mem,
                constants.TOTAL_HOURS: tenant_usage.total_hours
            }
            if not report_service.project_exist(tenant_usage.tenant_id):
                project = adapter.get_project(tenant_usage.tenant_id)
                report_service.create_project(adapter.host, tenant_usage.tenant_id, project['project_name'])
            report_service.save_project_stats(adapter.host, timestamp, tenant_usage.tenant_id, project_report)

    except Exception as e:
        logger.error(e.message)
        logger.error(e)


def load_report_data():
    logger.debug("Getting report data from all hypervisors.")

    hypervisors = load_hypervisors_with_soluser()
    timestamp = datetime.utcnow()
    for hypervisor in hypervisors:
        adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
        adapter.generate_admin_auth()
        load_hypervisors_stats(adapter, timestamp)
        load_tenant_wise_report(adapter, timestamp)


def generate_report():
    logger.debug("Executing retrive_reports method")
    reports_dict = {}
    time = report_service.get_latest_time()
    hypervisors_report = report_service.get_hypervisor_report(time)
    reports_dict["hypervisor"] = []
    for hypervisor_report in hypervisors_report:
        if hypervisor_report.total_cpu < hypervisor_report.used_cpu:
            hypervisor_report.total_cpu = hypervisor_report.used_cpu
        reports_dict["hypervisor"].append(
            {str(hypervisor_report.name): {"total_cpu": hypervisor_report.total_cpu,
                                           "used_cpu": hypervisor_report.used_cpu,
                                           "total_memory": hypervisor_report.total_memory,
                                           "used_memory": hypervisor_report.used_memory,
                                           "total_disk": hypervisor_report.total_disk,
                                           "used_disk": hypervisor_report.used_disk}})
    projects_report = report_service.get_project_report(time)
    reports_dict["Projects"] = []
    for project_report in projects_report:
        reports_dict["Projects"].append(
            {str(project_report.project.name): {"total_cpu": project_report.total_cpu,
                                                "used_cpu": project_report.used_cpu,
                                                "total_memory": project_report.total_memory,
                                                "used_memory": project_report.used_memory,
                                                "total_disk": project_report.total_disk,
                                                "used_disk": project_report.used_disk}})
    vms_report = report_service.get_vm_report(time)
    reports_dict["VMS"] = []
    for vm_report in vms_report:
        if vm_report.instance:
            key = str(vm_report.instance.instance_name)
            user = str(vm_report.instance.user.username)
        else:
            key, project, user = "-", "-", "-"
        reports_dict["VMS"].append(
            {key: {"total_cpu": vm_report.total_cpu, "used_cpu": vm_report.used_cpu,
                   "total_memory": vm_report.total_memory, "used_memory": vm_report.used_memory,
                   "total_disk": vm_report.total_disk, "used_disk": vm_report.used_disk,
                   "Project": str(vm_report.project.name), "user": user}})
    return reports_dict
