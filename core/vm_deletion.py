import datetime as datetime_obj
from datetime import datetime
from db import db_service
from tabulate import tabulate
import sol_email
from lib import factory
import logging
from core import constants

logging.basicConfig()
logger = logging.getLogger(__name__)


def auto_vm_deletion():
    logger.info('Running delete expired instace @ ' + str(datetime_obj.datetime.now()))
    try:
        instances = db_service.get_created_instances(all_created=True)
        if not instances:
            logger.info("No instances found. Exiting vm deletion job.")
            return

        for instance in instances:
            logger.info('Checking expiry details for : ' + instance.instance_name)
            expiry_date = datetime.strptime(str(instance.doe), '%Y-%m-%d')
            today_date = datetime.strptime(str(datetime_obj.date.today()), '%Y-%m-%d')
            if expiry_date <= today_date:
                domain, username, password = db_service.get_user_creds(instance.project.hypervisor.host,
                                                                       constants.HYPERVISOR_SOLUSER_NAME)
                if not domain:
                    logger.error("Unable to delete instance : " + instance.instance_name +
                                 "as SOLUSER for hypervisor : " + instance.project.hypervisor.host + " Does not exist.")
                    continue
                hypervisor = {
                    constants.TYPE: instance.project.hypervisor.type,
                    constants.PROTOCOL: instance.project.hypervisor.protocol,
                    constants.HOST: instance.project.hypervisor.host,
                    constants.PORT: instance.project.hypervisor.port,
                    constants.DOMAIN: domain,
                    constants.USERNAME: username,
                    constants.PASSWORD: password,
                    constants.PROJECT_ID: instance.project.project_id
                }
                logger.debug(
                    "virtual machine '" + instance.instance_name + "' has expired. Hence, deleting the virtual machine.")
                adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
                adapter.generate_admin_auth()
                user_roles = adapter.get_user_roles_project(hypervisor[constants.PROJECT_ID])
                for user in user_roles:
                    if user[constants.USERNAME] == constants.HYPERVISOR_SOLUSER_NAME:
                        break
                else:
                    sol_user_id = db_service.get_sol_user_id(hypervisor[constants.HOST])
                    role_ids = []
                    roles = adapter.get_roles()
                    for role in roles:
                        role_ids.append(role[constants.ROLE_ID])
                    adapter.assign_roles(role_ids, sol_user_id, hypervisor[constants.PROJECT_ID])

                adapter.delete_instance(instance.instance_id)

                subject = 'SOL (deleted): Instance ' + instance.instance_name + ' has deleted.'
                vm_information_table = tabulate(
                    [["Instance Name : ", instance.instance_name],
                     ["Hypervisor : ", instance.project.hypervisor.host],
                     ["Project : ", instance.project.name],
                     ["Date of Creation:", instance.doc],
                     ["Expiry Date:", instance.doe],
                     ["Deleted by:", "Service Online"]])
                message = "Hi " + instance.user.full_name + ", \n\tYour virtual machine " + \
                          instance.instance_name + " has deleted. Please, check Virtual " \
                                                   "machine Details below,\n\n" + vm_information_table + \
                          "\n\nFor any issue, please get in touch with Administrator."
                sol_email.send_mail(receiver=instance.user.email_id, subject=subject, message=message)
                db_service.remove_instance(instance_id=instance.instance_id)
                logger.debug('Instance ' + instance.instance_name + ' has deleted')
    except Exception as e:
        logger.error('Exception while executing deleting expired instances job: ' + e.message)
        logger.error(e)
