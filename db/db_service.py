from . import models as sol_db
from core import constants
from core import services
from time import gmtime, strftime


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
    # store user details in db
    user, _ = sol_db.User.objects.get_or_create(username=user_detail[constants.USERNAME],
                                                full_name=user_detail[constants.USER_FULL_NAME],
                                                email_id=user_detail[constants.USER_EMAIL])
    # change the flag true i.e user is in activated state
    user.active = True
    user.deleted = False
    user.save()
    return user


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


def get_user(username=None):
    """
    Get the users details from SOL DB
    :param username:
    :return:
    """
    if not username:
        return sol_db.User.objects.filter(deleted=False, active=True).all()

    user = sol_db.User.objects.filter(username=username)
    if user:
        return user.first()

    return None


def load_hypervisors():
    hypervisors = sol_db.Hypervisor.objects.all()
    hypervisor_list = []

    user = sol_db.User.objects.filter(username=constants.HYPERVISOR_SOLUSER_NAME)
    if user:
        user = user.first()

    for hypervisor in hypervisors:
        superuser_created = False
        if user:
            hypervisor_user = sol_db.HypervisorUser.objects.filter(user=user.username, hypervisor=hypervisor.id)
            if hypervisor_user:
                superuser_created = True

        hypervisor_list.append({
            'id': hypervisor.id,
            'host': hypervisor.host,
            'port': hypervisor.port,
            'protocol': hypervisor.protocol,
            'type': hypervisor.type,
            'has_superuser': superuser_created
        })

    return hypervisor_list


def get_hypervisor(host):
    return sol_db.Hypervisor.objects.get(host=host)


def get_hypervisor_of_user(username):
    hypervisors = sol_db.HypervisorUser.objects.filter(user=username)
    if not hypervisors:
        return []
    user_hypervisors = []
    hypervisors = hypervisors.all()
    for hypervisor in hypervisors:
        user_hypervisors.append({constants.TYPE: hypervisor.hypervisor.type,
                                 constants.PROTOCOL: hypervisor.hypervisor.protocol,
                                 constants.HOST: hypervisor.hypervisor.host,
                                 constants.PORT: hypervisor.hypervisor.port})
    return user_hypervisors


def create_hypervisor(hypervisor_type, protocol, host, port):
    hypervisor, _ = sol_db.Hypervisor.objects.get_or_create(type=hypervisor_type, host=str(host), protocol=protocol)
    hypervisor.port = port
    hypervisor.save()
    return hypervisor


def save_user_credentials(user, hypervisor, domain, username, password):
    user_creds, _ = sol_db.UserCredential.objects.get_or_create(user=user, hypervisor=hypervisor)
    user_creds.domain = domain
    user_creds.username = username
    user_creds.password = password
    user_creds.save()


def update_hypervisor_user_id(user, hypervisor, user_id):
    hypervisor_user, _ = sol_db.HypervisorUser.objects.get_or_create(user=user, hypervisor=hypervisor)
    hypervisor_user.hypervisor_user_id = user_id
    hypervisor_user.save()


def get_hypervisor_users(hypervisor_id):
    users = sol_db.HypervisorUser.objects.filter(hypervisor=hypervisor_id, has_access=True)
    if not users:
        return None
    users = users.all()
    hypervisor_users = []
    for user in users:
        hypervisor_users.append({
            'username': user.user.username,
            'full_name': user.user.full_name
        })

    return hypervisor_users


def set_hypervisor_user_access(user_name, hypervisor_id, access=True):
    user = get_user(user_name)
    hypervisor = sol_db.Hypervisor.objects.get(id=hypervisor_id)
    hypervisor_user, _ = sol_db.HypervisorUser.objects.get_or_create(user=user, hypervisor=hypervisor)
    hypervisor_user.has_access = access
    hypervisor_user.save()


def save_instance_request(hypervisor, project, user, name, image, network, flavor, doe):
    db_user = sol_db.User.objects.get(username=user[constants.USERNAME])
    db_hypervisor = sol_db.Hypervisor.objects.get(host=hypervisor[constants.HOST])
    db_project, _ = sol_db.Project.objects.get_or_create(hypervisor=db_hypervisor, project_id=project['id'],
                                                         name=project['name'])
    name = hypervisor[constants.HOST] + "_" + project['name'] + "_" + name
    instance, _ = sol_db.Instance.objects.get_or_create(user=db_user, project=db_project, instance_name=name,
                                                     doc=strftime('%Y-%m-%d', gmtime()), doe=doe, flavor=flavor,
                                                     network=network, image=image)
    instance.requested = True
    instance.save()