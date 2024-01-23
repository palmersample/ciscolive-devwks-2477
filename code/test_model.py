"""
Mid-workshop testscript. This is designed to send data to an unfinished model,
which will generate a pydantic.ValidationError exception and show invalid
fields.
"""
# pylint: disable=no-name-in-module
from pprint import pprint
from interface_models import InterfaceData

example_data = {
    "ticket": {
        "network_interface_name": "GigabitEthernet1/0/3",
        "network_interface_description": "Uplink to MCO1-1N-P23A",
        "network_interface_enabled": True,
        "network_interface_mtu": ""
    }
}

print("\nTesting the InterfaceData model with example data:\n")
pprint(example_data)
print()

InterfaceData.model_validate(example_data["ticket"])
