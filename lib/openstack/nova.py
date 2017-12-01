from novaclient import client
from exception.openstack_exception import OpenstackException
from core import constants
import logging

LOGGER = logging.getLogger(__name__)


def get_nova_connection(protocol, host, port, domain, username, password, project_id):
    LOGGER.info("Executing get_nova_connection with args : " + protocol + "\t" + host + "\t" + port + "\t" + domain +
                "\t" + username + "\t" + project_id)
    try:
        auth_url = protocol + "://" + host + ":" + port + "/v3"
        return client.Client("2", username=username, password=password, project_id=project_id, auth_url=auth_url,
                             user_domain_name=domain)
    except Exception as e:
        raise OpenstackException(message="Exception while loading nova client : " + e.message, exception=e,
                                 logger=LOGGER)


def list_servers(nova_client, images):
    LOGGER.info("Executing list_servers with args : " + images)
    flavors = list_flavors(nova_client)
    try:
        servers = nova_client.servers.list()
        servers_list = []
        for server in servers:
            server_flavor = None
            for flavor in flavors:
                if flavor[constants.FLAVOR_ID] == server.flavor['id']:
                    server_flavor = flavor
                    break
            server_image = None
            for image in images:
                if image[constants.IMAGE_ID] == server.image['id']:
                    server_image = image
                    break
            server_ips = load_server_ips(nova_client, server.id)
            servers_list.append({
                constants.INSTANCE_ID: server.id,
                constants.INSTANCE_NAME: server.name,
                constants.INSTANCE_STATUS: server.status,
                constants.INSTANCE_FLAVOR: server_flavor,
                constants.INSTANCE_IMAGE: server_image,
                constants.INSTANCE_IPS: server_ips
            })
        return servers_list
    except Exception as e:
        raise OpenstackException(message="Exception while listing servers : " + e.message, exception=e, logger=LOGGER)


def load_server_ips(nova_client, server_id):
    LOGGER.info("Executing load_server_ips with args : " + server_id)
    networks = nova_client.servers.ips(server=server_id)
    server_ips = []
    for network in networks.keys():
        for ips in networks[network]:
            server_ips.append(ips['addr'])
    return server_ips


def list_flavors(nova_client):
    try:
        flavors = nova_client.flavors.list()
        flavors_list = []
        for flavor in flavors:
            flavors_list.append({
                constants.FLAVOR_ID: flavor.id,
                constants.FLAVOR_NAME: flavor.name,
                constants.FLAVOR_VCPU: flavor.vcpus,
                constants.FLAVOR_RAM: flavor.ram,
                constants.FLAVOR_DISK: flavor.disk
            })
        return flavors_list
    except Exception as e:
        raise OpenstackException(message="Exception while listing flavor : " + e.message, exception=e, logger=LOGGER)


def create_server(nova_client, server_name, image_id, flavor_id, network_id):
    LOGGER.info("Executing create_server with args : " + server_name + "\t" + image_id + "\t" + flavor_id + "\t" +
                network_id)
    try:
        server = nova_client.servers.create(name=server_name, image=image_id, flavor=flavor_id,
                                            nics=[{'net-id': network_id}])
        return server.id
    except Exception as e:
        raise OpenstackException(message="Exception while creating server : " + e.message, exception=e, logger=LOGGER)


def modify_flavor(nova_client, server_id, flavor_id):
    LOGGER.info("Executing modify_flavor with args : " + server_id + "\t" + flavor_id)
    try:
        nova_client.servers.resize(server=server_id, flavor=flavor_id)
    except Exception as e:
        raise OpenstackException(message="Exception while modifying flavor : " + e.message, exception=e, logger=LOGGER)


def load_console(nova_client, server_id):
    LOGGER.info("Executing load_console with args : " + server_id)
    try:
        vnc_url_obj = nova_client.servers.get_vnc_console(server=server_id, console_type="novnc")
        return vnc_url_obj['console']['url']
    except Exception as e:
        raise OpenstackException(message="Exception while loading console : " + e.message, exception=e, logger=LOGGER)


def start_server(nova_client, server_id):
    LOGGER.info("Executing start_server with args : " + server_id)
    try:
        return nova_client.servers.start(server=server_id)
    except Exception as e:
        raise OpenstackException(message="Exception while starting server : " + e.message, exception=e, logger=LOGGER)


def delete_server(nova_client, server_id):
    LOGGER.info("Executing delete_server with args : " + server_id)
    try:
        return nova_client.servers.delete(server=server_id)
    except Exception as e:
        raise OpenstackException(message="Exception while deleting server : " + e.message, exception=e, logger=LOGGER)


def stop_server(nova_client, server_id):
    LOGGER.info("Executing stop_server with args : " + server_id)
    try:
        return nova_client.servers.stop(server=server_id)
    except Exception as e:
        raise OpenstackException(message="Exception while stopping server : " + e.message, exception=e, logger=LOGGER)


def hypervisor_list(nova_client):
    try:
        return nova_client.hypervisors.list()
    except Exception as e:
        raise OpenstackException(message="Exception while getting hypervisors : " + e.message, exception=e,
                                 logger=LOGGER)


def get_hypervisor(nova_client, hypervisor):
    LOGGER.info("Executing get_hypervisor with args : " + hypervisor)
    try:
        return nova_client.hypervisors.get(hypervisor)
    except Exception as e:
        raise OpenstackException(message="Exception while getting hypervisor : " + e.message, exception=e,
                                 logger=LOGGER)


def get_detailed_usage(nova_client, start_date, end_date):
    LOGGER.info("Executing get_detailed_usage with args : " + start_date + "\t" + end_date)
    try:
        return nova_client.usage.list(start=start_date, end=end_date, detailed=True)
    except Exception as e:
        raise OpenstackException(message="Exception while getting usage details : " + e.message, exception=e,
                                 logger=LOGGER)


def get_quota_details(nova_client, tenant_id):
    LOGGER.info("Executing get_quota_details with args : " + tenant_id)
    try:
        return nova_client.quotas.get(tenant_id=tenant_id)
    except Exception as e:
        raise OpenstackException(message="Exception while getting quota details : " + e.message, exception=e,
                                 logger=LOGGER)


def set_quota_details(nova_client, tenant_id, quotas):
    LOGGER.info("Executing set_quota_details with args : " + tenant_id + "\t" + quotas)
    try:
        nova_client.quotas.update(tenant_id=tenant_id, cores=quotas[constants.TOTAL_CPU],
                                  fixed_ips=quotas[constants.FIXED_IPS], floating_ips=quotas[constants.FLOATING_IPS],
                                  instances=quotas[constants.INSTANCES], ram=quotas[constants.TOTAL_MEMORY],
                                  security_group_rules=quotas[constants.SECURITY_GROUP_RULES],
                                  security_groups=quotas[constants.SECURITY_GROUPS],
                                  server_group_members=quotas[constants.SERVER_GROUP_MEMBERS],
                                  server_groups=quotas[constants.SERVER_GROUPS])
    except Exception as e:
        return OpenstackException(message="Exception while setting quota : " + e.message, exception=e, logger=LOGGER)