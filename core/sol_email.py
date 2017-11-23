from db import db_service
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from core import constants

logging.basicConfig()
logger = logging.getLogger(__name__)


def is_email_configured():
    if db_service.get_smtp_configuration():
        return True

    logger.error('Email configuration not found.')
    return False


# This method is for sending a mail
def send_mail(receiver, subject, message):
    """

    to send mail
    :param receiver: receiver mail
    :param subject: subject of mail
    :param message: message body of the mail
    """
    try:
        if not is_email_configured():
            logger.error("Unable receiver find Email Configuration, Please contact Administrator.")
            logger.error('Not sending email : \n receiver : ' + receiver + '\nSubject : ' + subject + '\nMessage : '
                         + message)
            return
        email_config = db_service.get_smtp_configuration()
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = email_config[constants.SMTP_USERNAME]
        msg['To'] = receiver
        body = message + "\n\n\n This is system generated email, please do not reply receiver this email."
        msg.attach(MIMEMultipart("alternative", None, [MIMEText(body)]))

        logger.info("Connecting receiver email server.")
        mail = smtplib.SMTP(email_config[constants.SMTP_SERVER], str(email_config[constants.SMTP_PORT]))
        logger.info("Connection receiver email server successful.")

        mail.ehlo()
        mail.starttls()
        mail.login(email_config[constants.SMTP_USERNAME], email_config[constants.SMTP_PASSWORD])
        logger.info("Email auth successful, sending mail receiver " + receiver)

        mail.sendmail(email_config[constants.SMTP_USERNAME], receiver.split(","), msg.as_string())
        mail.quit()
        logger.debug('Email sent successfully receiver "' + receiver + '"')
        logger.info('Email Details \nreceiver : ' + receiver + '\nSubject : ' + subject +
                    '\nmessage : ' + body)

    except Exception as e:
        logger.error('Exception while sending email : ' + str(e))
