from jsonschema import Draft7Validator, validators, draft7_format_checker, validate
from ruamel.yaml import YAML


def extend_with_default(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])

        for error in validate_properties(
            validator,
            properties,
            instance,
            schema,
        ):
            yield error

    return validators.extend(
        validator_class,
        {"properties": set_defaults},
    )


DefaultValidatingDraft7Validator = extend_with_default(Draft7Validator)


def validate_schema(schema, data):
    if "type" not in schema:
        schema = {
            "type": "object",
            "properties": schema,
            "required": [],
        }

    if "required" not in schema:
        schema["required"] = []

    props = schema.get("properties", {})
    for prop in props:
        details = props.get(prop)
        if "required" in details and prop not in schema["required"]:
            schema["required"].append(prop)
            details.pop("required")

    validator = DefaultValidatingDraft7Validator(
        schema, format_checker=draft7_format_checker
    )
    errors = {}
    for error in sorted(validator.iter_errors(data), key=str):
        print(error)
        attr = ".".join(error.absolute_path)
        errors[attr] = error.message
    return errors


def validate_params(module, params):
    if not hasattr(module, "SCHEMA"):
        print("NO schema!")

        exit()

    yaml = YAML(typ="safe", pure=True)
    schema = yaml.load(module.SCHEMA)

    result = validate_schema(schema, params)
    print(result)

    # print(validate(params, schema, format_checker=draft7_format_checker))
