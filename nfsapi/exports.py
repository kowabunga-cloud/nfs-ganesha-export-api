# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

from typing import cast, List, Dict, Any, Optional, TYPE_CHECKING

from nfsapi.common import *
from nfsapi.parser import RawBlock, GaneshaConfParser

class GaneshaExportConfig():
    def __init__(self, cfg_file):
        self.cfg_file = cfg_file
        self.exports = []

    def read(self):
        with open(self.cfg_file) as f:
            data = f.read()
            p = GaneshaConfParser(data)
            self.exports = p.parse()

    def write(self, data):
        with open(self.cfg_file, 'w') as f:
            f.write(data)

    def dump(self):
        res = '''
###############################################################
# This file has been automatically generated. Do NOT edit it. #
###############################################################

'''
        for e in self.exports:
            res += e.export()
            res += '\n'
        print(res)
        return res

    def lookup(self, k: str, v: Any) -> RawBlock:
        for e in self.exports:
            if e.values.get(k) == v:
                return e
        return None

    def lookup_by_id(self, eid: int) -> RawBlock:
        return self.lookup(NFS_EXPORT_ATTR_ID, eid)

    def lookup_by_name(self, name: str):
        return self.lookup(NFS_EXPORT_ATTR_PSEUDO, name)

    def verify_params(self, eid=None, name=None, access=None, protocols=None) -> bool:
        if eid is not None and (eid < 1 or eid > 65535):
            print(f'Invalid export ID: {eid}')
            return False
        if name is not None and self.lookup_by_name(name) is not None:
            print(f'Export with name {name} already exists')
            return False
        if access is not None and access not in NFS_EXPORT_ATTR_ACCESS_TYPE_ALLOWED_VALUES:
            print(f'Invalid access type: {access}')
            return False
        if protocols is not None:
            for p in protocols:
                if p not in NFS_EXPORT_ATTR_PROTOCOLS_ALLOWED_VALUES:
                    print(f'Invalid protocols: {protocols}')
                    return False
        return True

    def add(self, eid: int, name: str, fs: str, path: str, access: str, protocols: list, clients: list) -> bool:
        if not self.verify_params(eid, name, access, protocols):
            return False

        if self.lookup_by_id(eid) is not None:
            print(f'Export with ID {eid} already exists')
            return False

        fsal_values = {
            NFS_FSAL_ATTR_NAME: NFS_FSAL_ATTR_NAME_DEFAULT_VALUE,
            NFS_FSAL_ATTR_USER: NFS_FSAL_ATTR_USER_DEFAULT_VALUE,
            NFS_FSAL_ATTR_FS: fs,
        }
        fsal = RawBlock(NFS_BLOCK_FSAL, [], fsal_values)

        client_values = {
            NFS_CLIENT_ATTR_CLIENTS: clients,
        }
        client = RawBlock(NFS_BLOCK_CLIENT, [], client_values)

        export_values = {
            NFS_EXPORT_ATTR_ID: eid,
            NFS_EXPORT_ATTR_PATH: path,
            NFS_EXPORT_ATTR_PSEUDO: name,
            NFS_EXPORT_ATTR_ACCESS_TYPE: access,
            NFS_EXPORT_ATTR_PROTOCOLS: protocols,
            NFS_EXPORT_ATTR_TRANSPORTS: NFS_EXPORT_ATTR_TRANSPORTS_DEFAULT_VALUE,
            NFS_EXPORT_ATTR_SEC_TYPE: NFS_EXPORT_ATTR_SEC_TYPE_DEFAULT_VALUE,
            NFS_EXPORT_ATTR_SQUASH: NFS_EXPORT_ATTR_SQUASH_DEFAULT_VALUE,
            NFS_EXPORT_ATTR_EXPIRE: NFS_EXPORT_ATTR_EXPIRE_DEFAULT_VALUE,
        }
        e = RawBlock(NFS_BLOCK_EXPORT, [fsal, client], export_values)
        self.exports.append(e)
        return True

    def add_block(self, e: RawBlock) -> bool:
        eid = e.get(NFS_EXPORT_ATTR_ID)
        name = e.get(NFS_EXPORT_ATTR_PSEUDO)
        access = e.get(NFS_EXPORT_ATTR_ACCESS_TYPE)
        protocols = e.get(NFS_EXPORT_ATTR_PROTOCOLS)
        if not self.verify_params(eid, name, access, protocols):
            return False

        if self.lookup_by_id(eid) is not None:
            print(f'Export with ID {eid} already exists')
            return False

        self.exports.append(e)
        return True

    def update(self, eid: int, access: str, protocols: list, clients: list) -> bool:
        # check for params
        if not self.verify_params(access=access, protocols=protocols):
            return False

        e = self.lookup_by_id(eid)
        if e is None:
            print(f'No such export ID: {eid}')
            return False

        e.update(NFS_EXPORT_ATTR_ACCESS_TYPE, access)
        e.update(NFS_EXPORT_ATTR_PROTOCOLS, protocols)
        e.update(NFS_CLIENT_ATTR_CLIENTS, clients)

        return True

    def remove(self, eid: int) -> bool:
        e = self.lookup_by_id(eid)
        if e is not None:
            self.exports.remove(e)
            return True
        return False
