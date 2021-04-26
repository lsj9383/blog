#!/usr/bin/env python

import base64

from optparse import OptionParser

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def parse_args():
    parser = OptionParser()

    parser.add_option("-n", "--modulus", dest="modulus", help="The RSA public key modulus")
    parser.add_option("-e", "--exponent", dest="exponent", help="The RSA public key exponent")
    return parser.parse_args()


def urlsafe_b64decode(data):
    missing_padding = 4 - len(data) % 4
    if missing_padding:
        data += '=' * missing_padding
    return base64.urlsafe_b64decode(data)


def pem_from_n_e(modulus, exponent):
    decode_n = urlsafe_b64decode(modulus)
    decode_e = urlsafe_b64decode(exponent)
    int_n = int.from_bytes(decode_n, byteorder='big')
    int_e = int.from_bytes(decode_e, byteorder='big')
    pub_key = rsa.RSAPublicNumbers(int_e, int_n).public_key()
    pem = pub_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode("utf-8")


def main():
    options, _ = parse_args()
    pem = pem_from_n_e(options.modulus, options.exponent)
    print(pem)


if __name__ == '__main__':
    main()
