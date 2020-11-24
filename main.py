#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import fnmatch
import json
import jsonschema
import pandas as pd


BASEDIR = os.path.abspath(
    os.path.dirname(__file__)
)

EVENTDIR = os.path.join(BASEDIR, 'event')
SCHEMADIR = os.path.join(BASEDIR, 'schema')


def get_files(path, extension='json'):
    files_name = os.listdir(path)
    for file in files_name:
        if fnmatch.fnmatch(file, "*.{}".format(extension)):
            yield os.path.join(path, file)


def read_file(path):
    with open(path, 'r') as file:
        json_object = json.load(file)
    return json_object


def recommendations(message):
    recommend = None
    if re.search('is a required property', message):
        recommend = '{} - {}'.format(
            'Add property to json file',
            re.findall(r'[\'](.*?)[\']', message)[0]
        )
    elif re.search('is not of type', message):
        recommend = '{} - {}'.format(
            'Enter the correct value in place',
            re.findall(r'[\'](.*?)[\']', message)[0]
        )

    return recommend


def validate(file, json_data, schema):
    validator = jsonschema.Draft7Validator(schema)

    errors = sorted(
        validator.iter_errors(json_data['data']),
        key=lambda e: e.path
    )

    info = []
    for error in errors:
        info.append({
            'message': error.message,
            'filename': file,
            'schemaname': json_data['event'].replace(' ', ''),
            'info': recommendations(error.message)
            }
        )

    return info


def file_analysis(json_dir, schema_dir):

    result = []
    for json_file in get_files(json_dir):
        json_data = read_file(json_file)
        if json_data is not None and bool(json_data):
            # Путь к файлу схемы
            schema_file = os.path.join(
                schema_dir,
                '{}.schema'.format(json_data['event'].replace(' ', ''))
            )
            if os.path.exists(schema_file):
                schema = read_file(schema_file)
                result.extend(validate(
                    os.path.basename(json_file),
                    json_data,
                    schema
                ))
            else:
                result.append({
                    'message': None,
                    'filename': os.path.basename(json_file),
                    'schemaname': None,
                    'info': 'File schema for json not found'
                    }
                )
        else:
            result.append({
                'message': 'file format incorrect',
                'filename': os.path.basename(json_file),
                'schemaname': None,
                'info': 'Enter the correct format for the file'
                }
            )

    return pd.DataFrame.from_records(result).to_html()


def main():
    table = file_analysis(EVENTDIR, SCHEMADIR)
    with open('README.md', 'w') as file:
        file.write(table)


if __name__ == '__main__':
    main()
