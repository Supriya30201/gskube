import base64
import paramiko
import time
import constants
from wsgiref.util import FileWrapper
import os
from django.http import HttpResponse
from tabulate import tabulate


key = "openstack-box_007"
OPENVPN_COMMAND_LIST1 = ["rm -rf {temp_location};", "cp -R {openvpn_location} {temp_location};",
                         "cd {temp_location}easy-rsa/keys/;", "mkdir ../../openvpnconfig;",
                         "cp ca.crt ../../openvpnconfig;", "cp ca.key ../../openvpnconfig;",
                         "cp index.txt ../../openvpnconfig;", "cp serial ../../openvpnconfig;",
                         "rm -r *;", "cd {temp_location}openvpnconfig;", "cp ca.crt {temp_location}easy-rsa/keys/;",
                         "cp ca.key {temp_location}easy-rsa/keys/;", "cp index.txt {temp_location}easy-rsa/keys/;",
                         "cp serial {temp_location}easy-rsa/keys/"]
OPENVPN_COMMAND_LIST2 = ["cd {temp_location}easy-rsa/;", "chmod 777 whichopensslcnf;", "pwd;",
                         "source ./vars;chmod 777 build-key;", "chmod 777 pkitool;", "./build-key --batch {file_name};",
                         "mkdir {file_name};"]
OPENVPN_COMMAND_LIST3 = ["cd {temp_location}easy-rsa/keys;", "cp *.pem ../../openvpnconfig;",
                         "cp {file_name}.* ../../openvpnconfig;",
                         "cp {openvpn_location}easy-rsa/keys/ahaldar/ta.key {temp_location}openvpnconfig;",
                         "cp {openvpn_location}easy-rsa/keys/ahaldar/client.ovpn {temp_location}openvpnconfig;",
                         "sed -Ei 's/ahaldar/{file_name}/g' {temp_location}openvpnconfig/client.ovpn"]
OPENVPN_COMMAND_LIST4 = ["cd {temp_location}openvpnconfig;rm index.txt serial;", "zip -rm {file_name}.zip ."]


def encode(string_to_encode):
    """
    encode method can be used to encode any string.
    :param string_to_encode:
    :return:
    """
    """enc = []
    for i in range(len(string_to_encode)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(string_to_encode[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc).encode(encoding="utf-8"))"""
    return base64.urlsafe_b64encode("".join(string_to_encode).encode(encoding="utf-8"))


def decode(string_to_decode):
    """
    decode method can be used to decode encoded string.
    :param string_to_decode:
    :return:
    """
    dec = []
    cipher = base64.urlsafe_b64decode(string_to_decode)
    cipher = str(cipher, 'utf-8')
    """for i in range(len(cipher)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(cipher[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)"""
    return "".join(cipher)


def generate_openvpn_certificate(openvpn_conf, username):
    temp_location = openvpn_conf[constants.OPENVPN_TEMP_FOLDER_LOCATION]
    openvpn_location = openvpn_conf[constants.OPENVPN_FOLDER_LOCATION]
    local_file = './{file_name}'.format(file_name=username)
    dir_remote = '{temp_location}openvpnconfig/{file_name}.zip'.format(file_name=username, temp_location=temp_location)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(openvpn_conf[constants.OPENVPN_HOST], username=openvpn_conf[constants.OPENVPN_USERNAME],
                password=decode(openvpn_conf[constants.OPENVPN_PASSWORD]))
    ssh.exec_command(''.join(OPENVPN_COMMAND_LIST1).format(temp_location=temp_location,
                                                           openvpn_location=openvpn_location))
    time.sleep(3)
    ssh.exec_command(''.join(OPENVPN_COMMAND_LIST2).format(file_name=username, temp_location=temp_location))
    time.sleep(3)
    ssh.exec_command(''.join(OPENVPN_COMMAND_LIST3).format(file_name=username, temp_location=temp_location,
                                                           openvpn_location=openvpn_location))
    time.sleep(3)
    ssh.exec_command(''.join(OPENVPN_COMMAND_LIST4).format(file_name=username, temp_location=temp_location))
    transport = paramiko.Transport((openvpn_conf[constants.OPENVPN_HOST], 22))
    transport.connect(username=openvpn_conf[constants.OPENVPN_USERNAME],
                      password=decode(openvpn_conf[constants.OPENVPN_PASSWORD]))
    sftp = paramiko.SFTPClient.from_transport(transport)
    if sftp.stat(dir_remote):
        sftp.get(localpath=local_file, remotepath=dir_remote)
        transport.close()
    ssh.exec_command("rm -rf {temp_location}".format(temp_location=temp_location))

    wrapper = FileWrapper(open(local_file, 'rb'))
    response = HttpResponse(wrapper, content_type='application/force-download')
    response['Content-Length'] = os.path.getsize(local_file)
    response['Content-Disposition'] = "attachment; filename=" + username + ".zip"
    os.remove(local_file)
    return response


def get_instance_table(name, host, project, doc, doe, action, user_full_name):
    return tabulate([["Instance Name : ", name], ["Hypervisor : ", host],
                     ["Project : ", project], ["Date of Request:", doc],
                     ["Expiry Date:", doe], [action, user_full_name]])