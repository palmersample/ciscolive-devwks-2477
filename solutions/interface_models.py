"""
Interface data model definitions
"""
# pylint: disable=unused-import, line-too-long, raise-missing-from
import ipaddress
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


class InterfaceData(BaseModel):
    """
    Interface model to set needed fields for Jinja2-generated RESTCONF
    message-body
    """
    interface_type: str
    interface_name: str
    interface_enabled: bool = Field(validation_alias="network_interface_enabled")
    interface_description: Optional[str] = Field(validation_alias="network_interface_description",
                                                 min_length=0,
                                                 max_length=200)
    interface_mtu: int = Field(validation_alias="network_interface_mtu",
                               ge=1500,
                               le=9000,
                               default=1500)

    @model_validator(mode="before")
    @classmethod
    def set_interface_details(cls, data):
        """
        Parse the interface name from the device into components needed by the
        YANG model.

        Example: GigabitEthernet1/0/3 is parsed into a dictionary:
          {
            "interface_type": "GigabitEthernet",
            "interface_name": "1/0/3"
          }

        :param data: Input data dict passed to the Pydantic model
        :return: Input data updated with the parsed dictionary
        """
        try:
            interface_type, interface_name = INTERFACE_REGEX.match(data["network_interface_name"]).groups()
        except Exception:
            raise ValueError("Unable to extract the interface type and name from the ticket.")

        data.update({"interface_type": interface_type,
                     "interface_name": interface_name})
        return data

    @model_validator(mode="before")
    @classmethod
    def remove_unset_mtu(cls, data):
        """
        If the network_interface_mtu field is an empty string on input, delete
        the key from the input data so the default value is applied.

        :param data: Input data dict passed to the Pydantic model
        :return: Input data with network_interface_mtu deleted if empty string
        """
        if data.get("network_interface_mtu", "") == "":
            del data["network_interface_mtu"]
        return data

    @field_validator("interface_name")
    @classmethod
    def validate_interface_name(cls, v):
        """
        Validate the interface name is compliant with the YANG model
        definition for this device type.

        :param v: Value of the field being validated (interface_name)
        :raises: ValueError is the name is invalid
        :return: Validated field value
        """
        if not YANG_REGEX.match(v):
            raise ValueError(f"Invalid name for interface: '{v}'")
        return v

    @field_validator("interface_description")
    @classmethod
    def empty_str_to_none(cls, v):
        """
        If the interface description field is an empty string, set the value
        to None. Otherwise, keep the description as-is.

        :param v: Value of the field being validated (interface_description)
        :return: None is input is an empty string, value otherwise
        """
        if v == "":
            return None
        return v
