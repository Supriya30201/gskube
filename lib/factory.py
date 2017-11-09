from lib.openstack import openstack


def get_adapter(hypervisor_type):
    if hypervisor_type == "openstack":
        return openstack.Openstack()
