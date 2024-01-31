"""

DEVWKS-2477 - Challenge test script. Load sample webhook data and the
corresponding validated JSON test file. Parse the webhook data with
the challenge Pydantic model, and print the rendered YANG Patch message-body
along with the result of comparing the webhook data to the test data.

Copyright (c) 2023 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

__author__ = "Palmer Sample <psample@cisco.com>"
__copyright__ = "Copyright (c) 2023 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"

import argparse
import json
import os
import sys
from jinja2 import Environment, FileSystemLoader
from interface_models import InterfacePortConfig


# Set paths for the script, data files, and templates
SCRIPT_BASEPATH = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DATA_PATH = os.path.join(SCRIPT_BASEPATH, "sample_webhook_data")
TEST_DATA_PATH = os.path.join(SCRIPT_BASEPATH, "test_data")
TEMPLATE_PATH = os.path.join(SCRIPT_BASEPATH, "templates")
TEMPLATE_FILE = "interface_yang_patch.j2"


# Set the sample data and test files based on the test name
DATA_FILES = {
    "access": {
        "sample_data": "ticket_access_interface.json",
        "test_data": "challenge_access_interface.json"
    },
    "trunk": {
        "sample_data": "ticket_trunk_interface.json",
        "test_data": "challenge_trunk_interface.json"
    },
    "l3": {
        "sample_data": "ticket_l3_interface.json",
        "test_data": "challenge_l3_interface.json"
    }
}

template_env = Environment(loader=FileSystemLoader(TEMPLATE_PATH),
                           lstrip_blocks=True,
                           trim_blocks=True)
RESTCONF_TEMPLATE = template_env.get_template(TEMPLATE_FILE)


def load_json_file(file_path, file_name):
    """
    Load a JSON source file and return the Python object.

    :param file_path: Path of the file to load
    :param file_name: Filename to load
    :return: Deserialized JSON data as a Python object
    """
    print(f"Loading JSON file '{os.path.join(file_path, file_name)}'...")
    try:
        with open(os.path.join(file_path, file_name), "r", encoding="utf-8") as infile:
            source_data = json.load(infile)
    except FileNotFoundError as err:
        sys.exit(f"Unable to open source file '{os.path.join(file_path, file_name)}': {err}'")

    return source_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-a", "--access",
                        help="Access port tests",
                        action="store_const",
                        dest="test_name",
                        const="access")
    group.add_argument("-t", "--trunk",
                        help="Trunk port tests",
                        action="store_const",
                        dest="test_name",
                        const="trunk")
    group.add_argument("-l", "--layer3",
                        help="Layer 3 port tests",
                        action="store_const",
                        dest="test_name",
                        const="l3")
    args, _ = parser.parse_known_args()

    # Load the source data files
    webhook_data = load_json_file(SAMPLE_DATA_PATH, DATA_FILES[args.test_name]["sample_data"])
    test_data = load_json_file(TEST_DATA_PATH, DATA_FILES[args.test_name]["test_data"])

    # Validate the input and render the message-body
    validated_data = InterfacePortConfig.model_validate(webhook_data["ticket"])
    message_body = json.loads(RESTCONF_TEMPLATE.render(validated_data))

    print("Pydantic model output:\n")
    print(validated_data.model_dump_json(indent=2))
    print("\nYANG Patch message-body from template:\n")
    print(json.dumps(message_body, indent=2))

    if message_body == test_data:
        print("\nOK! Output data matches the tested YANG Patch message-body!")
    else:
        print("\nFAIL - Something went wrong and the output does NOT match the tested message-body")
