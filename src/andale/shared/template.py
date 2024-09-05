import os.path
import json
from jinja2.sandbox import SandboxedEnvironment
from jinja2 import meta
from datetime import datetime
import xmltodict
import jmespath
from jinja2_ansible_filters import AnsibleCoreFiltersExtension
from jinja2.nativetypes import NativeCodeGenerator, NativeTemplate
from bs4 import BeautifulSoup
from typing import Any


class NativeEnvironment(SandboxedEnvironment):
    template_class = NativeTemplate
    code_generator_class = NativeCodeGenerator
    template_class: Any


def filter_decoder(value, format="ndjson", options={}):
    if format not in ["json", "csv", "ndjson", "xml"]:
        return value

    if format == "ndjson":
        if isinstance(value, str):
            return [json.loads(l) for l in value.split("\n")]
        else:
            print(type(value))
            return [json.loads(l) for l in value.readlines()]

    if format == "json":
        if isinstance(value, str):
            return json.loads(value)
        else:
            return json.load(value)

    if format == "xml":
        if isinstance(value, str):
            return xmltodict.parse(value)
        v = xmltodict.parse(value.read())
        print("IN_FILTER", type(v))
        return v
    return value


def filter_dump(value):
    print(json.dumps(value, indent=4))
    return json.dumps(value, indent=4)


def filter_jmespath(value, path):
    return jmespath.search(path, value)


def get_secret(value=None, key=None):
    return "zSQ4zQosPCEG7F2utCaLpqANAbi4AqLaMpMsXybrIgQ"


def eval_conditional(expr, vars, default=False):
    env = SandboxedEnvironment()
    compiled = env.compile_expression(expr)
    try:
        return compiled(**vars) == True
    except Exception as err:
        print(err)
        return default


def render_string(template, data):
    # https://jinja.palletsprojects.com/en/2.11.x/api/#policies
    env = NativeEnvironment(extensions=[AnsibleCoreFiltersExtension])
    env.filters["decoder"] = filter_decoder
    env.filters["jmespath"] = filter_jmespath
    env.globals["now"] = datetime.utcnow()
    env.globals["get_secret"] = get_secret

    tmp = {**data, **{"data_dir": os.path.abspath(".data")}}
    ast = env.parse(template.strip(), tmp)
    # print("UNDECLARED! {}".format(meta.find_undeclared_variables(ast)))
    template = env.from_string(ast)
    return template.render(**tmp)


def render_recursive(target, data):
    if isinstance(target, str):
        return render_string(target, data)

    if isinstance(target, list):
        return [render_recursive(i, data) for i in target]

    if isinstance(target, dict):
        new_target = {}
        for attr in target:
            val = target[attr]
            key = render_string(attr, data)
            new_target[key] = render_recursive(val, data)
        return new_target

    return target
