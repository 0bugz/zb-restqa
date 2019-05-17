from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import open
from future import standard_library
standard_library.install_aliases()
from builtins import object
import os
import re
import glob
import yaml
import jmespath
import requests

from .parser import E2ESuiteParser
from .parser import get_attribute

JSON_SELECTOR_REGEX = r'(resp(\.[a-zA-Z0-9_]+)+)'
CTXT_SELECTOR_REGEX = r'(ctxt(\.[a-zA-Z0-9_]+)+)'

PATTERNS = [(JSON_SELECTOR_REGEX, 'resp'), (CTXT_SELECTOR_REGEX, 'ctxt')]

def none_function(ctxt):
    return ctxt

class StepExecutor(object):

    def smart_replace(self, expression, locals):
        expression = str(expression)
        for pattern in PATTERNS[1:]:
            # print("{}/{}".format(pattern[0], expression))
            matches = re.findall(pattern[0], expression)
            # print("expression: {}/properties: {}".format(expression, matches))
            for match in matches:
                replace_expr = match[0].replace("{}.".format(pattern[1]), '')
                replace_expr = '{}"{}"{}'.format("jmespath.search(", replace_expr, ", {})".format(pattern[1]))
                val = eval(replace_expr, None, locals)
                # print("smart_replace:replace_expr:{}/locals:{}/val:{}".format(replace_expr, locals, val))
                if val == None:
                    val = ''
                expression = expression.replace(match[0], val)
            # print("New expression: {}".format(expression))
        return expression

    def assertion_smart_replace(self, expression):
        expression = str(expression)
        for pattern in PATTERNS:
            # print("{}/{}".format(pattern[0], expression))
            matches = re.findall(pattern[0], expression)
            # print("expression: {}/properties: {}".format(expression, matches))
            for match in matches:
                replace_expr = match[0].replace("{}.".format(pattern[1]), '')
                replace_expr = "{}'{}'{}".format("jmespath.search(", replace_expr, ", {})".format(pattern[1]))
                expression = expression.replace(match[0], replace_expr)
            # print("New expression: {}".format(expression))
        return expression

    def execute(self, step, func_dict, ctxt):
        pre_step_func_name = step.pre_step_func_name
        if pre_step_func_name:
            pre_step_func = func_dict.get(pre_step_func_name, None)
            if pre_step_func == None:
                raise Exception("Function {} not in function_dict".format(pre_step_func_name))
            pre_step_func(ctxt)
        # Invoke the actual step run method - HTTPStep or PythonStep
        resp = self.run(step, func_dict, ctxt)
        locals = {
            "ctxt": ctxt,
            "resp": resp
        }
        for expression in step.assertions:
            expression = self.assertion_smart_replace(expression)
            eval(expression, None, locals)

        post_step_func_name = step.post_step_func_name
        if post_step_func_name:
            post_step_func = func_dict.get(post_step_func_name, None)
            if post_step_func == None:
                raise Exception("Function {} not in function_dict".format(post_step_func_name))
            post_step_func(ctxt)

class HTTPStepExecutor(StepExecutor):

    def run(self, step, func_dict, ctxt):
        headers = {}
        locals = {
            "ctxt": ctxt
        }
        for header_name, header_value in step.settings.headers.items():
            headers[header_name] = self.smart_replace(header_value, locals)

        optional_params = {
            "headers": headers
        }

        payload = {}
        if step.payload:
            for key, value in step.payload.items():
                payload[key] = self.smart_replace(value, locals)

        if step.method == "GET" and payload != None:
            optional_params["params"] = payload
        if step.method == "POST":
            if payload != None:
                if step.json_payload:
                    optional_params["json"] = json.dumps(payload)
                else:
                    optional_params["data"] = payload
        request_url_path = self.smart_replace(step.path, locals)
        request_url = "{}/{}".format(step.settings.base_url, request_url_path)
        print("request_url: {}".format(request_url))
        # resp = requests.request(test_http_method, request_url, **optional_params)
        # return resp.json()
        return {}

class PythonStepExecutor(StepExecutor):

    def run(self, step, func_dict, ctxt):
        invoke_method = get_attribute(func_dict, step.invoke, is_mandatory=True)
        return invoke_method(ctxt)

class E2ETestsuiteDriver(object):

    def __init__(self, test_suite_dir, function_dict):
        self.test_suite_dir = test_suite_dir
        self.function_dict = function_dict

    def _get_func(self, func_name):
        func = none_function
        if func_name:
            func = self.function_dict.get(func_name, None)
            if func == None:
                raise Exception("Function {} not in function_dict".format(func_name))
        return func

    def run_tests(self):
        http_step_executor = HTTPStepExecutor()
        py_step_executor = PythonStepExecutor()

        parser = E2ESuiteParser()
        test_suite_files_expr = "{}/*_e2e_suite.yml".format(self.test_suite_dir)
        suites = glob.glob(test_suite_files_expr)
        for suite in suites:
            ctxt = {}
            e2e_test_suite = parser.parse(suite)
            print("Executing flow/suite: {}".format(e2e_test_suite.name))

            setup_func = self._get_func(e2e_test_suite.setup_func_name)
            setup_func(ctxt)

            for step in e2e_test_suite.steps:
                if step.type == "HTTPStep":
                    http_step_executor.execute(step, self.function_dict, ctxt)
                elif step.type == "PythonStep":
                    py_step_executor.execute(step, self.function_dict, ctxt)

            teardown_func = self._get_func(e2e_test_suite.teardown_func_name)
            teardown_func(ctxt)
