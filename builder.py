#! /usr/bin/env python3
import re
import sys

import argparse
import os
import os.path

import pydantic
import yaml


class Options(pydantic.BaseModel):
    path: str = pydantic.Field(alias='path')
    output: str = pydantic.Field(alias='output')


def parse_def(content: str):  # TODO better parsing
    node = {}
    m = re.search('type:([^\n]*)\n', content)
    if m:
        node['type'] = [f.strip() for f in m.group(1).strip().split(';')[0].split(',')]
    m = re.search('help:([^\n]*)\n', content)
    if m:
        node['help'] = m.group(1).strip()
    m = re.search('multi:', content)
    node['multi'] = True if m else False
    return node


def handle_folder(path: str):
    schema = {}

    node_file = os.path.join(path, 'node.def')
    node = {}
    if os.path.isfile(node_file):
        with open(node_file, 'r') as f:
            node = parse_def(f.read())

    node_desc = node.get('help', None)
    if node_desc:
        schema['description'] = node_desc

    schema_types = [{'$ref': '#/$defs/{}'.format(t)} for t in node.get('type', [])]

    files = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]

    if files:
        schema_obj = {
            'type': 'object',
            'properties': {}
        }
        for file in files:
            file_path = os.path.join(path, file)
            if file == 'node.tag':
                schema_obj['additionalProperties'] = handle_folder(file_path)
            else:
                schema_obj['properties'][file] = handle_folder(file_path)
        if not schema_obj['properties']:
            del schema_obj['properties']
        schema_obj = {
            'oneOf': [
                schema_obj,
                {
                    'type': 'string',
                    'pattern': "^''$"
                }
            ]
        }
        schema_types.append(schema_obj)

    if len(schema_types) > 1:
        schema['oneOf'] = schema_types
    elif schema_types:
        schema.update(schema_types[0])
    else:
        print('No type for "{}"'.format(path))

    if node.get('multi', False):
        schema = {
            'type': 'array',
            'items': [schema]
        }

    return schema


def main(argv):
    default_options = Options(**{
        'path': './templates',
        'output': './unifi.schema.yaml'
    })

    parser = argparse.ArgumentParser(description='Some awesome project')
    parser.add_argument('path', type=str, default=default_options.path, help='Path to UniFi folder')
    parser.add_argument('output', type=str, default=default_options.output, help='Path to output schema file')
    args = parser.parse_args(argv[1:])

    options = Options(**vars(args))

    schema = handle_folder(options.path)
    schema.update({
        'title': 'UniFi config.gateway.json',
        '$defs': {
            'txt': {
                'type': 'string'
            },
            'u32': {
                'oneOf': [
                    {
                        'type': 'integer'
                    },
                    {
                        'type': 'string',
                        'pattern': '^\\d+$'
                    }
                ]
            },
            'bool': {
                'oneOf': [
                    {
                        'type': 'boolean'
                    },
                    {
                        'type': 'string',
                        'enum': [
                            'true',
                            'false'
                        ]
                    }
                ]
            },
            'macaddr': {
                'type': 'string'
            },
            'ipv4': {
                'type': 'string',
                'pattern': '((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])'
            },
            'ipv6': {
                'type': 'string',
                'pattern': '(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'
            },
            'ipv4net': {
                'type': 'string',
                'pattern': '((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])/(\\d+)'  # TODO mask length
            },
            'ipv6net': {
                'type': 'string',
                'pattern': '(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))/(\\d+)'  # TODO mask length
            },
        }
    })

    with open(options.output, 'w') as f:
        yaml.dump(schema, f)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
