from keystoneauth1.identity import v2
from keystoneauth1 import session as keystone_session
from keystoneclient.v2_0 import client as v2_client
from exception.openstack_exception import OpenstackException
from exception.openstack_session_exception import OpenstackSessionException
from keystoneclient.v3 import client as v3_client
from keystoneclient.auth.identity import v3


# Unscoped Token using v2
def unscoped_login(protocol, host, port, username, password):
    try:
        url = protocol + "://" + host + ":" + port + "/v2.0"
        auth = v2.Password(username=username, password=password, auth_url=url)
        session = keystone_session.Session(auth=auth)
        client = v2_client.Client(session=session)
        token = client.session.get_token(auth)
        user_id = client.session.get_user_id(auth)
        return {'token': token, 'client': client, 'user_id': user_id}
    except Exception as e:
        raise OpenstackException(message="Exception while performing unscoped login : " + e.message, exception=e)


# Uses:For User operations(create/delete/list users) and compute operations(create/delete/list/start/stop instance)
def scoped_login_v3(protocol, host, port, token, project_id):
    try:
        url = protocol + "://" + host + ":" + port + "/v3"
        auth = v3.Token(auth_url=url, token=token, project_id=project_id)
        session = keystone_session.Session(auth=auth)
        connection = v3_client.Client(session=session)
        token = connection.session.get_token(auth)
        return {'client': connection, 'token': token}
    except Exception as e:
        raise OpenstackException("Exception while performing scoped login : " + e.message, exception=e)


def get_client(protocol, host, port, token):
    try:
        url = protocol + "://" + host + ":" + port + "/v3"
        connection = v3_client.Client(endpoint=url, token=token)
        return connection
    except Exception as e:
        raise OpenstackSessionException(message="Exception while requesting client : " + e.message, exception=e)


# List projects using v2 unscoped token
def list_projects(client, v2_api=True):
    try:
        if v2_api:
            projects_list = client.tenants.list()
        else:
            projects_list = client.projects.list()
        return projects_list
    except Exception as e:
        raise OpenstackException(message="Exception while getting list of projects : " + e.message, exception=e)


def get_user_roles(client, user_id, project_id):
    try:
        user_roles = []
        users_role_list = client.roles.list(user=user_id, project=project_id)

        for role in users_role_list:
            user_roles.append(role.name)
        return user_roles
    except Exception as e:
        raise OpenstackException(message="Exception while getting roles for specified project and user : " + e.message,
                                 exception=e)


def is_admin(client, user_id, project_id):
    users_project_roles = get_user_roles(client, user_id, project_id)
    for role in users_project_roles:
        if "admin" in role.lower():
            return True
    return False


def create_user(client, name, password, email, description, roles=None, project_id=None):
    try:
        new_user = client.users.create(name=name, description=description, password=password, email=email,
                                       project=project_id)
        if project_id:
            assign_roles(client, new_user.id, roles, project_id)
        return new_user.id
    except Exception as e:
        raise OpenstackException(message="Exception while creating user in openstack : " + e.message, exception=e)


def get_roles(client):
    try:
        roles = client.roles.list()
        return roles
    except Exception as e:
        raise OpenstackException(message="Exception while getting roles from openstack: " + e.message, exception=e)


def assign_roles(client, user_id, roles, project_id):
    try:
        for role in roles:
            client.roles.grant(role=role, user=user_id, project=project_id)

    except Exception as e:
        raise OpenstackException(message="Exception while assiging roles: " + e.message, exception=e)


def remove_user_role(client, user_id, roles, project_id):
    try:
        for role in roles:
            client.roles.revoke(role=role, user=user_id, project=project_id)
    except Exception as e:
        raise OpenstackException(message="Exception while removing roles of user: " + e.message, exception=e)


def create_project(client, domain, project_name, description, project_id=None):
    """
    If project_id is passed, method will update project.
    :param client:
    :param domain:
    :param project_name:
    :param description:
    :param project_id:
    :return:
    """
    try:
        if project_id:
            client.projects.update(project=project_id, name=project_name, description=description)
        else:
            client.projects.create(name=project_name, domain=domain, description=description)

    except Exception as e:
        raise OpenstackException(message="Exception while creating project : " + e.message, exception=e)


def delete_project(client, project_id):
    try:
        client.projects.delete(project=project_id)
    except Exception as e:
        raise OpenstackException(message="Exception while deleting project : " + e.message, exception=e)
