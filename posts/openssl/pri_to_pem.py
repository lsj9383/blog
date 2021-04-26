#!/usr/bin/env python

import base64
from optparse import OptionParser

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def parse_args():
    parser = OptionParser()

    parser.add_option("--n", dest="n", help="")
    parser.add_option("--e", dest="e", help="")
    parser.add_option("--p", dest="p", help="")
    parser.add_option("--q", dest="q", help="")
    parser.add_option("--d", dest="d", help="")
    parser.add_option("--dp", dest="dp", help="")
    parser.add_option("--dq", dest="dq", help="")
    parser.add_option("--qi", dest="qi", help="")
    return parser.parse_args()


def urlsafe_b64decode(data):
    missing_padding = 4 - len(data) % 4
    if missing_padding:
        data += '=' * missing_padding
    return base64.urlsafe_b64decode(data)


def pem_from_pri(n, e, p, q, d, dp, dq, qi):
    decode_n = urlsafe_b64decode(n)
    decode_e = urlsafe_b64decode(e)
    int_n = int.from_bytes(decode_n, byteorder='big')
    int_e = int.from_bytes(decode_e, byteorder='big')
    pub_key_numbers = rsa.RSAPublicNumbers(int_e, int_n)

    decode_p = urlsafe_b64decode(p)
    decode_q = urlsafe_b64decode(q)
    decode_d = urlsafe_b64decode(d)
    decode_dp = urlsafe_b64decode(dp)
    decode_dq = urlsafe_b64decode(dq)
    decode_qi = urlsafe_b64decode(qi)

    int_p = int.from_bytes(decode_p, byteorder='big')
    int_q = int.from_bytes(decode_q, byteorder='big')
    int_d = int.from_bytes(decode_d, byteorder='big')
    int_dp = int.from_bytes(decode_dp, byteorder='big')
    int_dq = int.from_bytes(decode_dq, byteorder='big')
    int_qi = int.from_bytes(decode_qi, byteorder='big')

    pri_key = rsa.RSAPrivateNumbers(int_p, int_q, int_d, int_dp, int_dq, int_qi, pub_key_numbers).private_key()
    pem = pri_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem.decode("utf-8")


def main():
    options, _ = parse_args()
    pem = pem_from_pri(options.n, options.e, options.p, options.q, options.d, options.dp, options.dq, options.qi)
    print(pem)


if __name__ == '__main__':
    main()
