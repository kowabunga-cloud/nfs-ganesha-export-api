# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

import os
import json
from bottle import Bottle
from bottle import request, response
from bottle import post, get, put, delete
from bottle import route, run
from threading import Lock

from nfsapi.common import *
from nfsapi.parser import RawBlock
from nfsapi.exports import GaneshaExportConfig

EXPORT_API_KEY_ID = 'id'
EXPORT_API_KEY_NAME = 'name'
EXPORT_API_KEY_FS = 'fs'
EXPORT_API_KEY_PATH = 'path'
EXPORT_API_KEY_ACCESS = 'access'
EXPORT_API_KEY_PROTOCOLS = 'protocols'
EXPORT_API_KEY_CLIENTS = 'clients'

class InvalidExportError(Exception):
    pass

class DuplicateExportError(Exception):
    pass

class UpdateExportError(Exception):
    pass

class NfsExport():
    def __init__(self, data):
        self.eid = None
        self.name = None
        self.fs = None
        self.path = None
        self.access = None
        self.protocols = None
        self.clients = None

        if data is None:
            raise InvalidExportError

        if type(data) == dict:
            self._from_json(data)
        elif type(data) == RawBlock:
            self._from_block(data)

        if not self._is_valid():
            raise InvalidExportError

    def _is_valid(self):
        if self.eid is None or self.name is None or self.fs is None or self.path is None or \
           self.access is None or self.protocols is None or self.clients is None:
            return False
        return True

    def _get(self, data, k):
        return data[k] if k in data else None

    def _from_json(self, js):
        self.eid = self._get(js, EXPORT_API_KEY_ID)
        self.name = self._get(js, EXPORT_API_KEY_NAME)
        self.fs = self._get(js, EXPORT_API_KEY_FS)
        self.path = self._get(js, EXPORT_API_KEY_PATH)
        self.access = self._get(js, EXPORT_API_KEY_ACCESS)
        self.protocols = self._get(js, EXPORT_API_KEY_PROTOCOLS)
        self.clients = self._get(js, EXPORT_API_KEY_CLIENTS)

    def json(self):
        return json.dumps({
            EXPORT_API_KEY_ID: self.eid,
            EXPORT_API_KEY_NAME: self.name,
            EXPORT_API_KEY_FS: self.fs,
            EXPORT_API_KEY_PATH: self.path,
            EXPORT_API_KEY_ACCESS: self.access,
            EXPORT_API_KEY_PROTOCOLS: self.protocols,
            EXPORT_API_KEY_CLIENTS: self.clients,
        })

    def _from_block(self, b):
        self.eid = b.get(NFS_EXPORT_ATTR_ID)
        self.name = b.get(NFS_EXPORT_ATTR_PSEUDO)
        self.fs = b.get(NFS_FSAL_ATTR_FS)
        self.path = b.get(NFS_EXPORT_ATTR_PATH)
        self.access = b.get(NFS_EXPORT_ATTR_ACCESS_TYPE)
        self.protocols = b.get(NFS_EXPORT_ATTR_PROTOCOLS)
        self.clients = b.get(NFS_CLIENT_ATTR_CLIENTS)

    def block(self):
        fsal_values = {
            NFS_FSAL_ATTR_NAME: NFS_FSAL_ATTR_NAME_DEFAULT_VALUE,
            NFS_FSAL_ATTR_USER: NFS_FSAL_ATTR_USER_DEFAULT_VALUE,
            NFS_FSAL_ATTR_FS: self.fs,
        }
        fsal = RawBlock(NFS_BLOCK_FSAL, [], fsal_values)

        client_values = {
            NFS_CLIENT_ATTR_CLIENTS: self.clients,
        }
        client = RawBlock(NFS_BLOCK_CLIENT, [], client_values)

        export_values = {
            NFS_EXPORT_ATTR_ID: self.eid,
            NFS_EXPORT_ATTR_PATH: self.path,
            NFS_EXPORT_ATTR_PSEUDO: self.name,
            NFS_EXPORT_ATTR_ACCESS_TYPE: self.access,
            NFS_EXPORT_ATTR_PROTOCOLS: self.protocols,
            NFS_EXPORT_ATTR_TRANSPORTS: NFS_EXPORT_ATTR_TRANSPORTS_DEFAULT_VALUE,
            NFS_EXPORT_ATTR_SEC_TYPE: NFS_EXPORT_ATTR_SEC_TYPE_DEFAULT_VALUE,
            NFS_EXPORT_ATTR_SQUASH: NFS_EXPORT_ATTR_SQUASH_DEFAULT_VALUE,
            NFS_EXPORT_ATTR_EXPIRE: NFS_EXPORT_ATTR_EXPIRE_DEFAULT_VALUE,
        }
        return RawBlock(NFS_BLOCK_EXPORT, [fsal, client], export_values)

class RestServer(Bottle):
    def __init__(self, output, host='0.0.0.0', port=54934, debug=False, reload=False):
        self.output = output
        self.host = host
        self.port = port
        self.debug = debug
        self.reload = reload
        self._app = Bottle()
        self.cfg = GaneshaExportConfig(self.output)
        self.lock = Lock()
        self._route()

    def serve(self):
        self._app.run(host=self.host, port=self.port, debug=self.debug, reloader=self.reload)

    def _prepare_headers(self):
        response.headers['Content-Type'] = 'application/json'
        response.headers['Cache-Control'] = 'no-cache'

    def _read(self):
        self.lock.acquire()
        self.cfg.read()
        self.lock.release()

    def _write(self):
        self.lock.acquire()
        data = self.cfg.dump()
        self.cfg.write(data)
        self.lock.release()
        self._reload()

    def _reload(self):
        try:
            os.system("/usr/bin/systemctl reload nfs-ganesha.service")
        except:
            print("Unable to reload NFS Ganesha service")

    def _route(self):
        self._app.route('/api/v1/export', method="GET", callback=self._list_exports)
        self._app.route('/api/v1/export', method="POST", callback=self._create_export)
        self._app.route('/api/v1/export/<eid:int>', method="GET", callback=self._read_export)
        self._app.route('/api/v1/export/<eid:int>', method="PUT", callback=self._update_export)
        self._app.route('/api/v1/export/<eid:int>', method="DELETE", callback=self._delete_export)

    def _list_exports(self):
        self._read()

        ids = []
        for e in self.cfg.exports:
            ids.append(e.values[NFS_EXPORT_ATTR_ID])

        self._prepare_headers()
        return json.dumps(ids)

    def _create_export(self):
        self._read()

        try:
            export = NfsExport(request.json)
            ok = self.cfg.add_block(export.block())
            if not ok:
                raise DuplicateExportError

        except InvalidExportError:
            response.status = 400
            return
        except DuplicateExportError:
            response.status = 409
            return

        self._write()

        self._prepare_headers()
        return export.json()

    def _read_export(self, eid):
        self._read()

        e = self.cfg.lookup_by_id(eid)
        if e is None:
            response.status = 404
            return

        export = NfsExport(e)
        self._prepare_headers()
        return export.json()

    def _update_export(self, eid):
        self._read()

        e = self.cfg.lookup_by_id(eid)
        if e is None:
            response.status = 404
            return

        export = NfsExport(request.json)
        ok = self.cfg.update(eid, export.access, export.protocols, export.clients)
        if not ok:
            response.status = 409
            return

        # read data back
        export = NfsExport(e)

        self._write()

        self._prepare_headers()
        return export.json()

    def _delete_export(self, eid):
        self._read()

        e = self.cfg.lookup_by_id(eid)
        if e is None:
            response.status = 404
            return

        ok = self.cfg.remove(eid)
        if not ok:
            response.status = 500
            return

        self._write()

        response.status = 204
        self._prepare_headers()
