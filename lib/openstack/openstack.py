from lib.adapter import sol_adapter
from lib.openstack import keystone
from exception.openstack_exception import OpenstackException
from core import constants


class Openstack(sol_adapter.SolAadapter):
    def __init__(self):

        return

    def create_sol_user(self, protocol, host, port, domain, username, password):
        try:
            unscoped_auth = keystone.unscoped_login(protocol, host, port, username, password)
            projects = keystone.list_projects(unscoped_auth['client'])
            scoped_auth = None
            found_admin = False
            project_id = None
            for project in projects:
                scoped_auth = keystone.scoped_login_v3(protocol, host, port, unscoped_auth['token'], project.id)
                if keystone.is_admin(scoped_auth['client'], unscoped_auth['user_id'], project.id):
                    found_admin = True
                    project_id = project.id
                    break

            if found_admin:
                user_id = keystone.create_user(scoped_auth['client'], constants.HYPERVISOR_SOLUSER_NAME,
                                               constants.HYPERVISOR_SOLUSER_PASSWORD,
                                               constants.HYPERVISOR_SOLUSER_EMAIL,
                                               constants.HYPERVISOR_SOLUSER_DESCRIPTION,
                                               keystone.get_roles(scoped_auth['client']), project_id)
                return {'user_id': user_id, 'user_password': constants.HYPERVISOR_SOLUSER_PASSWORD}

            return {constants.ERROR_MESSAGE: "User is not admin in any project."}
        except OpenstackException as oe:
            print oe.get_exception()
            return {constants.ERROR_MESSAGE: oe.get_message()}

        except Exception as e:
            print e
            return {constants.ERROR_MESSAGE: e.message}

