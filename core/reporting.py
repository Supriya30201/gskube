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
            project_report = {
                constants.TOTAL_CPU: tenant_quota.cores,
                constants.TOTAL_DISK: tenant_quota.local_gb,
                constants.TOTAL_MEMORY: tenant_quota.ram,
                constants.USED_CPU: tenant_usage.total_vcpus_usage / tenant_usage.total_hours,
                constants.USED_DISK: (tenant_usage.total_local_gb_usage / tenant_usage.total_hours),
                constants.USED_MEMORY: tenant_usage.total_memory_mb_usage / tenant_usage.total_hours,
                constants.TOTAL_HOURS: tenant_usage.total_hours
            }
            report_service.save_project_stats(adapter.host, timestamp, tenant_usage.tenant_id, project_report)

            for server_usage in tenant_usage.server_usages:
                vm_report = {
                    constants.TOTAL_CPU: server_usage['vcpus'],
                    constants.TOTAL_DISK: server_usage['local_gb'],
                    constants.TOTAL_MEMORY: server_usage['memory_mb'],
                    constants.USED_CPU: server_usage['vcpus'],
                    constants.USED_DISK: server_usage['local_gb'],
                    constants.USED_MEMORY: server_usage['memory_mb'],
                    constants.TOTAL_HOURS: server_usage['hours']
                }
                report_service.save_vm_stats(server_usage['instance_id'], timestamp, vm_report)
    except Exception as e:
        logger.error(e.message)
        logger.error(e)


def load_report_data():
    logger.debug("Getting report data from all hypervisors.")

    hypervisors = load_hypervisors_with_soluser()
    timestamp = datetime.utcnow()
    for hypervisor in hypervisors:
        adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
        load_hypervisors_stats(adapter, timestamp)