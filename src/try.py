from ruamel.yaml import YAML
import tasks.http as task
from shared.schema import validate_schema
from jsonschema import validate, draft7_format_checker

class X(object):
    def __or__(self, other):
        print(other)


x() | x()
exit()
yaml = YAML(typ="safe", pure=True)
schema = yaml.load(task.SCHEMA)

if 'type' not in schema:
    schema = {
        "type" : "object",
        "properties": schema,
        "required": [],
    }

if 'required' not in schema:
    schema['required'] = []

props = schema.get('properties', {})
for prop in props:
    details = props.get(prop)
    if 'required' in details and prop not in schema['required']:
        schema['required'].append(prop)
        details.pop('required')

print(schema)
data = {"url": 'https://facebook/'}

result = validate_schema(schema, data)
print(result)

print(validate(data, schema, format_checker=draft7_format_checker))