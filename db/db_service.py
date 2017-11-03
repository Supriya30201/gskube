from . import models as sol_db
from core import constants


def get_auth_ad():
    """
    getter for auth ad
    :return:
    """
    # check if ad is configured.
    host = sol_db.ConfigMaster.objects.filter(key=constants.AUTH_AD_HOST)
    if not host:
        return None

    host = host.first().value

    return {
        constants.AUTH_AD_HOST: host,
        constants.AUTH_AD_PORT: sol_db.ConfigMaster.objects.filter(key=constants.AUTH_AD_PORT).first().value,
        constants.AUTH_AD_DOMAIN: sol_db.ConfigMaster.objects.filter(key=constants.AUTH_AD_DOMAIN).first().value,
        constants.AUTH_AD_USERNAME: sol_db.ConfigMaster.objects.filter(key=constants.AUTH_AD_USERNAME).first().value,
        constants.AUTH_AD_PASSWORD: sol_db.ConfigMaster.objects.filter(key=constants.AUTH_AD_PASSWORD).first().value,
        }


def get_local_ad():
    """
    local AD getter
    :return:
    """
    # check if local AD configured.
    host = sol_db.ConfigMaster.objects.filter(key=constants.LOCAL_AD_HOST)
    if not host:
        return None

    host = host.first().value

    return {
        constants.LOCAL_AD_HOST: host,
        constants.LOCAL_AD_PORT: sol_db.ConfigMaster.objects.filter(key=constants.LOCAL_AD_PORT).first().value,
        constants.LOCAL_AD_DOMAIN: sol_db.ConfigMaster.objects.filter(key=constants.LOCAL_AD_DOMAIN).first().value,
        constants.LOCAL_AD_USERNAME: sol_db.ConfigMaster.objects.filter(key=constants.LOCAL_AD_USERNAME).first().value,
        constants.LOCAL_AD_PASSWORD: sol_db.ConfigMaster.objects.filter(key=constants.LOCAL_AD_PASSWORD).first().value,
        }
