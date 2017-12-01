from neutronclient.v2_0 import client as neutron_client
from exception.openstack_exception import OpenstackException
from core import constants
import logging

LOGGER = logging.getLogger(__name__)


def create_neutron_client(endpoint, token):
    LOGGER.info("Executing create_neutron_client with args : " + endpoint + "\t" + token)
    try:
        return neutron_client.Client(endpoint_url=endpoint, token=token)
    except Exception as e:
        raise OpenstackException(message="Exception while creating neutron client : " + e.message, exception=e,
                                 logger=LOGGER)


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
        raise OpenstackException(message="Exception while listing networks : " + e.message, exception=e, logger=LOGGER)
