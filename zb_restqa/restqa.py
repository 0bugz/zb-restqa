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

JSON_SELECTOR_REGEX = r'(resp(\.[a-zA-Z0-9]+)+)'

def none_function(ctxt):
    return ctxt

class RestTestsuiteDriver(object):

    def __init__(self, test_suite_dir, function_dict):
        self.test_suite_dir = test_suite_dir
        self.function_dict = function_dict

    def run_tests(self):

        test_suite_files_expr = "{}/*_test_suite.yml".format(self.test_suite_dir)
        suites = glob.glob(test_suite_files_expr)
        for suite in suites:
            with open(suite, 'r') as yaml_in:
                suite_settings = yaml.safe_load(yaml_in)
                suite_settings = suite_settings["suite"]
                suite_base_url = suite_settings.get("base_url", None)
                print("suite_base_url: {}".format(suite_base_url))
                suite_name = suite_settings.get("name", None)
                suite_setup = suite_settings.get("setup", None)
                suite_teardown = suite_settings.get("teardown", None)
                print("suite: {}::setup_function: {}::teardown_function: {}".format(suite_name, suite_setup, suite_teardown))
                try:
                    ctxt = {}
                    setup_function = self.function_dict.get(suite_setup, none_function)
                    ctxt = setup_function(ctxt)
                    tests = suite_settings.get("tests", [])
                    for test_settings in tests:
                        try:
                            test_name = test_settings.get("name", "None")
                            test_json_payload = test_settings.get("json", False)
                            test_http_headers = test_settings.get("headers", [])
                            test_http_method = test_settings.get("method", "GET")
                            test_http_path = test_settings.get("path", None)
                            test_http_payload = test_settings.get("payload", None)
                            test_pre = test_settings.get("pre_test", None)
                            test_post = test_settings.get("post_test", None)
                            test_assertions = test_settings.get("assertions", None)
                            headers = {}
                            for test_http_header in test_http_headers:
                                for header_name, header_value in test_http_header.items():
                                    headers[header_name] = header_value
                            optional_params = {
                                "headers": headers
                            }
                            if test_http_method == "GET" and test_http_payload != None:
                                optional_params["params"] = test_http_payload
                            if test_http_method == "POST":
                                if test_http_payload != None:
                                    if test_json_payload:
                                        optional_params["json"] = json.dumps(test_http_payload)
                                    else:
                                        optional_params["data"] = test_http_payload
                            request_url = "{}{}".format(suite_base_url, test_http_path)
                            print("request_url: {}".format(request_url))
                            test_pre_function = self.function_dict.get(test_pre, none_function)
                            ctxt = test_pre_function(ctxt)
                            try:
                                resp = requests.request(test_http_method, request_url, **optional_params)
                                resp = resp.json()
                                locals = {
                                    "ctxt": ctxt,
                                    "resp": resp
                                }
                                for expression in test_assertions:
                                    matches = re.findall(JSON_SELECTOR_REGEX, expression)
                                    print("expression: {}/properties: {}".format(expression, matches))
                                    for match in matches:
                                        replace_expr = match[0].replace('resp\.', '')
                                        replace_expr = "{}'{}'{}".format("jmespath.search(", replace_expr ,", resp)")
                                        expression = expression.replace(match[0], replace_expr)
                                    print("New expression: {}".format(expression))
                                    eval(expression, None, locals)
                            except Exception as e2:
                                print("Exception occured while executing suite: {} / test: {} / {}".format(suite_name, test_name, e2))
                            test_post_function = self.function_dict.get(test_post, none_function)
                            ctxt = test_post_function(ctxt)
                        except Exception as e1:
                            print("Exception occured while executing suite: {} / test: {} / {}".format(suite_name, test_name, e1))
                    teardown_function = self.function_dict.get(suite_teardown, none_function)
                    ctxt = teardown_function(ctxt)
                except Exception as e:
                    print("Exception occured while executing test suite: {}/{}".format(suite_name, e))
