from . import models as sol_db
from core import constants
from core import services


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
        constants.AUTH_AD_DN: sol_db.ConfigMaster.objects.filter(key=constants.AUTH_AD_DN).first().value,
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
        constants.LOCAL_AD_DN: sol_db.ConfigMaster.objects.filter(key=constants.LOCAL_AD_DN).first().value,
        constants.LOCAL_AD_DOMAIN: sol_db.ConfigMaster.objects.filter(key=constants.LOCAL_AD_DOMAIN).first().value,
        constants.LOCAL_AD_USERNAME: sol_db.ConfigMaster.objects.filter(key=constants.LOCAL_AD_USERNAME).first().value,
        constants.LOCAL_AD_PASSWORD: sol_db.ConfigMaster.objects.filter(key=constants.LOCAL_AD_PASSWORD).first().value,
        }


def store_auth_ad(host, port, dn, domain, username, password):
    """
    Store auth ad method stores details of auth ad to database.
    :return:
    """
    update_configuration(constants.AUTH_AD_HOST, host)
    update_configuration(constants.AUTH_AD_PORT, port)
    update_configuration(constants.AUTH_AD_DN, dn)
    update_configuration(constants.AUTH_AD_DOMAIN, domain)
    update_configuration(constants.AUTH_AD_USERNAME, username)
    update_configuration(constants.AUTH_AD_PASSWORD, services.encode(password))

    return {constants.AUTH_AD_HOST: host, constants.AUTH_AD_PORT: port, constants.AUTH_AD_DN: dn,
            constants.AUTH_AD_DOMAIN: domain, constants.AUTH_AD_USERNAME: username,
            constants.AUTH_AD_PASSWORD: services.encode(password)}


def store_local_ad(host, port, dn, domain, username, password):
    """
    Store auth ad method stores details of auth ad to database.
    :return:
    """
    update_configuration(constants.LOCAL_AD_HOST, host)
    update_configuration(constants.LOCAL_AD_PORT, port)
    update_configuration(constants.LOCAL_AD_DN, dn)
    update_configuration(constants.LOCAL_AD_DOMAIN, domain)
    update_configuration(constants.LOCAL_AD_USERNAME, username)
    update_configuration(constants.LOCAL_AD_PASSWORD, services.encode(password))

    return {constants.LOCAL_AD_HOST: host, constants.LOCAL_AD_PORT: port, constants.LOCAL_AD_DN: dn,
            constants.LOCAL_AD_DOMAIN: domain, constants.LOCAL_AD_USERNAME: username,
            constants.LOCAL_AD_PASSWORD: services.encode(password)}


def get_openvpn_configuration():
    # check if ad is configured.
    host = sol_db.ConfigMaster.objects.filter(key=constants.AUTH_AD_HOST)
    if not host:
        return None

    host = host.first().value

    return {
        constants.AUTH_AD_HOST: host,
        constants.AUTH_AD_PORT: sol_db.ConfigMaster.objects.filter(key=constants.AUTH_AD_PORT).first().value,
        constants.AUTH_AD_DN: sol_db.ConfigMaster.objects.filter(key=constants.AUTH_AD_DN).first().value,
        constants.AUTH_AD_DOMAIN: sol_db.ConfigMaster.objects.filter(key=constants.AUTH_AD_DOMAIN).first().value,
        constants.AUTH_AD_USERNAME: sol_db.ConfigMaster.objects.filter(key=constants.AUTH_AD_USERNAME).first().value,
        constants.AUTH_AD_PASSWORD: sol_db.ConfigMaster.objects.filter(key=constants.AUTH_AD_PASSWORD).first().value,
    }


def update_configuration(key, value):
    """
    update configuration method can be used to update any key from configuration table.
    :param key:
    :param value:
    :return:
    """
    obj, _ = sol_db.ConfigMaster.objects.get_or_create(key=key)
    obj.value = value
    obj.save()


def create_user(user_detail):
    """
    Store the users deails in SOL DB
    :param user_detail: username, user_full_name, email
    :return:
    """
    #store user details in db
    user, _ = sol_db.User.objects.get_or_create(username=user_detail[constants.USERNAME],
                                                full_name=user_detail[constants.USER_FULL_NAME],
                                                email_id=user_detail[constants.USER_EMAIL])
    #change the flag true i.e user is in activated state
    user.active = True
    user.deleted = False
    user.save()


def change_user_status(username):
    """
    Change the user's flag (Activate/Deactivate)
    :param username:
    :return:
    """
    user = sol_db.User.objects.get(username=username)
    user.active = not user.active
    user.save()


def delete_user(username):
    """
    Delete the user from SOL DB by changing the deleted flag to True
    :param username:
    :return:
    """
    user = sol_db.User.objects.get(username=username)
    user.deleted = True
    user.save()


def get_user(username):
    """
    Get the users details from SOL DB
    :param username:
    :return:
    """
    return sol_db.User.objects.get(username=username)

