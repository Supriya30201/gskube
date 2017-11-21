from glanceclient import client as glance_client
from exception.openstack_exception import OpenstackException
from core import constants


def create_glance_client(version, endpoint, token):
    try:
        return glance_client.Client(version=version, endpoint=endpoint, token=token)
    except Exception as e:
        raise OpenstackException(message=e.message, exception=e)


def image_list(client):
    try:
        images = client.images.list()
        images_list = []
        for image in images:
            images_list.append({
                constants.IMAGE_ID: image.id,
                constants.IMAGE_NAME: image.name,
                constants.IMAGE_STATUS: image.status,
                constants.IMAGE_SIZE: image.size/100000
            })
        return images_list
    except Exception as e:
        raise OpenstackException(message=e.message, exception=e)