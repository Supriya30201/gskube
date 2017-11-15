from lib.adapter import sol_adapter
from lib.openstack import keystone
from exception.openstack_exception import OpenstackException
from core import constants


class Openstack(sol_adapter.SolAadapter):
    def __init__(self, hypervisor_details):
        if dict:
            self.protocol = str(hypervisor_details['protocol'])
            self.host = str(hypervisor_details['host'])
            self.port = str(hypervisor_details['port'])
            self.domain = str(hypervisor_details['domain'])
            if 'username' in hypervisor_details:
                self.username = str(hypervisor_details['username'])
                self.password = str(hypervisor_details['password'])
                self.keystone_client = None
            else:
                self.keystone_client = keystone.get_client(self.protocol, self.host, self.port,
                                                           str(hypervisor_details['token']))
            return

    def create_sol_user(self, protocol, host, port, domain, username, password):
        try:
            project_id = self.generate_admin_auth()
            if isinstance(project_id, dict):
                return project_id
            user_id = keystone.create_user(self.keystone_client, constants.HYPERVISOR_SOLUSER_NAME,
                                           constants.HYPERVISOR_SOLUSER_PASSWORD,
                                           constants.HYPERVISOR_SOLUSER_EMAIL,
                                           constants.HYPERVISOR_SOLUSER_DESCRIPTION,
                                           keystone.get_roles(self.keystone_client), project_id)
            return {'user_id': user_id, 'user_password': constants.HYPERVISOR_SOLUSER_PASSWORD}

        except OpenstackException as oe:
            return {constants.ERROR_MESSAGE: oe.get_message()}
        except Exception as e:
            return {constants.ERROR_MESSAGE: e.message}

    def generate_admin_auth(self):
        unscoped_auth = keystone.unscoped_login(self.protocol, self.host, self.port, self.username, self.password)
        projects = keystone.list_projects(unscoped_auth['client'])
        project_id = None
        token = None
        for project in projects:
            scoped_auth = keystone.scoped_login_v3(self.protocol, self.host, self.port, unscoped_auth['token'],
                                                   project.id)
            if keystone.is_admin(scoped_auth['client'], unscoped_auth['user_id'], project.id):
                self.keystone_client = scoped_auth['client']
                project_id = project.id
                token = scoped_auth['token']
                break

        if not project_id:
            raise OpenstackException(message="Unable to find admin role for given user.")

        return token, project_id

    def get_all_projects(self):
        projects_response = keystone.list_projects(self.keystone_client, False)
        projects = []
        for project in projects_response:
            projects.append({
                'id': project.id,
                'name': project.name
            })
        return projects

    def create_project(self, domain, name, description):
        keystone.create_project(self.keystone_client, domain, name, description)

    def delete_project(self, project_id):
        keystone.delete_project(self.keystone_client, project_id)
