"""
Interface data model definitions
"""
# pylint: disable=unused-import
from ipaddress import IPv4Interface
import re
from typing import Optional
from pydantic import BaseModel, model_validator, Field, field_validator


# Regular expression to split interface type and ID.
#
# Example input: GigabitEthernet1/0/3
# Match group 1: GigabitEthernet
# Match group 2: 1/0/3
INTERFACE_REGEX = re.compile(r"(\D+)(.*)")

# Regular expression for interface name from YANG model
# Example valid matches:
# 1/0/3
# 25.2
# 1/0/3.100
YANG_REGEX = re.compile(r'(0|[1-9][0-9]*)(/(0|[1-9][0-9]*))*(\.[0-9]*)?')
