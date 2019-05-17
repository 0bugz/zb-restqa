import jmespath
from zb_restqa import E2ETestsuiteDriver

def sample_setup(ctxt):
    print("sample_setup invoked")

def sample_teardown(ctxt):
    print("sample_teardown invoked")

def pre_test_1(ctxt):
    print("pre_test_1: setting account_number and bearer_token")
    ctxt['account_number'] = 'ACC123XXYY-2345'
    ctxt['bearer_token'] = 'B-token'
    print("pre_test_1 invoked")
    print("pre_test_1:jmes_account_number: {}".format(jmespath.search("account_number", ctxt)))
    locals = {'ctxt':ctxt}
    print("locals: {}".format(locals))
    print("pre_test_1:eval:jmes_account_number: {}".format(eval('jmespath.search("bearer_token", ctxt)', None, locals)))

def post_test_1(ctxt):
    del ctxt['account_number']
    print("post_test_1 invoked")

def pre_test_2(ctxt):
    print("pre_test_2 invoked")

def post_test_2(ctxt):
    print("post_test_2 invoked")

def py_function(ctxt):
    print("py_function invoked")

driver = E2ETestsuiteDriver(".", {
    'pre_test_1': pre_test_1,
    'post_test_1': post_test_1,
    'pre_test_2': pre_test_2,
    'post_test_2': post_test_2,
    'py_function': py_function,
    'sample_setup': sample_setup,
    'sample_teardown': sample_teardown
})
driver.run_tests()
