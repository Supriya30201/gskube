from lib.adapter import sol_adapter
from core import constants


class Vcenter(sol_adapter.SolAadapter):
    def __init__(self, hypervisor_details):
        if hypervisor_details:
            self.protocol = str(hypervisor_details[constants.PROTOCOL])
            self.host = str(hypervisor_details[constants.HOST])
            self.port = str(hypervisor_details[constants.PORT])
            self.domain = str(hypervisor_details[constants.DOMAIN])
            return