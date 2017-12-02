from keystoneauth1.identity import v2
from keystoneauth1 import session as keystone_session
from keystoneclient.v2_0 import client as v2_client
from exception.openstack_exception import OpenstackException
from exception.openstack_session_exception import OpenstackSessionException
from keystoneclient.v3 import client as v3_client
from keystoneclient.auth.identity import v3
from core import constants
import logging

LOGGER = logging.getLogger(__name__)


# Unscoped Token using v2
def unscoped_login(protocol, host, port, username, password):
    LOGGER.info("Executing unscoped_login with args : " + str(protocol) + "\t" + str(host) + "\t" + str(port) + "\t" +
                str(username))
    try:
        url = protocol + "://" + host + ":" + port + "/v2.0"
        auth = v2.Password(username=username, password=password, auth_url=url)
        session = keystone_session.Session(auth=auth)
        client = v2_client.Client(session=session)
        token = client.session.get_token(auth)
        user_id = client.session.get_user_id(auth)
        return {'token': token, 'client': client, 'user_id': user_id}
    except Exception as e:
        raise OpenstackException(message="Exception while performing unscoped login : " + e.message, exception=e,
                                 logger=LOGGER)


# Uses:For User operations(create/delete/list users) and compute operations(create/delete/list/start/stop instance)
def scoped_login_v3(protocol, host, port, token, project_id):
    LOGGER.info("Executing scoped_login_v3 with args : " + str(protocol) + "\t" + str(host) + "\t" + str(port) + "\t" +
                str(token) + "\t" + str(project_id))
    try:
        url = protocol + "://" + host + ":" + port + "/v3"
        auth = v3.Token(auth_url=url, token=token, project_id=project_id)
        session = keystone_session.Session(auth=auth)
        connection = v3_client.Client(session=session)
        token = connection.session.get_token(auth)
        try:
            services = connection.services.list()
        except Exception as e:
            if 'You are not authorized to perform' in e.message:
                return {'client': connection, 'token': token}
            raise e
        endpoints = connection.endpoints.list(interface="public")
        endpoint_urls = []
        for service in services:
            for endpoint in endpoints:
                if endpoint.service_id == service.id:
                    endpoint_urls.append({
                        "endpoint_name": str(service.name),
                        "endpoint_url": str(endpoint.url)
                    })
                    break;

        return {'client': connection, 'token': token, 'endpoint_urls': endpoint_urls}
    except Exception as e:
        raise OpenstackException("Exception while performing scoped login : " + e.message, exception=e, logger=LOGGER)


def get_client(protocol, host, port, token):
    LOGGER.info("Executing get_client with args : " + str(protocol) + "\t" + str(host) + "\t" + str(port) + "\t" +
                str(token))
    try:
        url = protocol + "://" + host + ":" + port + "/v3"
        connection = v3_client.Client(endpoint=url, token=token)
        return connection
    except Exception as e:
        raise OpenstackSessionException(message="Exception while requesting client : " + e.message, exception=e,
                                        logger=LOGGER)


# List projects using v2 unscoped token
def list_projects(client, v2_api=True):
    LOGGER.info("Executing list_projects with args : " + str(v2_api))
    try:
        if v2_api:
            projects_list = client.tenants.list()
        else:
            projects_list = client.projects.list()
        return projects_list
    except Exception as e:
        raise OpenstackException(message="Exception while getting list of projects : " + e.message, exception=e,
                                 logger=LOGGER)


def get_user_roles(client, user_id, project_id):
    LOGGER.info("Executing get_user_roles with args : " + str(user_id) + "\t" + str(project_id))
    try:
        user_role_ids = []
        user_roles = []
        users_role_list = client.roles.list(user=user_id, project=project_id)

        for role in users_role_list:
            user_role_ids.append(role.id)
            user_roles.append(role.name)
        return user_roles, user_role_ids
    except Exception as e:
        raise OpenstackException(message="Exception while getting roles for specified project and user : " + e.message,
                                 exception=e, logger=LOGGER)


def is_admin(client, user_id, project_id):
    LOGGER.info("Executing is_admin with args : " + str(user_id) + "\t" + str(project_id))
    users_project_roles, _ = get_user_roles(client, user_id, project_id)
    for role in users_project_roles:
        if "admin" in role.lower():
            return True
    return False


def create_user(client, name, password, email, description, roles=None, project_id=None):
    LOGGER.info("Executing create_user with args : " + str(name) + "\t" + str(email) + "\t" + str(description) + "\t" +
                str(roles) + "\t" + str(project_id))
    try:
        new_user = client.users.create(name=name, description=description, password=password, email=email,
                                       project=project_id)
        if project_id:
            assign_roles(client, new_user.id, roles, project_id)
        return new_user.id
    except Exception as e:
        raise OpenstackException(message="Exception while creating user in openstack : " + e.message, exception=e,
                                 logger=LOGGER)


def delete_user(client, user_id):
    LOGGER.info("Executing assign_roles with args : " + str(user_id))
    try:
        client.users.delete(user=user_id)
    except Exception as e:
        raise OpenstackException(message="Exception while deleting user : " + e.message, exception=e, logger=LOGGER)


def get_roles(client):
    try:
        roles = client.roles.list()
        role_list = []
        for role in roles:
            role_list.append({
                constants.ROLE_ID: role.id,
                constants.ROLE_NAME: role.name
            })
        return role_list
    except Exception as e:
        raise OpenstackException(message="Exception while getting roles from openstack: " + e.message, exception=e,
                                 logger=LOGGER)


def assign_roles(client, user_id, roles, project_id):
    LOGGER.info("Executing assign_roles with args : " + str(user_id) + "\t" + str(roles) + "\t" + str(project_id))
    try:
        for role in roles:
            client.roles.grant(role=role, user=user_id, project=project_id)

    except Exception as e:
        raise OpenstackException(message="Exception while assigning role : " + e.message, exception=e, logger=LOGGER)


def revoke_roles(client, user_id, roles, project_id):
    LOGGER.info("Executing revoke_roles with args : " + str(user_id) + "\t" + str(roles) + "\t" + str(project_id))
    try:
        for role in roles:
            client.roles.revoke(role=role, user=user_id, project=project_id)
    except Exception as e:
        raise OpenstackException(message="Exception while revoking role : " + e.message, exception=e, logger=LOGGER)


def get_project(client, project_id):
    LOGGER.info("Executing get_project with args : " + str(project_id))
    try:
        project = client.projects.get(project=project_id)
        return {'project_id': project_id, 'project_name': project.name, 'project_description': project.description,
                'enabled': project.enabled, 'is_domain': project.is_domain, 'domain_id': project.domain_id,
                'parent_id': project.parent_id}
    except Exception as e:
        raise OpenstackException(message="Exception while getting project information : " + e.message, exception=e,
                                 logger=LOGGER)


def create_project(client, project_name, description, domain=None, project_id=None):
    """
    If project_id is passed, method will update project.
    :param client:
    :param domain:
    :param project_name:
    :param description:
    :param project_id:
    :return:
    """
    LOGGER.info("Executing create_project with args : " + str(project_name) + "\t" + str(description) + "\t" +
                str(domain) + "\t" + str(project_id))
    try:
        if project_id:
            client.projects.update(project=project_id, name=project_name, description=description)
        else:
            client.projects.create(name=project_name, domain=domain, description=description)

    except Exception as e:
        raise OpenstackException(message="Exception while creating project : " + e.message, exception=e, logger=LOGGER)


def delete_project(client, project_id):
    LOGGER.info("Executing delete_project with args : " + str(project_id))
    try:
        client.projects.delete(project=project_id)
    except Exception as e:
        raise OpenstackException(message="Exception while deleting project : " + e.message, exception=e, logger=LOGGER)


def list_user(client, with_sol_user=False):
    LOGGER.info("Executing list_user with args : " + str(with_sol_user))
    try:
        users = client.users.list()
        user_list = []
        for user in users:
            if user.name == constants.HYPERVISOR_SOLUSER_NAME and not with_sol_user:
                continue
            user_list.append({
                constants.USER_ID: user.id,
                constants.USERNAME: user.name,
                constants.USER_FULL_NAME: None if not hasattr(user, 'description') else user.description
            })
        return user_list
    except Exception as e:
        raise OpenstackException(message="Exception while lsting users : " + e.message, exception=e, logger=LOGGER)


def list_users_in_project(client, users, project_id):
    LOGGER.info("Executing list_users_in_project with args : " + str(users) + "\t" + str(project_id))
    try:
        if not users:
            users = list_user(client, with_sol_user=True)
        project_users = []
        for user in users:
            roles, ids = get_user_roles(client, user[constants.USER_ID], project_id)
            if roles:
                user[constants.ROLES] = roles
                user['role_ids'] = ids
                project_users.append(user)
        return project_users
    except Exception as e:
        raise OpenstackException(message="Exception while listing users in project : " + e.message, exception=e,
                                 logger=LOGGER)
