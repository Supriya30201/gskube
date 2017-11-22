from neutronclient.v2_0 import client as neutron_client
from exception.openstack_exception import OpenstackException
from core import constants


def create_neutron_client(endpoint, token):
    try:
        return neutron_client.Client(endpoint_url=endpoint, token=token)
    except Exception as e:
        raise OpenstackException(message=e.message, exception=e)


def network_list(client):
    try:
        networks = client.list_networks()['networks']
        networks_list = []
        for network in networks:
            networks_list.append({
                constants.NETWORK_ID: str(network['id']),
                constants.NETWORK_NAME: str(network['name']),
                constants.NETWORK_STATUS: str(network['status']),
            })
        return networks_list
    except Exception as e:
        raise OpenstackException(message=e.message, exception=e)