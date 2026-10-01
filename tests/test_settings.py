# -*- coding: utf-8 -*-
"""Check template upgrades seed saved HCP values without requiring the client."""
from __future__ import print_function

import ast
import collections
import sys
import types
import unittest


class Templates(object):
    @staticmethod
    def createLabel(*args):
        return {}

    createEmpty = createLabel

    @staticmethod
    def createCheckbox(label, key, value, *args):
        return {'varName': key, 'value': value}

    @staticmethod
    def createDropdown(label, key, options, value):
        return {'varName': key, 'value': value, 'options': options}

    @staticmethod
    def createNumericStepper(label, key, value, *args, **kwargs):
        return {'varName': key, 'value': value}


class SettingsTest(unittest.TestCase):
    def test_template_upgrade_preserves_current_values(self):
        with open(SOURCE_PATH, 'rb') as source:
            tree = ast.parse(source.read(), SOURCE_PATH)
        functions = set(('_register_settings', '_settings_filter_enabled',
                         '_sort_mode', '_sort_descending', '_carousel_rows', '_carousel_auto'))
        constants = set(('FILTER_ORDER', 'SORT_ORDER', 'SETTINGS_RANDOM_SORT_OPTIONS'))
        body = [node for node in tree.body if
                (isinstance(node, ast.FunctionDef) and node.name in functions) or
                (isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id in constants for t in node.targets))]
        code = compile(ast.Module(body=body), SOURCE_PATH, 'exec')
        captured = []
        api = types.ModuleType('gui.modsSettingsApi')
        api.templates = Templates
        api.g_modsSettingsApi = type('API', (), {
            'setModTemplate': lambda _self, *args: captured.append(args)})()
        saved_modules = dict((name, sys.modules.get(name)) for name in ('gui', 'gui.modsSettingsApi'))
        sys.modules['gui'] = types.ModuleType('gui')
        sys.modules['gui.modsSettingsApi'] = api
        try:
            for auto in (True, False):
                ns = {
                    'SETTINGS_REGISTERED': False,
                    'CONFIG': {'enabled': False, 'filters': {'enabled': ['non_elite']},
                               'cardStats': {'enabled': False, 'minimumBattles': 37},
                               'sorting': {'enabled': False},
                               'actionCards': {'hideBuyTank': True, 'hideBuySlot': True,
                                               'hideRestoreTank': True}},
                    'RUNTIME_STATE': {'sortMode': 'random', 'sortDescending': False,
                                      'carouselRows': 3, 'carouselRowsMode': 'auto' if auto else 'manual'},
                    '_settings_labels': lambda: collections.defaultdict(lambda: 'label'),
                    '_settings_language': lambda: 'uk', '_on_settings_changed': lambda *args: None,
                    'LOGGER': type('Logger', (), {'info': lambda *args: None,
                                                 'exception': lambda *args: self.fail(str(args))})(),
                }
                exec(code, ns)
                ns['_register_settings']()
                linkage, template, callback = captured[-1]
                self.assertEqual('com.rcooler.hangar_carousel_plus', linkage)
                self.assertGreater(template['settingsVersion'], 2)
                self.assertFalse(template['enabled'])
                controls = dict((x['varName'], x) for x in template['column1'] + template['column2']
                                if 'varName' in x)
                expected = {'minimumBattles': 37, 'cardStatsEnabled': False,
                            'carouselRows': 0 if auto else 3, 'sortingEnabled': False,
                            'sortMode': ns['SORT_ORDER'].index('random'), 'sortDescending': False,
                            'hideBuyTank': True, 'hideBuySlot': True, 'hideRestoreTank': True}
                for key, value in expected.items():
                    self.assertEqual(value, controls[key]['value'], key)
                for key in ns['FILTER_ORDER']:
                    if key != 'all':
                        self.assertEqual(key == 'non_elite', controls['filter_' + key]['value'])
                self.assertEqual(len(ns['SORT_ORDER']), len(controls['sortMode']['options']))
                self.assertTrue(ns['SETTINGS_REGISTERED'])
                count = len(captured)
                ns['_register_settings']()
                self.assertEqual(count, len(captured))
        finally:
            for name, value in saved_modules.items():
                if value is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = value


if __name__ == '__main__':
    SOURCE_PATH = sys.argv.pop(1)
    unittest.main()
