#!/usr/bin/env python

import base64
import jwt

from optparse import OptionParser
from cryptography.hazmat.primitives.serialization import load_pem_public_key


def parse_args():
    parser = OptionParser()

    parser.add_option("-e", "--exponent", dest="exponent", help="The RSA public key exponent")
    parser.add_option("-n", "--modulus", dest="modulus", help="The RSA public key modulus")
    return parser.parse_args()


def n_e_from_pem(modulus, exponent):
    p = load_pem_public_key(pem)
    n = base64.urlsafe_b64encode(p.public_numbers().n.to_bytes(257, byteorder='big', signed=True))
    e = base64.urlsafe_b64encode(p.public_numbers().e.to_bytes(3, byteorder='big', signed=True))
    return n, e


def main():
    options, _ = parse_args()

    pem = pem_from_n_e(options.modulus, options.exponent)
    print(pem)


if __name__ == '__main__':
    main()
