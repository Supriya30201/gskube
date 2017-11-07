import base64

key = "openstack-box_007"


def encode(string_to_encode):
    """
    encode method can be used to encode any string.
    :param string_to_encode:
    :return:
    """
    enc = []
    for i in range(len(string_to_encode)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(string_to_encode[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc))


def decode(string_to_decode):
    """
    decode method can be used to decode encoded string.
    :param string_to_decode:
    :return:
    """
    string_to_decode = str(string_to_decode)
    dec = []
    cipher = base64.urlsafe_b64decode(string_to_decode)
    for i in range(len(cipher)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(cipher[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)
