"""
Interface data model definitions
"""
# pylint: disable=unused-import, line-too-long, raise-missing-from
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


class InterfacePortConfig(InterfaceData):
    """
    Workshop bonus challenge: model for interface switchport configuration.
    """
    switchport_mode: Optional[str] = None
    switchport_native_vlan: Optional[int] = None
    switchport_allowed_vlans: Optional[str] = None
    interface_ip4_address: Optional[IPv4Interface] = Field(validation_alias="network_interface_ip4_address",
                                                           default=None)

    @model_validator(mode="before")
    @classmethod
    def set_switchport_details(cls, data):
        """
        Given a source webhook field with variable colon-separated fields,
        split the field and populate the switchport mode, native vlan, and
        allowed_vlans if defined.

        Examples:

        "access:100"
            -> {
                  "switchport_mode": "access",
                  "switchport_native_vlan": 100
               }

        "trunk:100:"
            -> {
                  "switchport_mode": "trunk",
                  "switchport_native_vlan": 100
               }

        "l3:"
            -> {
                  "switchport_mode": None
               }

        :param data: Input data dict passed to the Pydantic model
        :return: Input data updated with the parsed dictionary
        """
        switchport_mode, primary_vlan = data["network_switchport_mode_and_vlan"].split(":", 1)
        if switchport_mode.lower() == "l3":
            switchport_mode = None

        elif switchport_mode.lower() == "access":
            if primary_vlan == "":
                primary_vlan = None
            data.update({"switchport_native_vlan": primary_vlan})

        elif switchport_mode.lower() == "trunk":
            native_vlan, allowed_vlans = primary_vlan.split(":")
            if native_vlan == "":
                native_vlan = None
            data.update({"switchport_native_vlan": native_vlan,
                         "switchport_allowed_vlans": allowed_vlans})

        data.update({"switchport_mode": switchport_mode})
        return data

    @model_validator(mode="before")
    @classmethod
    def remove_unset_ip4_addr(cls, data):
        """
        If the input field "network_interface_ip4_address" is an empty string,
        delete the key from the input before further model processing to allow
        the default to be applied.

        :param data: Input data dict passed to the Pydantic model
        :return: Input data updated with the parsed dictionary
        """
        if data.get("network_interface_ip4_address", "") == "":
            del data["network_interface_ip4_address"]
        return data

    @field_validator("switchport_native_vlan")
    @classmethod
    def validate_native_vlan(cls, v):
        """
        Test that the primary/native VLAN is in the range 1..4094.

        :param v: Value of the field being validated (switchport_native_vlan)
        :raises: ValueError if the VLAN is out of range
        :return: Validated field value
        """
        if v and not 1 <= int(v) <= 4094:
            raise ValueError("VLAN must be in the range 1-4094.")
        return v

    @field_validator("switchport_allowed_vlans")
    @classmethod
    def validate_allowed_vlans(cls, v):
        """
        Remove any spaces from the input field, then split the allowed VLAN
        list on expected delimiters (,-). Test that each allowed VLAN is in
        the range 1..4094.

        :param v: Value of the field being validated (switchport_allowed_vlans)
        :raises: ValueError if any VLAN is out of range
        :return: Validated field value
        """
        if v == "":
            v = None
        else:
            v = v.replace(" ", "")  # Remove any whitespace from allowed vlans
            for vlan in re.split(r",|-", v):
                if not 1 <= int(vlan) <= 4094:
                    raise ValueError(f"VLAN '{vlan}' error: must be in the range 1-4094")
        return v
