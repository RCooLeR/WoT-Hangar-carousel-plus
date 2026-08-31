# -*- coding: utf-8 -*-
"""Behavioral tests for HCP's Python 2.7 automatic-row coordinator."""
from __future__ import print_function

import ast
import sys
import unittest


FUNCTIONS = set((
    '_carousel_rows',
    '_carousel_auto',
    '_set_filter_provider_auto_property',
    '_cancel_pending_automatic_rows',
    '_cancel_filter_provider_rearm',
    '_complete_filter_provider_rearm',
    '_rearm_filter_provider',
    '_register_filter_provider',
    '_unregister_filter_provider',
    '_apply_rows_to_providers',
    '_set_carousel_rows',
    '_apply_pending_automatic_rows',
    '_request_automatic_carousel_rows',
))
SOURCE_PATH = None


class _Logger(object):
    def info(self, *_args):
        pass

    def exception(self, *args):
        raise AssertionError(args)


class _BigWorld(object):
    callbacks = []

    @classmethod
    def callback(cls, delay, function):
        if delay not in (0.0, 0.4):
            raise AssertionError('Unexpected debounce delay: %r' % delay)
        cls.callbacks.append((delay, function))


class _ViewModel(object):
    def __init__(self, rows):
        self.rows = rows
        self.carousel_auto = True
        self.auto_history = []

    def getCarouselRowCount(self):
        return self.rows

    def transaction(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        return False

    def setHcpCarouselAuto(self, enabled):
        self.carousel_auto = bool(enabled)
        self.auto_history.append(bool(enabled))


class _Provider(object):
    def __init__(self, name, rows=4):
        self.name = name
        self.viewModel = _ViewModel(rows)
        self._VehicleFiltersDataProvider__rowCount = rows
        self.updates = 0

    def _VehicleFiltersDataProvider__updateCarousel(self):
        self.updates += 1
        self.viewModel.rows = self._VehicleFiltersDataProvider__rowCount


class _Model(object):
    def __init__(self):
        self.refreshes = 0

    def refresh(self):
        self.refreshes += 1


def _load_functions(source_path):
    with open(source_path, 'rb') as source_file:
        source = source_file.read()
    tree = ast.parse(source, source_path)
    body = [node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS]
    found = set(node.name for node in body)
    if found != FUNCTIONS:
        raise AssertionError('Missing functions: %s' % sorted(FUNCTIONS - found))
    module = ast.Module(body=body)
    ast.fix_missing_locations(module)
    return compile(module, source_path, 'exec')


class AutomaticRowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if SOURCE_PATH is None:
            raise RuntimeError('Expected mod_hangar_carousel_plus.py path')
        cls.compiled_functions = _load_functions(SOURCE_PATH)

    def setUp(self):
        _BigWorld.callbacks = []
        self.calls = {'save': 0, 'invalidate': 0, 'sync': 0}
        self.model = _Model()

        def save_runtime():
            self.calls['save'] += 1

        def invalidate_render_cache(include_sort=True):
            self.calls['invalidate'] += 1

        def sync_auto(_enabled):
            self.calls['sync'] += 1

        self.namespace = {
            'RUNTIME_STATE': {'carouselRows': 4, 'carouselRowsMode': 'auto'},
            'FILTER_PROVIDERS': [],
            'ACTIVE_FILTER_PROVIDER': None,
            'MODELS': [self.model],
            'LOGGER': _Logger(),
            'BigWorld': _BigWorld,
            'AUTO_ROWS_REQUEST_SERIAL': 0,
            'AUTO_ROWS_PENDING': None,
            'AUTO_ROWS_PENDING_PROVIDER': None,
            'AUTO_ROWS_DEBOUNCE_SECONDS': 0.4,
            'AUTO_ROWS_REARM_SERIAL': 0,
            '_save_runtime': save_runtime,
            '_invalidate_render_cache': invalidate_render_cache,
            '_sync_carousel_auto_property': sync_auto,
        }
        eval(self.compiled_functions, self.namespace)

    def register(self, provider):
        self.namespace['_register_filter_provider'](provider)

    def run_next(self, expected_delay=None):
        delay, callback = _BigWorld.callbacks.pop(0)
        if expected_delay is not None:
            self.assertEqual(expected_delay, delay)
        callback()

    def test_zero_amount_is_ignored(self):
        provider = _Provider('active')
        self.register(provider)
        serial = self.namespace['AUTO_ROWS_REQUEST_SERIAL']

        self.assertFalse(
            self.namespace['_request_automatic_carousel_rows'](0, provider))

        self.assertEqual(serial, self.namespace['AUTO_ROWS_REQUEST_SERIAL'])
        self.assertEqual([], _BigWorld.callbacks)
        self.assertIsNone(self.namespace['AUTO_ROWS_PENDING'])

    def test_latest_active_candidate_wins(self):
        provider = _Provider('active')
        self.register(provider)

        self.assertTrue(
            self.namespace['_request_automatic_carousel_rows'](1, provider))
        self.assertTrue(
            self.namespace['_request_automatic_carousel_rows'](3, provider))
        self.run_next()
        self.assertEqual(4, self.namespace['RUNTIME_STATE']['carouselRows'])
        self.run_next()

        self.assertEqual(3, self.namespace['RUNTIME_STATE']['carouselRows'])
        self.assertEqual(1, self.calls['save'])
        self.assertEqual(1, provider.updates)
        self.assertEqual(1, self.model.refreshes)

    def test_stale_provider_cannot_cancel_active_pending_request(self):
        stale = _Provider('stale')
        active = _Provider('active')
        self.register(stale)
        self.register(active)
        self.assertTrue(
            self.namespace['_request_automatic_carousel_rows'](2, active))
        serial = self.namespace['AUTO_ROWS_REQUEST_SERIAL']

        self.assertFalse(
            self.namespace['_request_automatic_carousel_rows'](4, stale))
        self.assertFalse(
            self.namespace['_set_carousel_rows'](3, provider=stale))

        self.assertEqual(serial, self.namespace['AUTO_ROWS_REQUEST_SERIAL'])
        self.assertEqual(2, self.namespace['AUTO_ROWS_PENDING'])
        self.assertIs(active, self.namespace['AUTO_ROWS_PENDING_PROVIDER'])
        self.run_next()
        self.assertEqual(2, self.namespace['RUNTIME_STATE']['carouselRows'])
        self.assertEqual(0, stale.updates)
        self.assertEqual(1, active.updates)

    def test_newest_provider_takes_ownership_from_previous_provider(self):
        previous = _Provider('previous')
        newest = _Provider('newest')
        self.register(previous)
        self.assertTrue(
            self.namespace['_request_automatic_carousel_rows'](1, previous))
        previous_callback = _BigWorld.callbacks.pop(0)[1]

        self.register(newest)
        previous_callback()
        self.assertEqual(4, self.namespace['RUNTIME_STATE']['carouselRows'])
        self.assertEqual(0, self.calls['save'])
        self.assertFalse(
            self.namespace['_request_automatic_carousel_rows'](3, previous))
        self.assertTrue(
            self.namespace['_request_automatic_carousel_rows'](2, newest))
        self.run_next()

        self.assertEqual(2, self.namespace['RUNTIME_STATE']['carouselRows'])
        self.assertEqual(0, previous.updates)
        self.assertEqual(1, newest.updates)

    def test_active_finalize_cancels_and_promotes_latest_fallback(self):
        oldest = _Provider('oldest')
        fallback = _Provider('fallback')
        active = _Provider('active')
        self.register(oldest)
        self.register(fallback)
        self.register(active)
        self.assertTrue(
            self.namespace['_request_automatic_carousel_rows'](2, active))
        callback = _BigWorld.callbacks.pop(0)[1]

        promoted = self.namespace['_unregister_filter_provider'](active)

        self.assertIs(fallback, promoted)
        self.assertIs(fallback, self.namespace['ACTIVE_FILTER_PROVIDER'])
        self.assertIsNone(self.namespace['AUTO_ROWS_PENDING'])
        self.assertEqual([False], fallback.viewModel.auto_history)
        self.assertEqual(1, len(_BigWorld.callbacks))
        self.assertEqual(0.0, _BigWorld.callbacks[0][0])
        callback()
        self.assertEqual(4, self.namespace['RUNTIME_STATE']['carouselRows'])
        self.assertEqual(0, self.calls['save'])
        self.run_next(expected_delay=0.0)
        self.assertEqual([False, True], fallback.viewModel.auto_history)
        self.assertTrue(
            self.namespace['_request_automatic_carousel_rows'](1, fallback))

    def test_finalized_promoted_provider_cannot_rearm(self):
        oldest = _Provider('oldest')
        promoted = _Provider('promoted')
        active = _Provider('active')
        self.register(oldest)
        self.register(promoted)
        self.register(active)

        self.namespace['_unregister_filter_provider'](active)
        stale_rearm = _BigWorld.callbacks.pop(0)[1]
        self.assertEqual([False], promoted.viewModel.auto_history)
        self.namespace['_unregister_filter_provider'](promoted)

        self.assertIs(oldest, self.namespace['ACTIVE_FILTER_PROVIDER'])
        self.assertFalse(self.namespace['_rearm_filter_provider'](promoted))
        stale_rearm()
        self.assertEqual([False], promoted.viewModel.auto_history)
        self.run_next(expected_delay=0.0)
        self.assertEqual([False, True], oldest.viewModel.auto_history)

    def test_same_row_active_request_cancels_older_candidate(self):
        provider = _Provider('active')
        self.register(provider)
        self.assertTrue(
            self.namespace['_request_automatic_carousel_rows'](1, provider))
        callback = _BigWorld.callbacks.pop(0)[1]

        self.assertFalse(
            self.namespace['_request_automatic_carousel_rows'](4, provider))

        self.assertIsNone(self.namespace['AUTO_ROWS_PENDING'])
        callback()
        self.assertEqual(4, self.namespace['RUNTIME_STATE']['carouselRows'])
        self.assertEqual(0, self.calls['save'])
        self.assertEqual(0, provider.updates)

    def test_unchanged_rows_skip_writes_refreshes_and_rebuilds(self):
        active = _Provider('active')
        stale = _Provider('stale')
        self.register(stale)
        self.register(active)

        self.assertFalse(self.namespace['_set_carousel_rows'](
            4, automatic=True, provider=active))

        self.assertEqual({'save': 0, 'invalidate': 0, 'sync': 0}, self.calls)
        self.assertEqual(0, active.updates)
        self.assertEqual(0, stale.updates)
        self.assertEqual(0, self.model.refreshes)


if __name__ == '__main__':
    SOURCE_PATH = sys.argv[1]
    del sys.argv[1]
    unittest.main()
