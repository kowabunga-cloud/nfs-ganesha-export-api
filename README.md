<p align="center">
  <a href="https://www.kowabunga.cloud/?utm_source=github&utm_medium=logo" target="_blank">
    <picture>
      <source srcset="https://raw.githubusercontent.com/kowabunga-cloud/infographics/master/art/kowabunga-title-white.png" media="(prefers-color-scheme: dark)" />
      <source srcset="https://raw.githubusercontent.com/kowabunga-cloud/infographics/master/art/kowabunga-title-black.png" media="(prefers-color-scheme: light), (prefers-color-scheme: no-preference)" />
      <img src="https://raw.githubusercontent.com/kowabunga-cloud/infographics/master/art/kowabunga-title-black.png" alt="Kowabunga" width="800">
    </picture>
  </a>
</p>

# NFS Ganesha Export API

This program is a simple REST API web server, exposing management and configuration of Ganesha NFS exports configuration.

[![License: Apache License, Version 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://spdx.org/licenses/Apache-2.0.html)
[![PyPi page link -- version](https://img.shields.io/pypi/v/kowabunga.svg)](https://pypi.python.org/pypi/nfs-ganesha-export-api)
<img src="https://img.shields.io/badge/python-3.8 | 3.9 | 3.10 | 3.11 | 3.12-blue.svg" alt="python">
[![Build Status](https://github.com/kowabunga-cloud/nfs-ganesha-export-api/actions/workflows/python.yml/badge.svg)](https://github.com/kowabunga-cloud/nfs-ganesha-export-api/actions/workflows/python.yml)

## Operational Requirements

This web server manages local configuration files only. Consequently, it has to run on the same server where Ganesha NFS daemon is running on.

The API server is only meant to build up a valid exports configuration file (and reload daemon accordingly). It is not meant to create and manage the underlying volumes that are to be shared through NFS, if any.

## API

The following REST API endpoints are exposed:

* **GET /api/v1/export**: retrives list of all export IDs as integers

* **POST /api/v1/export**: Create a new NFS export using export JSON representation as body.

* **GET /api/v1/export/{eid}**: Get NFS export JSON representation from **eid** identifier.

* **PUT /api/v1/export/{eid}**: Update a given NFS export. Only access type, protocols and clients list can be updated.

* **DELETE /api/v1/export/{eid}**: Delete a given NFS export.

Below is NFS export JSON object representation:

```json
{
  "id": uint16,
  "name": string,
  "fs": string,
  "path": string,
  "access": string,
  "protocols": [int],
  "clients": [string],
}
```

where:

* **id** is a unique integer, from 1 to 65535,
* **name** is a string, identifying the exporter share's name,
* **fs** is a string, identifying the underlying Ceph filesystem,
* **path** is a string, identifying the local path to be exported,
* **access** is a string, either **RO** or **RW**,
* **protocols** is a list of integer, representing NFS protocol version. Supported are **3** and **4**,
* **clients** is a list of string, representing CIDR values (e.g. 192.168.0.0/24) of authorized clients,

## License

Licensed under [Apache License, Version 2.0](https://opensource.org/license/apache-2-0), see [`LICENSE`](LICENSE).
