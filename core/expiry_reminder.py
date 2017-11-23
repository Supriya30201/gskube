from db import db_service
import datetime as datetime_obj
from datetime import datetime
import sol_email
import logging
from tabulate import tabulate

logging.basicConfig()
logger = logging.getLogger(__name__)


def reminder_expiry():
    logger.info('Running reminder expiry @ ' + str(datetime_obj.datetime.now()))
    try:
        instances = db_service.get_created_instances(all_created=True)
        if not instances:
            logger.info('Ending expiry reminder job as there are no instance')
            return

        for instance in instances:
            logger.info('Checking expiry details for : ' + instance.instance_name)
            expiry_date = datetime.strptime(str(instance.doe), '%Y-%m-%d')
            creation_date = datetime.strptime(str(instance.doc), '%Y-%m-%d')
            life_of_vm = abs(expiry_date - creation_date).days
            today_date = datetime.strptime(str(datetime_obj.date.today()), '%Y-%m-%d')
            remaining_days_to_expire = abs(expiry_date - today_date).days
            if remaining_days_to_expire == life_of_vm / 2 or remaining_days_to_expire <= 7:
                logger.debug("virtual machine '" + instance.instance_name + "' is going to expire in " +
                             str(remaining_days_to_expire) + " days. Hence sending reminder email.")
                subject = 'SOL (reminder): Instance ' + instance.instance_name + ' expiry alert (Remaining Day : ' + \
                          str(remaining_days_to_expire) + ')'
                vm_information_table = tabulate([["Instance Name : ", instance.instance_name],
                                                 ["Hypervisor : ", instance.project.hypervisor.host],
                                                 ["Project : ", instance.project.name],
                                                 ["Date of Creation:", instance.doc], ["Expiry Date:", instance.doe]])
                user = instance.user.username
                vm_user = db_service.get_user(user.strip())
                message = "Hi " + vm_user.full_name + ", \n\tYour virtual machine '" + instance.instance_name + \
                          "' is going to expire in " + str(remaining_days_to_expire) + \
                          " days.\nPlease check Virtual machine Details below,\n\n" + vm_information_table
                sol_email.send_mail(receiver=vm_user.email_id, subject=subject, message=message)
                logger.debug('Expiry alert sent successfully to ' + vm_user.email_id)
    except IOError as e:
        logger.error('Exception while executing Instance Expiry Reminder Job:' + e.message)
        logger.error(e)