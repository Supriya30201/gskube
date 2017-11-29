from lib.adapter import sol_adapter
from lib.openstack import keystone
from lib.openstack import nova
from lib.openstack import glance
from lib.openstack import neutron
from exception.openstack_exception import OpenstackException
from core import constants


class Openstack(sol_adapter.SolAadapter):
    def __init__(self, hypervisor_details):
        if hypervisor_details:
            self.protocol = str(hypervisor_details[constants.PROTOCOL])
            self.host = str(hypervisor_details[constants.HOST])
            self.port = str(hypervisor_details[constants.PORT])
            self.domain = str(hypervisor_details[constants.DOMAIN])
            if constants.USERNAME in hypervisor_details:
                self.username = str(hypervisor_details[constants.USERNAME])
                self.password = str(hypervisor_details[constants.PASSWORD])
                self.keystone_client = None

            if constants.TOKEN in hypervisor_details:
                self.keystone_client = keystone.get_client(self.protocol, self.host, self.port,
                                                           str(hypervisor_details[constants.TOKEN]))
            if constants.PROJECT_ID in hypervisor_details:
                self.project_id = str(hypervisor_details[constants.PROJECT_ID])

            self.nova_client = None
            self.glance_client = None
            self.neutron_client = None
            return

    def create_sol_user(self):
        try:
            _, project_id = self.generate_admin_auth()
            roles = []
            for role in self.get_roles():
                roles.append(role[constants.ROLE_ID])

            user_id = self.create_user(constants.HYPERVISOR_SOLUSER_NAME, constants.HYPERVISOR_SOLUSER_PASSWORD,
                                       constants.HYPERVISOR_SOLUSER_EMAIL, constants.HYPERVISOR_SOLUSER_DESCRIPTION,
                                       roles, project_id)
            return {'user_id': user_id, 'user_password': constants.HYPERVISOR_SOLUSER_PASSWORD}

        except OpenstackException as oe:
            return {constants.ERROR_MESSAGE: oe.get_message()}
        except Exception as e:
            return {constants.ERROR_MESSAGE: e.message}

    def generate_admin_auth(self):
        projects, unscoped_auth = self.get_projects_using_unscoped_login()
        project_id = None
        token = None
        for project in projects:
            scoped_auth = keystone.scoped_login_v3(self.protocol, self.host, self.port, unscoped_auth['token'],
                                                   project['id'])
            if keystone.is_admin(scoped_auth['client'], unscoped_auth['user_id'], project['id']):
                self.keystone_client = scoped_auth['client']
                project_id = project['id']
                token = scoped_auth['token']
                break

        if not project_id:
            raise OpenstackException(message="Unable to find admin role for given user.")

        return token, project_id

    def get_projects_using_unscoped_login(self):
        unscoped_auth = keystone.unscoped_login(self.protocol, self.host, self.port, self.username, self.password)
        api_projects = keystone.list_projects(unscoped_auth['client'])
        projects = []
        for project in api_projects:
            projects.append({'id': project.id,
                             'name': project.name})
        return projects, unscoped_auth

    def get_all_projects(self):
        self.load_keystone_client(self)
        projects_response = keystone.list_projects(self.keystone_client, False)
        projects = []
        for project in projects_response:
            projects.append({
                'id': project.id,
                'name': project.name,
                'description': project.description
            })
        return projects

    def is_admin_for_project(self):
        try:
            user_id, token, endpoint_urls = self.load_keystone_client(self.project_id)
            is_admin = False
            if endpoint_urls:
                is_admin = keystone.is_admin(self.keystone_client, user_id, self.project_id)
            return token, endpoint_urls, is_admin
        except Exception as e:
            raise OpenstackException(message=e.message, exception=e)

    def get_image_list(self, endpoint_list, token):
        self.load_glance_client(endpoint_list, token)
        return glance.image_list(self.glance_client)

    def get_network_list(self, endpoint_list, token):
        self.load_neutron_client(endpoint_list, token)
        return neutron.network_list(self.neutron_client)

    def get_flavor_list(self):
        self.load_nova_client()
        return nova.list_flavors(self.nova_client)

    def create_project(self, name, description, domain=None, project_id=None):
        self.load_keystone_client()
        keystone.create_project(self.keystone_client, name, description, domain=domain, project_id=project_id)

    def get_project(self, project_id):
        self.load_keystone_client()
        return keystone.get_project(self.keystone_client, project_id)

    def create_server(self, server_name, image_id, flavor_id, network_id):
        self.load_nova_client()
        return nova.create_server(self.nova_client, server_name, image_id, flavor_id, network_id)

    def list_servers(self, endpoint_list, token):
        self.load_nova_client()
        self.load_glance_client(endpoint_list, token)
        return nova.list_servers(self.nova_client, images=glance.image_list(self.glance_client))

    def delete_project(self, project_id):
        keystone.delete_project(self.keystone_client, project_id)

    def load_console(self, instance_id):
        self.load_nova_client()
        return nova.load_console(self.nova_client, instance_id)

    def start_instance(self, instance_id):
        self.load_nova_client()
        return nova.start_server(self.nova_client, instance_id)

    def stop_instance(self, instance_id):
        self.load_nova_client()
        return nova.stop_server(self.nova_client, instance_id)

    def delete_instance(self, instance_id):
        self.load_nova_client()
        return nova.delete_server(self.nova_client, instance_id)

    def modify_instance(self, instance_id, flavor_id):
        self.load_nova_client()
        return nova.modify_server(self.nova_client, instance_id, flavor_id)

    def get_users(self):
        self.load_keystone_client()
        return keystone.list_user(self.keystone_client)

    def create_user(self, username, password, email, full_name, roles=None, project_id=None):
        self.load_keystone_client()
        return keystone.create_user(self.keystone_client, username, password, email, full_name, roles, project_id)

    def delete_user(self, user_id):
        self.load_keystone_client()
        keystone.delete_user(self.keystone_client, user_id)

    def get_roles(self):
        self.load_keystone_client()
        return keystone.get_roles(self.keystone_client)

    def get_user_roles_project(self, project_id, users=None):
        self.load_keystone_client()
        return keystone.list_users_in_project(self.keystone_client, users, project_id)

    def assign_roles(self, roles, user_id, project_id):
        self.load_keystone_client()
        return keystone.assign_roles(self.keystone_client, user_id, roles, project_id)

    def revoke_roles(self, roles, user_id, project_id):
        self.load_keystone_client()
        return keystone.revoke_roles(self.keystone_client, user_id, roles, project_id)

    def load_hypervisors(self):
        self.load_nova_client()
        return nova.hypervisor_list(self.nova_client)

    def get_hypervisor(self, hypervisor):
        self.load_nova_client()
        return nova.get_hypervisor(self.nova_client, hypervisor)

    def get_detailed_usage(self, start_date, end_date):
        self.load_nova_client()
        return nova.get_detailed_usage(self.nova_client, start_date, end_date)

    def get_quota_details(self, tenant_id, limited=False):
        self.load_nova_client()
        quotas = nova.get_quota_details(self.nova_client, tenant_id)
        if not limited:
            return quotas
        return {
            constants.TOTAL_CPU: quotas.cores,
            constants.TOTAL_MEMORY: quotas.ram,
            constants.FIXED_IPS: quotas.fixed_ips,
            constants.FLOATING_IPS: quotas.floating_ips,
            constants.INSTANCES: quotas.instances,
            constants.SECURITY_GROUPS: quotas.security_groups,
            constants.SECURITY_GROUP_RULES: quotas.security_group_rules,
            constants.SERVER_GROUPS: quotas.server_groups,
            constants.SERVER_GROUP_MEMBERS: quotas.server_group_members
        }

    def set_quota_details(self, tenant_id, quotas):
        self.load_nova_client()
        nova.set_quota_details(self.nova_client, tenant_id, quotas)

    def load_nova_client(self):
        if not self.nova_client:
            if hasattr(self, "project_id"):
                self.nova_client = nova.get_nova_connection(self.protocol, self.host, self.port, self.domain,
                                                            self.username, self.password, self.project_id)
            else:
                self.nova_client = nova.get_nova_connection(self.protocol, self.host, self.port, self.domain,
                                                            self.username, self.password, None)

    def load_keystone_client(self, project_id=None):
        if self.keystone_client:
            return

        unscoped_auth = keystone.unscoped_login(self.protocol, self.host, self.port, self.username, self.password)
        if not project_id:
            self.keystone_client = unscoped_auth['client']
            return

        scoped_auth = keystone.scoped_login_v3(self.protocol, self.host, self.port, unscoped_auth['token'],
                                               project_id)

        self.keystone_client = scoped_auth['client']

        if 'endpoint_urls' in scoped_auth:
            return unscoped_auth['user_id'], scoped_auth['token'], scoped_auth['endpoint_urls']
        return unscoped_auth['user_id'], scoped_auth['token'], []

    def load_glance_client(self, endpoint_list, token):
        endpoint_url = None
        for endpoint in endpoint_list:
            if endpoint['endpoint_name'] == 'glance':
                endpoint_url = endpoint['endpoint_url']
                break
        self.glance_client = glance.create_glance_client('2', endpoint_url, token)

    def load_neutron_client(self, endpoint_list, token):
        endpoint_url = None
        for endpoint in endpoint_list:
            if endpoint['endpoint_name'] == 'neutron':
                endpoint_url = endpoint['endpoint_url']
                break

        self.neutron_client = neutron.create_neutron_client(endpoint_url, token)