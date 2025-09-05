#!/usr/bin/env python3

import requests
import sys

ID = 10000
BASE_URI = "http://0.0.0.0:54934/api/v1"

if __name__ == "__main__":

    print("Listing current exports ...")
    uri = BASE_URI + '/export'
    r = requests.get(uri)
    print(r.json())

    print("Creating new export ...")
    uri = BASE_URI + '/export'
    payload = {
        'id': ID,
        'name': "my_share",
        'fs': 'nfs',
        'path': "path_to_share",
        'access': 'RW',
        'protocols': [4],
        'clients': ['10.69.0.0/16'],
    }
    print(payload)
    r = requests.post(uri, json=payload)
    print(r)

    print("Updating export ...")
    uri = BASE_URI + f'/export/{ID}'
    payload = {
        'id': 10000,
        'name': "my_share",
        'fs': 'nfs',
        'path': "path_to_share",
        'access': 'RO',
        'protocols': [3, 4],
        'clients': ['192.168.0.0/24'],
    }
    print(payload)
    r = requests.put(uri, json=payload)
    print(r)

    print("Deleting export ...")
    uri = BASE_URI + f'/export/{ID}'
    r = requests.delete(uri)
    print(r)

    sys.exit(0)
