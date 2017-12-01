from glanceclient import client as glance_client
from exception.openstack_exception import OpenstackException
from core import constants
import logging

LOGGER = logging.getLogger(__name__)


def create_glance_client(version, endpoint, token):
    LOGGER.info("Executing create_glance_client with args : " + version + "\t" + endpoint + "\t" + token)
    try:
        return glance_client.Client(version=version, endpoint=endpoint, token=token)
    except Exception as e:
        raise OpenstackException(message="Exception while creating glance client : " + e.message, exception=e,
                                 logger=LOGGER)


def image_list(client):
    try:
        images = client.images.list()
        images_list = []
        for image in images:
            images_list.append({
                constants.IMAGE_ID: image.id,
                constants.IMAGE_NAME: image.name,
                constants.IMAGE_STATUS: image.status,
                constants.IMAGE_SIZE: image.size/1000000
            })
        return images_list
    except Exception as e:
        raise OpenstackException(message="Exception while listing images : " + e.message, exception=e, logger=LOGGER)
