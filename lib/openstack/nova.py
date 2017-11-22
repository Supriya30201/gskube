from novaclient import client
from exception.openstack_exception import OpenstackException
from core import constants
import logging

logger = logging.getLogger(__name__)


def get_nova_connection(protocol, host, port, domain, username, password, project_id):
    try:
        auth_url = protocol + "://" + host + ":" + port + "/v3"
        return client.Client("2", username=username, password=password, project_id=project_id, auth_url=auth_url,
                             user_domain_name=domain)
    except Exception as e:
        raise OpenstackException(message=e.message, exception=e)


def list_servers(nova_client, images):
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
        logger.error("Exception while listing servers : " + e.message)
        raise OpenstackException(message="Exception while listing servers : " + e.message, exception=e)


def load_server_ips(nova_client, server_id):
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
        raise OpenstackException(message=e.message, exception=e)


def create_server(nova_client, server_name, image_id, flavor_id, network_id):
    try:
        server = nova_client.servers.create(name=server_name, image=image_id, flavor=flavor_id, nics=[{'net-id': network_id}])
        return server.id
    except Exception as e:
        logger.error("Exception while creating server : " + e.message)
        raise OpenstackException(message="Exception while creating server : " + e.message, exception=e)


def modify_flavor(nova_client, server_id, flavor_id):
    try:
        nova_client.servers.resize(server=server_id, flavor=flavor_id)
    except Exception as e:
        logger.error("Exception while modifying flavor of server : " + e.message)
        raise OpenstackException(message=e.message, exception=e)


def load_console(nova_client, server_id):
    try:
        vnc_url_obj = nova_client.servers.get_vnc_console(server=server_id, console_type="novnc")
        return vnc_url_obj['console']['url']
    except Exception as e:
        logger.error("Exception while getting vnc url to start console : " + e.message)
        raise OpenstackException(message=e.message, exception=e)


def start_server(nova_client, server_id):
    try:
        return nova_client.servers.start(server=server_id)
    except Exception as e:
        logger.error("Exception while starting server : " + e.message)
        raise OpenstackException(message=e.message, exception=e)


def delete_server(nova_client, server_id):
    try:
        return nova_client.servers.delete(server=server_id)
    except Exception as e:
        logger.error("Exception while deleting server : " + e.message)
        raise OpenstackException(message=e.message, exception=e)


def stop_server(nova_client, server_id):
    try:
        return nova_client.servers.stop(server=server_id)
    except Exception as e:
        logger.error("Exception while stopping server : " + e.message)
        raise OpenstackException(message="Exception while stopping server : " + e.message, exception=e)