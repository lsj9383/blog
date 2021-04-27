#!/usr/bin/env python

import base64

from optparse import OptionParser
from cryptography.hazmat.primitives.serialization import load_pem_public_key


def parse_args():
    parser = OptionParser()

    parser.add_option("-p", "--pem", dest="pem", default="public_key.pem", help="PEM file")
    return parser.parse_args()


def n_e_from_pem(pem):
    p = load_pem_public_key(pem)
    n = base64.urlsafe_b64encode(p.public_numbers().n.to_bytes(256, byteorder='big'))
    e = base64.urlsafe_b64encode(p.public_numbers().e.to_bytes(3, byteorder='big'))
    return n, e


def main():
    options, _ = parse_args()

    raw_pem = None
    with open(options.pem, "rb") as p:
        raw_pem = p.read()

    b64n, b64e = n_e_from_pem(raw_pem)
    print("base64 n:", b64n.decode('utf-8'))
    print("\nbase64 e:", b64e.decode('utf-8'))


if __name__ == '__main__':
    main()
