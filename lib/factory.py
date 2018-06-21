from lib.openstack import openstack
from lib.vcenter import vcenter
def get_adapter(hypervisor_type, dict):
    if hypervisor_type == "openstack":
        return openstack.Openstack(dict)
    elif hypervisor_type =="vCenter":
        return vcenter.Vcenter(dict)
