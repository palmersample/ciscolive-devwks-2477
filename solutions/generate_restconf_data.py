"""
Generate a YANG Patch message-body from a Jinja2 template after data has
been validated by the Pydantic InterfaceData model, then load expected output
and verify the generated message-body matches the test data.
"""
import json
import sys
from jinja2 import Environment, FileSystemLoader
from interface_models import InterfaceData

# Define filenames to import
#
# Jinja2 path and template name for YANG Patch message-body:
TEMPLATE_DIR = "templates/"
TEMPLATE_FILE = "interface_yang_patch.j2"

# Sample webhook data from ITSM:
SAMPLE_DATA_FILE = "sample_webhook_data/ticket_trunk_interface.json"

# Validated message-body for generated output comparison:
SAMPLE_TEST_DATA_FILE = "test_data/expected_trunk_interface.json"

# Prepare the Jinaj2 environment and load the template:
template_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR),
                           lstrip_blocks=True,
                           trim_blocks=True)
interface_template = template_env.get_template(TEMPLATE_FILE)
print()

# Load the sample webhook data and the expected output:
try:
    with open(SAMPLE_DATA_FILE, "r", encoding="utf-8") as sample_data:
        input_data = json.load(sample_data)
except FileNotFoundError as err:
    sys.exit(f"Unable to open sample webhook data file '{SAMPLE_DATA_FILE}': {err}")

validated_data = InterfaceData.model_validate(input_data["ticket"])

output_data = json.loads(interface_template.render(validated_data))
print(output_data)

try:
    with open(SAMPLE_TEST_DATA_FILE, "r", encoding="utf-8") as sample_test_data:
        test_data = json.load(sample_test_data)
except FileNotFoundError as err:
    sys.exit(f"Unable to open expected output test data '{SAMPLE_TEST_DATA_FILE}': {err}")

if output_data == test_data:
    print("\nOK! Output data matches the tested YANG Patch message-body!")
else:
    print("\nFAIL - Something went wrong and the output does NOT match the tested message-body")
