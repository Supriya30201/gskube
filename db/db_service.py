from . import models as sol_db
from core import constants
from core import services
from time import gmtime, strftime
from django.contrib.auth.models import User
from django.db.models import Q


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


def store_auth_ad(auth_active_directory):
    """
    Store auth ad method stores details of auth ad to database.
    :return:
    """
    update_configuration(constants.AUTH_AD_HOST, auth_active_directory[constants.AUTH_AD_HOST])
    update_configuration(constants.AUTH_AD_PORT, auth_active_directory[constants.AUTH_AD_PORT])
    update_configuration(constants.AUTH_AD_DN, auth_active_directory[constants.AUTH_AD_DN])
    update_configuration(constants.AUTH_AD_DOMAIN, auth_active_directory[constants.AUTH_AD_DOMAIN])
    update_configuration(constants.AUTH_AD_USERNAME, auth_active_directory[constants.AUTH_AD_USERNAME])
    update_configuration(constants.AUTH_AD_PASSWORD, auth_active_directory[constants.AUTH_AD_PASSWORD], True)


def store_local_ad(local_active_directory):
    """
    Store auth ad method stores details of auth ad to database.
    :return:
    """
    update_configuration(constants.LOCAL_AD_HOST, local_active_directory[constants.LOCAL_AD_HOST])
    update_configuration(constants.LOCAL_AD_PORT, local_active_directory[constants.LOCAL_AD_PORT])
    update_configuration(constants.LOCAL_AD_DN, local_active_directory[constants.LOCAL_AD_DN])
    update_configuration(constants.LOCAL_AD_DOMAIN, local_active_directory[constants.LOCAL_AD_DOMAIN])
    update_configuration(constants.LOCAL_AD_USERNAME, local_active_directory[constants.LOCAL_AD_USERNAME])
    update_configuration(constants.LOCAL_AD_PASSWORD, local_active_directory[constants.LOCAL_AD_PASSWORD], True)


def get_openvpn_configuration():
    # check if ad is configured.
    host = sol_db.ConfigMaster.objects.filter(key=constants.OPENVPN_HOST)
    if not host:
        return None

    host = host.first().value

    return {
        constants.OPENVPN_HOST: host,
        constants.OPENVPN_USERNAME: sol_db.ConfigMaster.objects.filter(key=constants.OPENVPN_USERNAME).first().value,
        constants.OPENVPN_PASSWORD: sol_db.ConfigMaster.objects.filter(key=constants.OPENVPN_PASSWORD).first().value,
        constants.OPENVPN_FOLDER_LOCATION: sol_db.ConfigMaster.objects.filter(
            key=constants.OPENVPN_FOLDER_LOCATION).first().value,
        constants.OPENVPN_TEMP_FOLDER_LOCATION: sol_db.ConfigMaster.objects.filter(
            key=constants.OPENVPN_TEMP_FOLDER_LOCATION).first().value,
    }


def save_openvpn_configuration(openvpn_config):
    update_configuration(constants.OPENVPN_HOST, openvpn_config[constants.OPENVPN_HOST])
    update_configuration(constants.OPENVPN_USERNAME, openvpn_config[constants.OPENVPN_USERNAME])
    update_configuration(constants.OPENVPN_PASSWORD, openvpn_config[constants.OPENVPN_PASSWORD], True)
    update_configuration(constants.OPENVPN_FOLDER_LOCATION, openvpn_config[constants.OPENVPN_FOLDER_LOCATION])
    update_configuration(constants.OPENVPN_TEMP_FOLDER_LOCATION, openvpn_config[constants.OPENVPN_TEMP_FOLDER_LOCATION])


def update_configuration(key, value, encode=False):
    """
    update configuration method can be used to update any key from configuration table.
    :param key:
    :param value:
    :return:
    """
    obj, _ = sol_db.ConfigMaster.objects.get_or_create(key=key)
    if encode:
        obj.value = services.encode(value)
    else:
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
    return user


def get_user(username=None):
    """
    Get the users details from SOL DB
    :param username:
    :return:
    """
    if not username:
        return sol_db.User.objects.filter(deleted=False).exclude(username=constants.HYPERVISOR_SOLUSER_NAME).all()

    user = sol_db.User.objects.filter(username=username)
    if user:
        return user.first()

    return None


def get_user_creds(hypervisor, username):
    db_hypervisor = sol_db.Hypervisor.objects.get(host=hypervisor)
    user_creds = sol_db.UserCredential.objects.filter(user=username, hypervisor=db_hypervisor.id)
    if user_creds:
        user_creds = user_creds.first()
        return user_creds.domain, user_creds.username, services.decode(user_creds.password)
    return None, None, None


def load_hypervisors():
    hypervisors = sol_db.Hypervisor.objects.all()
    hypervisor_list = []

    for hypervisor in hypervisors:
        if not hypervisor.deleted:
            hypervisor_list.append({
                'id': hypervisor.id,
                'host': hypervisor.host,
                'port': hypervisor.port,
                'protocol': hypervisor.protocol,
                'type': hypervisor.type,
            })

    return hypervisor_list


def delete_hypervisor(hypervisor_id):
    hypervisor = sol_db.Hypervisor.objects.get(id=hypervisor_id)
    hypervisor.deleted = True
    hypervisor.save()


def get_hypervisor(host=None, id=None):
    if id:
        return sol_db.Hypervisor.objects.get(id=id)
    return sol_db.Hypervisor.objects.get(host=host)


def get_hypervisor_of_user(username):
    db_user_hypervisors = sol_db.HypervisorUser.objects.filter(user=username)
    if not db_user_hypervisors:
        return []
    user_hypervisors = []
    db_user_hypervisors = db_user_hypervisors.all()
    for db_user_hypervisor in db_user_hypervisors:
        if not db_user_hypervisor.hypervisor.deleted:
            domain, username, password = get_user_creds(db_user_hypervisor.hypervisor.host, username)
            user_hypervisors.append({constants.TYPE: db_user_hypervisor.hypervisor.type,
                                     constants.PROTOCOL: db_user_hypervisor.hypervisor.protocol,
                                     constants.HOST: db_user_hypervisor.hypervisor.host,
                                     constants.PORT: db_user_hypervisor.hypervisor.port,
                                     constants.DOMAIN: domain, constants.USERNAME: username,
                                     constants.PASSWORD: password})
    return user_hypervisors


def create_hypervisor(hypervisor_type, protocol, host, port):
    hypervisor, _ = sol_db.Hypervisor.objects.get_or_create(type=hypervisor_type, host=str(host), protocol=protocol)
    hypervisor.port = port
    hypervisor.deleted = False
    hypervisor.save()
    return hypervisor


def save_user_credentials(user, hypervisor, domain, username, password):
    db_user = sol_db.User.objects.get(username=user)
    db_hypervisor = sol_db.Hypervisor.objects.get(host=hypervisor)
    user_creds, _ = sol_db.UserCredential.objects.get_or_create(user=db_user, hypervisor=db_hypervisor)
    user_creds.domain = domain
    user_creds.username = username
    user_creds.password = services.encode(password)
    user_creds.save()


def update_hypervisor_user_id(user, hypervisor, user_id):
    db_user = sol_db.User.objects.get(username=user)
    db_hypervisor = sol_db.Hypervisor.objects.get(host=hypervisor)
    hypervisor_user, _ = sol_db.HypervisorUser.objects.get_or_create(user=db_user, hypervisor=db_hypervisor)
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


def get_user_hypervisor_mapping(user_name):
    user_hypervisors = sol_db.HypervisorUser.objects.filter(user=user_name, has_access=True)
    if not user_hypervisors:
        return None
    user_hypervisors_list = []
    for user_hypervisor in user_hypervisors:
        user_hypervisors_list.append({
            'host': user_hypervisor.hypervisor.host,
            'user_id': user_hypervisor.hypervisor_user_id
        })
    return user_hypervisors_list


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
    name = project['name'] + "_" + user[constants.USERNAME] + "_" + name
    instance, _ = sol_db.Instance.objects.get_or_create(user=db_user, project=db_project, instance_name=name,
                                                     doc=strftime('%Y-%m-%d', gmtime()), doe=doe, flavor=flavor,
                                                     network=network, image=image)
    instance.requested = True
    instance.save()


def requested_instances(hypervisor, project):
    db_hypervisor = sol_db.Hypervisor.objects.get(host=hypervisor[constants.HOST])
    db_project = sol_db.Project.objects.filter(hypervisor=db_hypervisor.id, project_id=project['id'])
    if not db_project:
        return []
    db_project = db_project.first()
    requested_servers = sol_db.Instance.objects.filter(project=db_project, requested=True)
    if requested_servers:
        return requested_servers.all()

    return []


def remove_instance(request_id=None, instance_id=None):
    if request_id:
        instance_request = sol_db.Instance.objects.filter(id=request_id)
    else:
        instance_request = sol_db.Instance.objects.filter(instance_id=instance_id)

    if instance_request:
        instance_request.delete()


def update_requested_instance(request_id, instance_id=None, image=None, flavor=None, network=None, doe=None):
    instance_request = sol_db.Instance.objects.filter(id=request_id).first()
    if instance_id:
        instance_request.requested = False
        instance_request.instance_id = instance_id
    else:
        instance_request.image = image
        instance_request.flavor = flavor
        instance_request.network = network
        instance_request.doe = doe
    instance_request.save()


def get_created_instances(hypervisor=None, project=None, user=None, request_id=None, all_created=False,
                          instance_id=None):
    if instance_id:
        return sol_db.Instance.objects.get(instance_id=instance_id)
    if all_created:
        instances = sol_db.Instance.objects.filter(requested=False)
        if not instances:
            return []
        return instances.all()

    if request_id:
        return sol_db.Instance.objects.get(id=request_id)
    db_hypervisor = sol_db.Hypervisor.objects.get(host=hypervisor[constants.HOST])
    db_project = sol_db.Project.objects.filter(hypervisor=db_hypervisor.id, project_id=project['id'])
    if not db_project:
        return []
    db_project = db_project.first()
    instances = sol_db.Instance.objects.filter(project=db_project.id, user=user[constants.USERNAME], requested=False)
    if not instances:
        return []
    return instances.all()


def extend_expiry(instance_id, doe):
    instance = sol_db.Instance.objects.get(instance_id=instance_id)
    instance.doe = doe
    instance.save()


def set_default_project(hypervisor, user, project):
    db_hypervisor = sol_db.Hypervisor.objects.get(host=hypervisor)
    db_project, _ = sol_db.Project.objects.get_or_create(hypervisor=db_hypervisor, project_id=project['id'],
                                                         name=project['name'])
    db_user = sol_db.User.objects.get(username=user[constants.USERNAME])
    db_user.default_project = db_project
    db_user.save()
    return db_project


def remove_default_hypervisor(user):
    db_user = sol_db.User.objects.get(username=user[constants.USERNAME])
    db_user.default_project = None
    db_user.save()


def get_smtp_configuration():
    server = sol_db.ConfigMaster.objects.filter(key=constants.SMTP_SERVER)
    if not server:
        return {}

    server = server.first().value

    return {
        constants.SMTP_SERVER: server,
        constants.SMTP_PORT: sol_db.ConfigMaster.objects.filter(key=constants.SMTP_PORT).first().value,
        constants.SMTP_USERNAME: sol_db.ConfigMaster.objects.filter(key=constants.SMTP_USERNAME).first().value,
        constants.SMTP_PASSWORD: sol_db.ConfigMaster.objects.filter(key=constants.SMTP_PASSWORD).first().value
    }


def set_smtp_configuration(smtp_config):
    update_configuration(constants.SMTP_SERVER, smtp_config[constants.SMTP_SERVER])
    update_configuration(constants.SMTP_PORT, smtp_config[constants.SMTP_PORT])
    update_configuration(constants.SMTP_USERNAME, smtp_config[constants.SMTP_USERNAME])
    update_configuration(constants.SMTP_PASSWORD, smtp_config[constants.SMTP_PASSWORD], True)


def get_sol_user_id(hypervisor=None, hypervisor_id=None):
    if not hypervisor_id:
        db_hypervisor = sol_db.Hypervisor.objects.get(host=hypervisor)
        hypervisor_id = db_hypervisor.id

    hypervisor_user = sol_db.HypervisorUser.objects.filter(hypervisor=hypervisor_id,
                                                           user=constants.HYPERVISOR_SOLUSER_NAME).first()
    return hypervisor_user.hypervisor_user_id


def change_password(username, new_password):
    usr = User.objects.get(username=username)
    usr.set_password(new_password)
    usr.save()
