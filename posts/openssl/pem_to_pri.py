#!/usr/bin/env python

import base64
import json

from optparse import OptionParser
from cryptography.hazmat.primitives.serialization import load_pem_private_key


def parse_args():
    parser = OptionParser()

    parser.add_option("-p", "--pem", dest="pem", default="private_key.pem", help="PEM file")
    return parser.parse_args()


def pri_from_pem(pem):
    pri = load_pem_private_key(pem, password=None)
    int_p = pri.private_numbers().p
    int_q = pri.private_numbers().q
    int_d = pri.private_numbers().d
    int_dp = pri.private_numbers().dmp1
    int_dq = pri.private_numbers().dmq1
    int_qi = pri.private_numbers().iqmp

    p = base64.urlsafe_b64encode(int_p.to_bytes((int_p.bit_length() + 7) // 8, byteorder='big'))
    q = base64.urlsafe_b64encode(int_q.to_bytes((int_q.bit_length() + 7) // 8, byteorder='big'))
    d = base64.urlsafe_b64encode(int_d.to_bytes((int_d.bit_length() + 7) // 8, byteorder='big'))
    dp = base64.urlsafe_b64encode(int_dp.to_bytes((int_dp.bit_length() + 7) // 8, byteorder='big'))
    dq = base64.urlsafe_b64encode(int_dq.to_bytes((int_dq.bit_length() + 7) // 8, byteorder='big'))
    qi = base64.urlsafe_b64encode(int_qi.to_bytes((int_qi.bit_length() + 7) // 8, byteorder='big'))

    return {
        "p": p.decode('utf-8'),
        "q": q.decode('utf-8'),
        "d": d.decode('utf-8'),
        "dp": dp.decode('utf-8'),
        "dq": dq.decode('utf-8'),
        "qi": qi.decode('utf-8'),
    }


def main():
    options, _ = parse_args()

    raw_pem = None
    with open(options.pem, "rb") as p:
        raw_pem = p.read()

    jwk_rs256_pri = pri_from_pem(raw_pem)
    print(json.dumps(jwk_rs256_pri, indent=4))


if __name__ == '__main__':
    main()
