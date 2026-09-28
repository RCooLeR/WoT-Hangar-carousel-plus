# -*- coding: utf-8 -*-
"""Exercise actual sorting functions without importing the game client."""
from __future__ import print_function

import ast
import copy
import json
import random
import sys
import textwrap
import unittest


class SortingTest(unittest.TestCase):
    def setUp(self):
        with open(SOURCE_PATH, 'rb') as source:
            tree = ast.parse(source.read(), SOURCE_PATH)
        functions = set(('_random_sort_values', '_build_sort_json', '_sort_mode',
                         '_sort_descending', '_set_sorting', '_migrate_config',
                         '_invalidate_render_cache', '_reshuffle_random_order',
                         '_on_battle_ready', '_on_account_become_player'))
        constants = set(('DEFAULT_CONFIG', 'SORT_ORDER', 'FILTER_ORDER',
                         'SETTINGS_SORT_OPTIONS', 'SETTINGS_BATTLE_PASS_SORT_OPTIONS',
                         'SETTINGS_PRIORITY_SORT_OPTIONS', 'SETTINGS_RANDOM_SORT_OPTIONS'))
        body = [node for node in tree.body if
                (isinstance(node, ast.FunctionDef) and node.name in functions) or
                (isinstance(node, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id in constants
                    for target in node.targets))]
        self.vehicles = dict((i, None) for i in range(20))
        self.refreshes = []
        replay = type('Replay', (), {'isPlaying': False})()
        self.ns = {
            'json': json, 'random': random.Random(42),
            'RANDOM_SORT_ORDER': [], 'SORT_JSON_CACHE': None,
            'STATE_JSON_CACHE': None, 'MODELS': [],
            'BATTLE_RETURN_PENDING': False,
            'BattleReplay': type('BattleReplay', (), {'g_replayCtrl': replay})(),
            '_track_last_played': lambda: None,
            '_schedule_models_refresh': lambda: self.refreshes.append(True),
            'RUNTIME_STATE': {'sortMode': 'random', 'sortDescending': True},
            '_inventory_vehicles': lambda: self.vehicles,
            '_save_runtime': lambda: None, '_sync_sort_property': lambda: None,
            'LOGGER': type('Logger', (), {'info': lambda *args: None})(),
        }
        exec(compile(ast.Module(body=body), SOURCE_PATH, 'exec'), self.ns)
        self.ns['CONFIG'] = copy.deepcopy(self.ns['DEFAULT_CONFIG'])

    def payload(self):
        return json.loads(self.ns['_build_sort_json']())

    def test_permutation_and_refresh_stability(self):
        first = self.payload()
        self.assertEqual('random', first['mode'])
        self.assertFalse(first['descending'])
        self.assertEqual(list(range(20)), sorted(first['values'].values()))
        self.assertEqual(set(map(str, self.vehicles)), set(first['values']))
        self.assertNotEqual(list(range(20)), self.ns['RANDOM_SORT_ORDER'])
        self.ns['_invalidate_render_cache']()
        self.assertEqual(first, self.payload())

    def test_reselect_random_reshuffles(self):
        first = self.payload()
        self.ns['_set_sorting']('random', True)
        second = self.payload()
        self.assertNotEqual(first['values'], second['values'])
        self.assertEqual(sorted(first['values'].values()), sorted(second['values'].values()))
        self.assertFalse(second['descending'])
        self.assertTrue(self.ns['RUNTIME_STATE']['sortDescending'])

    def test_each_battle_return_reshuffles_once(self):
        previous = self.payload()
        for _ in range(3):
            self.ns['_on_battle_ready']()
            self.assertEqual(previous, self.payload())
            self.ns['_on_account_become_player']()
            current = self.payload()
            self.assertNotEqual(previous['values'], current['values'])
            self.ns['_on_account_become_player']()
            self.assertEqual(current, self.payload())
            previous = current
        self.assertEqual(3, len(self.refreshes))

    def test_login_and_replay_do_not_reshuffle(self):
        previous = self.payload()
        self.ns['_on_account_become_player']()
        self.assertEqual(previous, self.payload())
        self.ns['BattleReplay'].g_replayCtrl.isPlaying = True
        self.ns['_on_battle_ready']()
        self.ns['_on_account_become_player']()
        self.assertEqual(previous, self.payload())
        self.assertEqual([], self.refreshes)

    def test_other_sort_modes_and_disabled_sorting_are_unchanged(self):
        self.payload()
        previous = list(self.ns['RANDOM_SORT_ORDER'])
        for mode, enabled in [('default', True), ('random', False)]:
            self.ns['RUNTIME_STATE']['sortMode'] = mode
            self.ns['CONFIG']['sorting']['enabled'] = enabled
            self.ns['_on_battle_ready']()
            self.ns['_on_account_become_player']()
            self.assertFalse(self.ns['BATTLE_RETURN_PENDING'])
            self.assertEqual(previous, self.ns['RANDOM_SORT_ORDER'])
        self.assertEqual([], self.refreshes)

    def test_reshuffle_cannot_repeat_identical_order(self):
        self.payload()
        previous = list(self.ns['RANDOM_SORT_ORDER'])
        self.ns['random'] = type('Random', (), {'shuffle': lambda *args: None})()
        self.ns['_reshuffle_random_order']()
        self.assertNotEqual(previous, self.ns['RANDOM_SORT_ORDER'])
        self.assertEqual(sorted(previous), sorted(self.ns['RANDOM_SORT_ORDER']))

    def test_inventory_changes_keep_survivors_in_order(self):
        self.payload()
        old = list(self.ns['RANDOM_SORT_ORDER'])
        del self.vehicles[3]
        self.vehicles[100] = None
        self.ns['_invalidate_render_cache']()
        values = self.payload()['values']
        self.assertNotIn('3', values)
        self.assertIn('100', values)
        self.assertEqual([i for i in old if i != 3],
                         [i for i in self.ns['RANDOM_SORT_ORDER'] if i != 100])

    def test_empty_and_single_vehicle(self):
        self.vehicles.clear()
        self.assertEqual({}, self.payload()['values'])
        self.vehicles[5] = None
        self.ns['_invalidate_render_cache']()
        self.assertEqual({'5': 0}, self.payload()['values'])

    def test_all_three_tank_permutations_are_possible(self):
        orders = set()
        for second in range(2):
            for third in range(3):
                choices = iter((0, second, third))
                self.ns['random'] = type('Random', (), {
                    'randrange': lambda _self, _stop: next(choices)})()
                del self.ns['RANDOM_SORT_ORDER'][:]
                self.ns['_random_sort_values']({1: None, 2: None, 3: None})
                orders.add(tuple(self.ns['RANDOM_SORT_ORDER']))
        self.assertEqual(6, len(orders))

    def test_settings_dropdown_matches_modes_in_every_language(self):
        with open(SOURCE_PATH, 'rb') as source:
            text = source.read().decode('utf-8')
        start = text.index('        sort_options = ')
        end = text.index('        rows_value = ', start)
        code = compile(textwrap.dedent(text[start:end]), SOURCE_PATH, 'exec')
        for language, label in self.ns['SETTINGS_RANDOM_SORT_OPTIONS'].items():
            self.ns['language'] = language
            exec(code, self.ns)
            self.assertEqual(len(self.ns['SORT_ORDER']), len(self.ns['sort_options']))
            self.assertEqual(label, self.ns['sort_options'][-1])

    def test_disabled_sorting_does_not_shuffle(self):
        self.ns['CONFIG']['sorting']['enabled'] = False
        self.assertEqual({}, self.payload()['values'])
        self.assertEqual([], self.ns['RANDOM_SORT_ORDER'])

    def test_migration_preserves_custom_settings(self):
        config = {'schemaVersion': 6, 'sorting': {
            'enabled': False, 'options': ['lastPlayed'],
            'default': 'lastPlayed', 'descending': False},
            'cardStats': {'minimumBattles': 17}}
        result = self.ns['_migrate_config'](copy.deepcopy(config))
        expected = copy.deepcopy(config)
        expected['schemaVersion'] = 7
        expected['sorting']['options'].append('random')
        self.assertEqual(expected, result)
        self.assertEqual(expected, self.ns['_migrate_config'](result))
        result['sorting']['options'].remove('random')
        self.assertNotIn('random', self.ns['_migrate_config'](result)['sorting']['options'])


if __name__ == '__main__':
    SOURCE_PATH = sys.argv.pop(1)
    unittest.main()
