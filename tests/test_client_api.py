"""Python 2.7 tests for the non-executing private-API fingerprint guard."""
import imp
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = imp.load_source('hcp_client_api', os.path.join(ROOT, 'tools', 'check-client-api.py'))


class ClientApiTests(unittest.TestCase):
    def test_filename_and_line_metadata_do_not_change_contract(self):
        first = compile('def example():\n    return 1\n', 'first.py', 'exec')
        second = compile('\n\n# moved\ndef example():\n    return 1\n', 'second.py', 'exec')
        self.assertEqual(API.fingerprint(first), API.fingerprint(second))

    def test_function_body_change_is_detected(self):
        first = compile('def example():\n    return 1\n', 'test.py', 'exec')
        second = compile('def example():\n    return 2\n', 'test.py', 'exec')
        self.assertNotEqual(API.fingerprint(first), API.fingerprint(second))

    def test_model_property_default_change_is_detected(self):
        source = 'class Model:\n    def __init__(self, properties=%d, commands=3):\n        pass\n'
        first = compile(source % 4, 'test.py', 'exec')
        second = compile(source % 5, 'test.py', 'exec')
        self.assertNotEqual(API.fingerprint(first), API.fingerprint(second))

    def test_missing_or_changed_hook_fails_closed(self):
        contract = {'nodes': {'model.pyc': {'<module>.Model': 'expected'}}}
        self.assertRaises(ValueError, API.validate, {}, contract)
        self.assertRaises(ValueError, API.validate, {'model.pyc': {'<module>.Model': 'changed'}}, contract)

    def test_exact_contract_passes(self):
        observed = {'model.pyc': {'<module>.Model': 'expected'}}
        self.assertEqual(API.validate(observed, {'nodes': observed}), 1)

    def test_walk_never_executes_client_code(self):
        code = compile('raise RuntimeError("must not execute")\nclass Model:\n    pass\n', 'test.py', 'exec')
        self.assertIn('<module>.Model', dict(API.walk(code)))
        self.assertEqual(len(API.fingerprint(code)), 64)


if __name__ == '__main__':
    unittest.main()
