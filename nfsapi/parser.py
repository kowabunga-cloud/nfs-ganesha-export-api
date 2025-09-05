# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

from typing import cast, List, Dict, Any, Optional, TYPE_CHECKING

from nfsapi.common import *

def inject(data, indent, val):
    res = data
    for i in range(0, indent):
        res += " "
    res += val + '\n'
    return res

class RawBlock():
    def __init__(self, block_name: str, blocks: List['RawBlock'] = [], values: Dict[str, Any] = {}):
        if not values:  # workaround mutable default argument
            values = {}
        if not blocks:  # workaround mutable default argument
            blocks = []
        self.block_name = block_name
        self.blocks = blocks
        self.values = values

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RawBlock):
            return False
        return self.block_name == other.block_name and \
            self.blocks == other.blocks and \
            self.values == other.values

    def __repr__(self) -> str:
        return f'RawBlock({self.block_name!r}, {self.blocks!r}, {self.values!r})'

    def update(self, k: str, v: Any):
        if k in self.values:
            self.values[k] = v
            return

        # try to update a sub-block config if not in main one
        for b in self.blocks:
            b.update(k, v)

    def get(self, k: str):
        if k in self.values:
            return self.values[k]

        # try to look iwthin a sub-block config if not in main one
        for b in self.blocks:
            v = b.get(k)
            if v is not None:
                return v

        return None

    def export(self, indent=0) -> str:
        res = inject("", indent, self.block_name + ' {')
        for v in self.values:
            val = self.values[v]
            if type(val) == str:
                if v in [NFS_EXPORT_ATTR_PATH, NFS_EXPORT_ATTR_PSEUDO, NFS_FSAL_ATTR_USER, NFS_FSAL_ATTR_FS]:
                    value = f'"{val}"'
                else:
                    value = val
            elif type(val) == list:
                string_val = [str(x) for x in val]
                value = ', '.join(string_val)
            else:
                value = val
            line = f'{v} = {value};'
            res = inject(res, indent + 2, line)
        for b in self.blocks:
            res += '\n'
            res = inject(res, indent, b.export(indent + 2))
        res = inject(res, indent, '}')
        return res

class GaneshaConfParser:
    def __init__(self, raw_config: str):
        self.pos = 0
        self.text = ""
        for line in raw_config.split("\n"):
            line = line.lstrip()

            if line.startswith("%"):
                self.text += line.replace('"', "")
                self.text += "\n"
            elif line.startswith("#"):
                pass
            else:
                self.text += "".join(line.split())

    def stream(self) -> str:
        return self.text[self.pos:]

    def last_context(self) -> str:
        return f'"...{self.text[max(0, self.pos - 30):self.pos]}<here>{self.stream()[:30]}"'

    def parse_block_name(self) -> str:
        idx = self.stream().find('{')
        if idx == -1:
            raise Exception(f"Cannot find block name at {self.last_context()}")
        block_name = self.stream()[:idx]
        self.pos += idx + 1
        return block_name

    def parse_block_or_section(self) -> RawBlock:
        if self.stream().startswith("%url "):
            # section line
            self.pos += 5
            idx = self.stream().find('\n')
            if idx == -1:
                value = self.stream()
                self.pos += len(value)
            else:
                value = self.stream()[:idx]
                self.pos += idx + 1
            block_dict = RawBlock('%url', values={'value': value})
            return block_dict

        block_dict = RawBlock(self.parse_block_name().upper())
        self.parse_block_body(block_dict)
        if self.stream()[0] != '}':
            raise Exception("No closing bracket '}' found at the end of block")
        self.pos += 1
        return block_dict

    def parse_parameter_value(self, raw_value: str) -> Any:
        if raw_value.find(',') != -1:
            return [self.parse_parameter_value(v.strip())
                    for v in raw_value.split(',')]
        try:
            return int(raw_value)
        except ValueError:
            if raw_value == "true":
                return True
            if raw_value == "false":
                return False
            if raw_value.find('"') == 0:
                return raw_value[1:-1]
            return raw_value

    def parse_stanza(self, block_dict: RawBlock) -> None:
        equal_idx = self.stream().find('=')
        if equal_idx == -1:
            raise Exception("Malformed stanza: no equal symbol found.")
        semicolon_idx = self.stream().find(';')
        parameter_name = self.stream()[:equal_idx]#.lower()
        parameter_value = self.stream()[equal_idx + 1:semicolon_idx]
        block_dict.values[parameter_name] = self.parse_parameter_value(parameter_value)
        self.pos += semicolon_idx + 1

    def parse_block_body(self, block_dict: RawBlock) -> None:
        while True:
            if self.stream().find('}') == 0:
                # block end
                return

            last_pos = self.pos
            semicolon_idx = self.stream().find(';')
            lbracket_idx = self.stream().find('{')
            is_semicolon = (semicolon_idx != -1)
            is_lbracket = (lbracket_idx != -1)
            is_semicolon_lt_lbracket = (semicolon_idx < lbracket_idx)

            if is_semicolon and ((is_lbracket and is_semicolon_lt_lbracket) or not is_lbracket):
                self.parse_stanza(block_dict)
            elif is_lbracket and ((is_semicolon and not is_semicolon_lt_lbracket)
                                  or (not is_semicolon)):
                block_dict.blocks.append(self.parse_block_or_section())
            else:
                raise Exception("Malformed stanza: no semicolon found.")

            if last_pos == self.pos:
                raise Exception("Infinite loop while parsing block content")

    def parse(self) -> List[RawBlock]:
        blocks = []
        while self.stream():
            blocks.append(self.parse_block_or_section())
        return blocks
