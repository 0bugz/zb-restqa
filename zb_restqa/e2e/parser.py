from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import open
from future import standard_library
standard_library.install_aliases()
from builtins import object
import re
import yaml

def get_attribute(obj, attribute_name, is_mandatory = False):
    attr_value = obj.get(attribute_name, None)
    if attr_value == None and is_mandatory:
        raise Exception("{} is mandatory but not specified".format(attribute_name))
    return attr_value

class HTTPSettings(object):

    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = {}
        if headers:
            for header in headers:
                for key, value in header.items():
                    self.headers[key] = value

class Step(object):

    def __init__(self):
        self.pre_step_func_name = None
        self.post_step_func_name = None
        self.assertions = None
        self.type = "Abstract"

    def parse_step(self, step_settings):
        self.name = get_attribute(step_settings, "name")
        self.pre_step_func_name = get_attribute(step_settings, "pre_step")
        self.post_step_func_name = get_attribute(step_settings, "post_step")
        # print(step_settings)
        self.assertions = get_attribute(step_settings, "assertions", is_mandatory=True)
        # print("assertions: ".format(self.assertions))

class HTTPStep(Step):

    def __init__(self, step_http_settings, flow_http_settings):
        super().__init__()
        self.type = "HTTPStep"
        step_base_url = get_attribute(step_http_settings, "base_url")
        step_http_headers = get_attribute(step_http_settings, "headers")
        path = get_attribute(step_http_settings, "path")
        method = get_attribute(step_http_settings, "method")
        json_payload = get_attribute(step_http_settings, "json_payload")
        payload = get_attribute(step_http_settings, "payload")
        print("payload: {}".format(payload))

        step_settings = HTTPSettings(step_base_url, step_http_headers)
        flow_base_url = flow_http_settings.base_url
        step_base_url = step_settings.base_url
        if flow_base_url == None and step_base_url == None:
            raise Exception("base_url is mandatory either at the flow level or step level, none specified")
        step_settings.base_url = step_base_url if step_base_url else flow_base_url
        flow_http_headers = flow_http_settings.headers
        step_http_headers = step_settings.headers
        for key, value in flow_http_headers.items():
            override_val = get_attribute(step_http_headers, key)
            if override_val != None:
                print("Key {}: Value {} from Step HTTP Headers overrides {} from Flow HTTP Headers".format(key, override_val, value))
            else:
                step_http_headers[key] = value
        step_settings.headers = step_http_headers

        self.json_payload = json_payload if json_payload else False
        self.payload = payload
        self.method = method if method else 'GET'
        self.path = path if path else ''
        self.settings = step_settings
        self.url = "{}/{}".format(step_settings.base_url, self.path)

class PythonStep(Step):

    def __init__(self, step_py_settings):
        super().__init__()
        self.type = "PythonStep"
        self.invoke = get_attribute(step_py_settings, "invoke", is_mandatory=True)

class E2ETestSuite(object):

    def __init__(self, name, setup_func_name, teardown_func_name):
        self.name = name
        self.setup_func_name = setup_func_name
        self.teardown_func_name = teardown_func_name
        self.http_settings = None
        self.steps = []

    def parse_http_settings(self, http_settings):
        http_base_url = get_attribute(http_settings, "base_url")
        http_headers = get_attribute(http_settings, "headers")
        self.http_settings = HTTPSettings(http_base_url, http_headers)

    def parse_step(self, step_settings):
        step = None
        step_http_settings = get_attribute(step_settings, "http")
        if step_http_settings != None:
            step = HTTPStep(step_http_settings, self.http_settings)
        step_py_settings = get_attribute(step_settings, "python")
        if step_py_settings != None:
            step = PythonStep(step_py_settings)
        step.parse_step(step_settings)
        return step

    def set_steps(self, steps):
        for step in steps:
            self.steps.append(self.parse_step(step))

class E2ESuiteParser(object):

    def parse(self, suite_config_path):
        e2e_test_suite = None
        with open(suite_config_path, 'r') as yaml_in:
            suite_settings = yaml.safe_load(yaml_in)
            suite = suite_settings.get("suite", None)
            if suite == None:
                raise Exception("Invalid E2E test suite config file: suite not defined")

            name = get_attribute(suite, "name", is_mandatory=True)
            setup_func_name = get_attribute(suite, "setup")
            teardown_func_name = get_attribute(suite, "teardown")

            e2e_test_suite = E2ETestSuite(name, setup_func_name, teardown_func_name)
            http_settings = get_attribute(suite, "http")
            e2e_test_suite.parse_http_settings(http_settings)
            steps = get_attribute(suite, "steps", is_mandatory=True)
            e2e_test_suite.set_steps(steps)
        return e2e_test_suite
