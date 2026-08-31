# -*- coding: utf-8 -*-
"""Hangar Carousel Plus bootstrap for the World of Tanks 2.x client.

The client embeds Python 2.7, so this module deliberately avoids Python 3-only
syntax. Custom filter predicates narrow the native vehicle-statistics model;
the Gameface layer supplies independent toggles and card overlays.
"""
from __future__ import absolute_import, division

import io
import json
import logging
import os
import time
import weakref

import BigWorld
import BattleReplay
from PlayerEvents import g_playerEvents
from dossiers2.ui.achievements import MARK_ON_GUN_RECORD
from frameworks.wulf import ViewModel
from gui.impl.gen.view_models.views.lobby.hangar.sub_views.vehicle_filter_model import VehicleFilterModel
from gui.impl.gen.view_models.views.lobby.tooltips.carousel_vehicle_tooltip_model import CarouselVehicleTooltipModel
from gui.impl.lobby.hangar.presenters.vehicle_filters_presenter import VehicleFiltersDataProvider
from gui.impl.lobby.hangar.presenters.vehicle_statistics_presenter import VehiclesStatisticsPresenter
from gui.impl.lobby.hangar.presenters.vehicle_playlists_presenter import VehiclePlaylistsPresenter
from gui.impl.lobby.tooltips.carousel_vehicle_tooltip import CarouselVehicleTooltipView
from gui.shared.utils.requesters import REQ_CRITERIA
from gui.veh_post_progression.models.progression import PostProgressionCompletion
from helpers import dependency, getClientLanguage
from openwg_gameface import gf_mod_inject
from skeletons.gui.game_control import IBattlePassController, IVehiclePlaylistsController
from skeletons.gui.shared import IItemsCache


MOD_ID = 'hangar_carousel_plus'
MOD_VERSION = '0.8.13'
PLAYLIST_ID_PREFIX = 'rcooler_hcp_'
CONFIG_PATH = os.path.join('mods', 'configs', 'RCooLeR', 'hangar_carousel_plus.json')
RUNTIME_PATH = os.path.join('mods', 'configs', 'RCooLeR', 'hangar_carousel_plus.runtime.json')
LEGACY_CONFIG_PATH = os.path.join('res_mods', 'configs', MOD_ID, 'config.json')
LEGACY_RUNTIME_PATH = os.path.join('res_mods', 'configs', MOD_ID, 'runtime.json')
JS_URL = 'coui://gui/gameface/mods/rcooler/hangar_carousel_plus/hangar_carousel_plus.js'
I18N_URL = 'coui://gui/gameface/mods/rcooler/hangar_carousel_plus/hangar_carousel_plus.i18n.js'
CSS_URL = 'coui://gui/gameface/mods/rcooler/hangar_carousel_plus/hangar_carousel_plus.css'
TOOLTIP_JS_URL = 'coui://gui/gameface/mods/rcooler/hangar_carousel_plus/hangar_carousel_plus.tooltip.js'
TOOLTIP_CSS_URL = 'coui://gui/gameface/mods/rcooler/hangar_carousel_plus/hangar_carousel_plus.tooltip.css'

LOGGER = logging.getLogger('HangarCarouselPlus')

DEFAULT_CONFIG = {
    'schemaVersion': 6,
    'enabled': True,
    'filters': {
        'enabled': [
            'all', 'field_mod_incomplete', 'crew_not_maxed', 'non_elite',
            'reward_special', 'not_ready', 'no_mastery',
            'marks_incomplete', 'research_ready'
        ],
        'playlistPrefix': u'HCP · '
    },
    'cardStats': {
        'enabled': True,
        'fields': ['battles', 'winRate', 'averageDamage', 'mastery', 'marksOnGun'],
        'minimumBattles': 1
    },
    'sorting': {
        'enabled': True,
        'options': [
            'default', 'battles', 'winRate', 'averageDamage', 'marksOnGun',
            'battlePassPoints', 'lastPlayed', 'priority'
        ],
        'default': 'default',
        'descending': True
    },
    'actionCards': {
        'hideBuyTank': False,
        'hideBuySlot': False,
        'hideRestoreTank': False
    },
    'debug': False
}

FILTER_ORDER = (
    'all', 'field_mod_incomplete', 'crew_not_maxed', 'non_elite',
    'reward_special', 'not_ready', 'no_mastery',
    'marks_incomplete', 'research_ready'
)
SORT_ORDER = (
    'default', 'battles', 'winRate', 'averageDamage', 'marksOnGun',
    'battlePassPoints', 'lastPlayed', 'priority'
)
RUNTIME_DEFAULT = {
    'lastPlayed': {},
    'activeFilters': [],
    'carouselRows': 0,
    'carouselRowsMode': 'manual',
    'sortMode': 'default',
    'sortDescending': True
}


class _Services(object):
    itemsCache = dependency.descriptor(IItemsCache)
    playlists = dependency.descriptor(IVehiclePlaylistsController)
    battlePass = dependency.descriptor(IBattlePassController)


SERVICES = _Services()
# ViewModel has no dispose/finalize hook in the supported WoT 2.3.1.x Wulf API, but it is
# explicitly weak-referenceable.  Keeping these child models in a normal list
# would therefore extend their lifetime every time the hangar view is rebuilt.
MODELS = weakref.WeakSet()
FILTER_PROVIDERS = []
ACTIVE_FILTER_PROVIDER = None
STATISTICS_PRESENTERS = []
LAST_DATA_SUMMARY = None
LEGACY_PLAYLISTS_REMOVED = False
TOOLTIP_PAYLOAD_LOGGED = False
SETTINGS_REGISTERED = False
VEHICLE_DATA_CACHE = {}
STATE_JSON_CACHE = None
SORT_JSON_CACHE = None
MODEL_REFRESH_PENDING = False
BATTLE_PASS_EVENTS_REGISTERED = False
AUTO_ROWS_REQUEST_SERIAL = 0
AUTO_ROWS_PENDING = None
AUTO_ROWS_PENDING_PROVIDER = None
AUTO_ROWS_DEBOUNCE_SECONDS = 0.4
AUTO_ROWS_REARM_SERIAL = 0


def _is_hcp_playlist_id(value):
    return isinstance(value, basestring) and value.startswith(PLAYLIST_ID_PREFIX)


def _deep_merge(base, override):
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _migrate_config(loaded):
    if int(loaded.get('schemaVersion', 1)) < 2:
        filters = loaded.setdefault('filters', {})
        enabled = list(filters.get('enabled', DEFAULT_CONFIG['filters']['enabled']))
        if 'non_elite' not in enabled:
            enabled.append('non_elite')
        filters['enabled'] = enabled
        loaded['schemaVersion'] = 2
    if int(loaded.get('schemaVersion', 2)) < 3:
        filters = loaded.setdefault('filters', {})
        enabled = list(filters.get('enabled', []))
        if 'premium' in enabled:
            enabled.remove('premium')
        for filter_id in FILTER_ORDER:
            if filter_id not in enabled:
                enabled.append(filter_id)
        filters['enabled'] = enabled
        loaded['schemaVersion'] = 3
    loaded.pop('currencyLocks', None)
    if int(loaded.get('schemaVersion', 3)) < 5:
        sorting = loaded.setdefault('sorting', {})
        options = list(sorting.get('options', DEFAULT_CONFIG['sorting']['options']))
        if 'priority' not in options:
            options.append('priority')
        sorting['options'] = options
    if int(loaded.get('schemaVersion', 5)) < 6:
        sorting = loaded.setdefault('sorting', {})
        options = list(sorting.get('options', DEFAULT_CONFIG['sorting']['options']))
        if 'battlePassPoints' not in options:
            insert_at = options.index('lastPlayed') if 'lastPlayed' in options else len(options)
            options.insert(insert_at, 'battlePassPoints')
        sorting['options'] = options
    loaded['schemaVersion'] = 6
    return loaded


def _load_config():
    for path in (CONFIG_PATH, LEGACY_CONFIG_PATH):
        try:
            with io.open(path, 'r', encoding='utf-8-sig') as config_file:
                loaded = json.load(config_file)
            if not isinstance(loaded, dict):
                raise ValueError('root value must be an object')
            original_schema = int(loaded.get('schemaVersion', 1))
            if path == LEGACY_CONFIG_PATH:
                LOGGER.info('Migrating user configuration from %s to %s', path, CONFIG_PATH)
            return (_deep_merge(DEFAULT_CONFIG, _migrate_config(loaded)), path,
                    path == LEGACY_CONFIG_PATH or original_schema < DEFAULT_CONFIG['schemaVersion'])
        except IOError:
            continue
        except Exception:
            LOGGER.exception('Invalid config at %s; trying fallback', path)
    LOGGER.info('No user config found; using defaults at %s', CONFIG_PATH)
    return _deep_merge(DEFAULT_CONFIG, {}), None, True


def _load_runtime():
    for path in (RUNTIME_PATH, LEGACY_RUNTIME_PATH):
        try:
            with io.open(path, 'r', encoding='utf-8-sig') as runtime_file:
                loaded = json.load(runtime_file)
            if isinstance(loaded, dict):
                if path == LEGACY_RUNTIME_PATH:
                    LOGGER.info('Migrating runtime state from %s to %s', path, RUNTIME_PATH)
                return _deep_merge(RUNTIME_DEFAULT, loaded), path
        except IOError:
            continue
        except Exception:
            LOGGER.exception('Invalid runtime state at %s; trying fallback', path)
    return _deep_merge(RUNTIME_DEFAULT, {}), None


def _save_config():
    try:
        directory = os.path.dirname(CONFIG_PATH)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        with io.open(CONFIG_PATH, 'w', encoding='utf-8') as config_file:
            payload = json.dumps(CONFIG, ensure_ascii=False, indent=2, sort_keys=True)
            if not isinstance(payload, unicode):
                payload = payload.decode('utf-8')
            config_file.write(payload)
            config_file.write(u'\n')
    except Exception:
        LOGGER.exception('Unable to save configuration at %s', CONFIG_PATH)


def _save_runtime():
    try:
        directory = os.path.dirname(RUNTIME_PATH)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        with io.open(RUNTIME_PATH, 'w', encoding='utf-8') as runtime_file:
            payload = json.dumps(RUNTIME_STATE, ensure_ascii=False, separators=(',', ':'))
            if not isinstance(payload, unicode):
                payload = payload.decode('utf-8')
            runtime_file.write(payload)
    except Exception:
        LOGGER.exception('Unable to save runtime state at %s', RUNTIME_PATH)


CONFIG, CONFIG_SOURCE_PATH, CONFIG_NEEDS_SAVE = _load_config()
RUNTIME_STATE, RUNTIME_SOURCE_PATH = _load_runtime()
if CONFIG_NEEDS_SAVE:
    _save_config()
if RUNTIME_SOURCE_PATH != RUNTIME_PATH:
    _save_runtime()
ACTIVE_FILTERS = set(filter_id for filter_id in RUNTIME_STATE.get('activeFilters', [])
                     if filter_id in FILTER_ORDER and filter_id != 'all')


def _carousel_rows():
    try:
        rows = int(RUNTIME_STATE.get('carouselRows', 0))
        return rows if 1 <= rows <= 4 else 0
    except (TypeError, ValueError):
        return 0


def _carousel_auto():
    return RUNTIME_STATE.get('carouselRowsMode', 'manual') == 'auto'


def _set_filter_provider_auto_property(provider, enabled):
    try:
        with provider.viewModel.transaction() as model:
            model.setHcpCarouselAuto(bool(enabled))
        return True
    except Exception:
        LOGGER.exception('Unable to update automatic carousel mode')
        return False


def _sync_carousel_auto_property(enabled):
    for provider in list(FILTER_PROVIDERS):
        _set_filter_provider_auto_property(provider, enabled)


def _cancel_pending_automatic_rows():
    global AUTO_ROWS_REQUEST_SERIAL, AUTO_ROWS_PENDING, AUTO_ROWS_PENDING_PROVIDER
    AUTO_ROWS_REQUEST_SERIAL += 1
    AUTO_ROWS_PENDING = None
    AUTO_ROWS_PENDING_PROVIDER = None


def _cancel_filter_provider_rearm():
    global AUTO_ROWS_REARM_SERIAL
    AUTO_ROWS_REARM_SERIAL += 1


def _complete_filter_provider_rearm(provider, serial):
    if serial != AUTO_ROWS_REARM_SERIAL:
        return False
    if (not _carousel_auto() or provider is not ACTIVE_FILTER_PROVIDER or
            provider not in FILTER_PROVIDERS):
        return False
    return _set_filter_provider_auto_property(provider, True)


def _rearm_filter_provider(provider):
    if (not _carousel_auto() or provider is not ACTIVE_FILTER_PROVIDER or
            provider not in FILTER_PROVIDERS):
        return False
    _cancel_filter_provider_rearm()
    serial = AUTO_ROWS_REARM_SERIAL
    if not _set_filter_provider_auto_property(provider, False):
        return False
    BigWorld.callback(
        0.0,
        lambda: _complete_filter_provider_rearm(provider, serial))
    return True


def _register_filter_provider(provider):
    global ACTIVE_FILTER_PROVIDER
    if provider in FILTER_PROVIDERS:
        FILTER_PROVIDERS.remove(provider)
    FILTER_PROVIDERS.append(provider)
    if ACTIVE_FILTER_PROVIDER is not provider:
        _cancel_pending_automatic_rows()
        _cancel_filter_provider_rearm()
    ACTIVE_FILTER_PROVIDER = provider


def _unregister_filter_provider(provider):
    global ACTIVE_FILTER_PROVIDER
    was_active = ACTIVE_FILTER_PROVIDER is provider
    if was_active:
        _cancel_pending_automatic_rows()
        _cancel_filter_provider_rearm()
    elif AUTO_ROWS_PENDING_PROVIDER is provider:
        _cancel_pending_automatic_rows()
    if provider in FILTER_PROVIDERS:
        FILTER_PROVIDERS.remove(provider)
    if was_active:
        ACTIVE_FILTER_PROVIDER = FILTER_PROVIDERS[-1] if FILTER_PROVIDERS else None
        rows = _carousel_rows()
        if ACTIVE_FILTER_PROVIDER is not None and rows:
            _apply_rows_to_providers(rows, (ACTIVE_FILTER_PROVIDER,))
        if ACTIVE_FILTER_PROVIDER is not None:
            _rearm_filter_provider(ACTIVE_FILTER_PROVIDER)
    return ACTIVE_FILTER_PROVIDER


def _apply_rows_to_providers(rows, providers=None):
    updated = 0
    candidates = list(FILTER_PROVIDERS) if providers is None else list(providers)
    for provider in candidates:
        if provider not in FILTER_PROVIDERS:
            continue
        try:
            model_rows = int(provider.viewModel.getCarouselRowCount())
            provider_rows = int(getattr(
                provider, '_VehicleFiltersDataProvider__rowCount', model_rows))
            if model_rows == rows and provider_rows == rows:
                continue
            provider._VehicleFiltersDataProvider__rowCount = rows
            provider._VehicleFiltersDataProvider__updateCarousel()
            updated += 1
        except Exception:
            LOGGER.exception('Unable to apply %d carousel rows', rows)
    return updated


def _set_carousel_rows(rows, automatic=False, provider=None):
    rows = int(rows)
    if rows == 0:
        if _carousel_auto():
            return False
        _cancel_pending_automatic_rows()
        RUNTIME_STATE['carouselRowsMode'] = 'auto'
        _invalidate_render_cache(include_sort=False)
        _save_runtime()
        _sync_carousel_auto_property(True)
        for model in list(MODELS):
            model.refresh()
        LOGGER.info('Automatic carousel row mode enabled')
        return True

    rows = max(1, min(4, int(rows)))
    if automatic:
        if (not _carousel_auto() or provider is None or
                provider is not ACTIVE_FILTER_PROVIDER or
                provider not in FILTER_PROVIDERS):
            return False
        next_mode = 'auto'
    else:
        if (provider is not None and
                (provider is not ACTIVE_FILTER_PROVIDER or
                 provider not in FILTER_PROVIDERS)):
            return False
        _cancel_pending_automatic_rows()
        next_mode = 'manual'

    previous_rows = _carousel_rows()
    previous_mode = 'auto' if _carousel_auto() else 'manual'
    state_changed = previous_rows != rows or previous_mode != next_mode
    if state_changed:
        RUNTIME_STATE['carouselRowsMode'] = next_mode
        RUNTIME_STATE['carouselRows'] = rows
        _invalidate_render_cache(include_sort=False)
        _save_runtime()
        if previous_mode != next_mode:
            _sync_carousel_auto_property(next_mode == 'auto')

    target_providers = (provider,) if automatic else None
    updated_providers = _apply_rows_to_providers(rows, target_providers)
    if not state_changed and not updated_providers:
        return False

    if state_changed:
        for model in list(MODELS):
            model.refresh()
        LOGGER.info('Carousel row count changed to %d%s',
                    rows, ' automatically' if automatic else '')
    return True


def _apply_pending_automatic_rows(serial):
    global AUTO_ROWS_PENDING, AUTO_ROWS_PENDING_PROVIDER
    if serial != AUTO_ROWS_REQUEST_SERIAL:
        return
    rows = AUTO_ROWS_PENDING
    provider = AUTO_ROWS_PENDING_PROVIDER
    AUTO_ROWS_PENDING = None
    AUTO_ROWS_PENDING_PROVIDER = None
    if (provider is None or provider is not ACTIVE_FILTER_PROVIDER or
            provider not in FILTER_PROVIDERS):
        return
    if rows is None or not _carousel_auto() or rows == _carousel_rows():
        return
    _set_carousel_rows(rows, automatic=True, provider=provider)


def _request_automatic_carousel_rows(rows, provider=None):
    global AUTO_ROWS_REQUEST_SERIAL, AUTO_ROWS_PENDING, AUTO_ROWS_PENDING_PROVIDER
    try:
        rows = int(rows)
    except (TypeError, ValueError):
        return False
    if rows <= 0 or not _carousel_auto():
        return False
    if (provider is None or provider is not ACTIVE_FILTER_PROVIDER or
            provider not in FILTER_PROVIDERS):
        return False
    rows = max(1, min(4, rows))
    AUTO_ROWS_REQUEST_SERIAL += 1
    serial = AUTO_ROWS_REQUEST_SERIAL
    AUTO_ROWS_PENDING = None
    AUTO_ROWS_PENDING_PROVIDER = None

    if rows == _carousel_rows():
        if provider is not None:
            _apply_rows_to_providers(rows, (provider,))
        return False

    AUTO_ROWS_PENDING = rows
    AUTO_ROWS_PENDING_PROVIDER = provider
    BigWorld.callback(
        AUTO_ROWS_DEBOUNCE_SECONDS,
        lambda: _apply_pending_automatic_rows(serial))
    return True


def _inventory_vehicles():
    criteria = REQ_CRITERIA.INVENTORY | REQ_CRITERIA.VEHICLE.ACTIVE_IN_NATION_GROUP
    return SERVICES.itemsCache.items.getVehicles(criteria)


def _invalidate_render_cache(include_sort=True):
    global STATE_JSON_CACHE, SORT_JSON_CACHE
    STATE_JSON_CACHE = None
    if include_sort:
        SORT_JSON_CACHE = None


def _invalidate_vehicle_data(int_cds=None):
    if int_cds is None:
        VEHICLE_DATA_CACHE.clear()
    else:
        for int_cd in int_cds:
            try:
                VEHICLE_DATA_CACHE.pop(int(int_cd), None)
            except (TypeError, ValueError):
                continue
    _invalidate_render_cache()


def _schedule_models_refresh():
    global MODEL_REFRESH_PENDING
    if MODEL_REFRESH_PENDING:
        return
    MODEL_REFRESH_PENDING = True

    def refresh_models():
        global MODEL_REFRESH_PENDING
        MODEL_REFRESH_PENDING = False
        if (_sort_mode() != 'default' and
                CONFIG.get('sorting', {}).get('enabled', True)):
            _sync_sort_property()
        for model in list(MODELS):
            model.refresh()

    BigWorld.callback(0.05, refresh_models)


def _vehicle_data_context():
    account_random_stats = SERVICES.itemsCache.items.getAccountDossier().getRandomStats()
    vehicle_cuts = account_random_stats.getVehicles() if account_random_stats is not None else {}
    return account_random_stats, vehicle_cuts, set(SERVICES.itemsCache.items.stats.unlocks)


def _field_mod_incomplete(vehicle):
    try:
        progression = vehicle.postProgression
        is_eligible = vehicle.isElite or vehicle.typeDescr.eliteByProgression
        return bool(is_eligible and progression.isExists() and
                    progression.getCompletion() is not PostProgressionCompletion.FULL)
    except Exception:
        if CONFIG.get('debug'):
            LOGGER.exception('Field Modification check failed for %s', vehicle.intCD)
        return False


def _crew_not_maxed(vehicle):
    try:
        if not bool(vehicle.isCrewFull):
            return True
        for _, tankman in vehicle.crew:
            if tankman is None:
                return True
            if not tankman.isMaxRoleLevel:
                return True
            if not tankman.isMaxCurrentVehicleSkillsEfficiency:
                return True
            if tankman.hasSkillToLearn():
                return True
            for skill in tankman.skills:
                if skill.level < 100:
                    return True
        return False
    except Exception:
        if CONFIG.get('debug'):
            LOGGER.exception('Crew check failed for %s', vehicle.intCD)
        return False


def _reward_special(vehicle):
    try:
        return bool(vehicle.isSpecial)
    except Exception:
        return False


def _not_ready(vehicle):
    try:
        return bool(vehicle.isBroken or not vehicle.isCrewFull or not vehicle.isAmmoFull)
    except Exception:
        if CONFIG.get('debug'):
            LOGGER.exception('Vehicle readiness check failed for %s', vehicle.intCD)
        return False


def _research_ready(vehicle, unlocked=None):
    """Return True when vehicle XP can unlock an immediately available item."""
    try:
        if vehicle.isElite:
            return False
        if unlocked is None:
            unlocked = set(SERVICES.itemsCache.items.stats.unlocks)
        vehicle_xp = int(vehicle.xp)
        for _, xp_cost, int_cd, prerequisites in vehicle.getUnlocksDescrs():
            if int_cd in unlocked:
                continue
            if not prerequisites.issubset(unlocked):
                continue
            if vehicle_xp >= int(xp_cost):
                return True
        return False
    except Exception:
        if CONFIG.get('debug'):
            LOGGER.exception('Research-ready check failed for %s', vehicle.intCD)
        return False


def _battle_pass_progress(vehicle):
    """Return the current seasonal Battle Pass points and vehicle cap."""
    try:
        points, limit = SERVICES.battlePass.getVehicleProgression(vehicle.intCD)
        return int(points), int(limit)
    except Exception:
        if CONFIG.get('debug'):
            LOGGER.exception('Battle Pass progression check failed for %s', vehicle.intCD)
        return 0, 0


def _matches(filter_id, vehicle):
    return bool(_vehicle_data(vehicle)['matches'].get(filter_id, False))


def _marks_on_gun(vehicle_dossier):
    try:
        achievement = vehicle_dossier.getTotalStats().getAchievement(MARK_ON_GUN_RECORD)
        return int(achievement.getValue())
    except Exception:
        return 0


def _build_stats(vehicle, account_random_stats, vehicle_cuts):
    battles = 0
    wins = 0
    mastery = 0
    if vehicle.intCD in vehicle_cuts:
        battles, wins, _ = vehicle_cuts[vehicle.intCD]
        mastery = account_random_stats.getMarkOfMasteryForVehicle(vehicle.intCD)

    average_damage = 0
    marks_on_gun = 0
    try:
        vehicle_dossier = SERVICES.itemsCache.items.getVehicleDossier(vehicle.intCD)
        random_stats = vehicle_dossier.getRandomStats()
        random_battles = random_stats.getBattlesCount()
        if random_battles:
            average_damage = int(round(random_stats.getDamageDealt() / float(random_battles)))
        marks_on_gun = _marks_on_gun(vehicle_dossier)
    except Exception:
        if CONFIG.get('debug'):
            LOGGER.exception('Dossier stats failed for %s', vehicle.intCD)

    return {
        'battles': int(battles),
        'winRate': round(100.0 * wins / battles, 1) if battles else 0.0,
        'averageDamage': average_damage,
        'mastery': int(mastery),
        'marksOnGun': marks_on_gun
    }


def _build_vehicle_data(vehicle, context):
    account_random_stats, vehicle_cuts, unlocked = context
    stats = _build_stats(vehicle, account_random_stats, vehicle_cuts)
    field_mod_incomplete = _field_mod_incomplete(vehicle)
    battle_pass_points, battle_pass_limit = _battle_pass_progress(vehicle)
    matches = {
        'all': True,
        'field_mod_incomplete': field_mod_incomplete,
        'crew_not_maxed': _crew_not_maxed(vehicle),
        'non_elite': not bool(vehicle.isElite),
        'reward_special': _reward_special(vehicle),
        'not_ready': _not_ready(vehicle),
        'no_mastery': stats['mastery'] <= 0,
        'marks_incomplete': int(vehicle.level) >= 5 and stats['marksOnGun'] < 3,
        'research_ready': _research_ready(vehicle, unlocked)
    }
    return {
        'matches': matches,
        'stats': stats,
        'battlePassPoints': battle_pass_points,
        'battlePassLimit': battle_pass_limit,
        'priority': 0 if bool(getattr(vehicle, 'isFavorite', False)) else (
            1 if field_mod_incomplete else 2)
    }


def _vehicle_data(vehicle, context=None):
    int_cd = int(vehicle.intCD)
    cached = VEHICLE_DATA_CACHE.get(int_cd)
    if cached is not None:
        return cached
    if context is None:
        context = _vehicle_data_context()
    cached = _build_vehicle_data(vehicle, context)
    VEHICLE_DATA_CACHE[int_cd] = cached
    return cached


def _vehicle_data_map(vehicles):
    current_ids = set(int(int_cd) for int_cd in vehicles)
    for stale_id in set(VEHICLE_DATA_CACHE).difference(current_ids):
        VEHICLE_DATA_CACHE.pop(stale_id, None)

    missing = [vehicle for vehicle in vehicles.values()
               if int(vehicle.intCD) not in VEHICLE_DATA_CACHE]
    context = _vehicle_data_context() if missing else None
    started = time.time()
    for vehicle in missing:
        _vehicle_data(vehicle, context)
    if missing and CONFIG.get('debug'):
        LOGGER.info('Vehicle cache: built %d records in %.1f ms; %d reused',
                    len(missing), 1000.0 * (time.time() - started),
                    len(vehicles) - len(missing))
    return dict((int(vehicle.intCD), VEHICLE_DATA_CACHE[int(vehicle.intCD)])
                for vehicle in vehicles.values())


def _sort_mode():
    mode = RUNTIME_STATE.get('sortMode', CONFIG.get('sorting', {}).get('default', 'default'))
    return mode if mode in SORT_ORDER else 'default'


def _sort_descending():
    return bool(RUNTIME_STATE.get(
        'sortDescending', CONFIG.get('sorting', {}).get('descending', True)))


def _build_sort_json():
    global SORT_JSON_CACHE
    if SORT_JSON_CACHE is not None:
        return SORT_JSON_CACHE

    mode = _sort_mode()
    payload = {
        'mode': mode,
        'descending': False if mode == 'priority' else _sort_descending(),
        'values': {}
    }
    if mode == 'default' or not CONFIG.get('sorting', {}).get('enabled', True):
        SORT_JSON_CACHE = json.dumps(payload, separators=(',', ':'))
        return SORT_JSON_CACHE

    vehicles = _inventory_vehicles()
    if mode == 'lastPlayed':
        last_played = RUNTIME_STATE.get('lastPlayed', {})
        payload['values'] = dict((str(int_cd), long(last_played.get(str(int_cd), 0)))
                                 for int_cd in vehicles)
    else:
        vehicle_data = _vehicle_data_map(vehicles)
        for vehicle in vehicles.values():
            data = vehicle_data[int(vehicle.intCD)]
            payload['values'][str(vehicle.intCD)] = (
                data['priority'] if mode == 'priority' else (
                    data['battlePassPoints'] if mode == 'battlePassPoints' else
                    data['stats'].get(mode, 0)))
    SORT_JSON_CACHE = json.dumps(payload, separators=(',', ':'))
    return SORT_JSON_CACHE


def _sync_sort_property():
    sort_json = _build_sort_json()
    for provider in list(FILTER_PROVIDERS):
        try:
            with provider.viewModel.transaction() as model:
                model.setHcpSortJson(sort_json)
        except Exception:
            LOGGER.exception('Unable to update native carousel sorting')


def _set_sorting(mode, descending=None):
    if mode not in SORT_ORDER:
        mode = 'default'
    RUNTIME_STATE['sortMode'] = mode
    if descending is not None:
        RUNTIME_STATE['sortDescending'] = bool(descending)
    _save_runtime()
    _invalidate_render_cache()
    _sync_sort_property()
    for model in list(MODELS):
        model.refresh()
    LOGGER.info('Carousel sorting changed to %s (%s)',
                mode, 'descending' if _sort_descending() else 'ascending')


def _matches_active_filters(vehicle):
    return all(_matches(filter_id, vehicle) for filter_id in ACTIVE_FILTERS)


def _filtered_vehicle_map(vehicles):
    return dict((int_cd, vehicle) for int_cd, vehicle in vehicles.items()
                if _matches_active_filters(vehicle))


def _refresh_native_vehicle_model():
    refreshed = 0
    for presenter in list(STATISTICS_PRESENTERS):
        try:
            vehicles = presenter._vehiclesComponent.vehicles
            presenter._VehiclesStatisticsPresenter__updateVehicles(vehicles)
            refreshed += 1
        except Exception:
            LOGGER.exception('Unable to refresh native vehicle filter model')
    matching = sum(1 for vehicle in _inventory_vehicles().values()
                   if _matches_active_filters(vehicle))
    LOGGER.info('Active filter toggles %s: %d vehicles (%d presenters)',
                sorted(ACTIVE_FILTERS), matching, refreshed)


def _set_filter_state(filter_id):
    if filter_id == 'all':
        ACTIVE_FILTERS.clear()
    elif filter_id in FILTER_ORDER:
        if filter_id in ACTIVE_FILTERS:
            ACTIVE_FILTERS.remove(filter_id)
        else:
            ACTIVE_FILTERS.add(filter_id)
    RUNTIME_STATE['activeFilters'] = sorted(ACTIVE_FILTERS)
    _save_runtime()
    _refresh_native_vehicle_model()


def _remove_legacy_playlists():
    global LEGACY_PLAYLISTS_REMOVED
    if LEGACY_PLAYLISTS_REMOVED or not SERVICES.playlists.isEnabled:
        return
    legacy_ids = [playlist_id for playlist_id, _ in SERVICES.playlists.iterPlaylists()
                  if _is_hcp_playlist_id(playlist_id)]
    selected_id = SERVICES.playlists.getSelectedID()
    for playlist_id in legacy_ids:
        SERVICES.playlists.deletePlaylist(playlist_id)
    if legacy_ids:
        SERVICES.playlists.setSelectedID('' if selected_id in legacy_ids else (selected_id or ''))
    LEGACY_PLAYLISTS_REMOVED = True
    if legacy_ids:
        LOGGER.info('Removed %d legacy HCP dynamic playlists', len(legacy_ids))


def _track_last_played():
    try:
        if getattr(BattleReplay.g_replayCtrl, 'isPlaying', False):
            return
        avatar = BigWorld.player()
        vehicle = BigWorld.entity(avatar.playerVehicleID)
        if vehicle is None:
            return
        int_cd = vehicle.typeDescriptor.type.compactDescr
        RUNTIME_STATE.setdefault('lastPlayed', {})[str(int_cd)] = long(time.time())
        _save_runtime()
        _invalidate_render_cache()
        if _sort_mode() == 'lastPlayed':
            _sync_sort_property()
    except Exception:
        LOGGER.exception('Unable to track the last-played vehicle')


def _on_battle_pass_vehicle_points_updated(vehicle_points=None, *_args, **_kwargs):
    try:
        int_cds = vehicle_points.keys() if isinstance(vehicle_points, dict) else None
        _invalidate_vehicle_data(int_cds)
        _schedule_models_refresh()
    except Exception:
        LOGGER.exception('Unable to refresh Battle Pass vehicle points')


def _on_battle_pass_state_updated(*_args, **_kwargs):
    _invalidate_vehicle_data()
    _schedule_models_refresh()


def _register_battle_pass_events():
    global BATTLE_PASS_EVENTS_REGISTERED
    if BATTLE_PASS_EVENTS_REGISTERED:
        return
    SERVICES.battlePass.onVehiclesPointsUpdated += _on_battle_pass_vehicle_points_updated
    SERVICES.battlePass.onSeasonStateChanged += _on_battle_pass_state_updated
    SERVICES.battlePass.onBattlePassSettingsChange += _on_battle_pass_state_updated
    BATTLE_PASS_EVENTS_REGISTERED = True
    LOGGER.info('Battle Pass vehicle-point updates registered')


def _build_payload():
    global LAST_DATA_SUMMARY
    vehicles = _inventory_vehicles()
    values = list(vehicles.values())
    vehicle_data = _vehicle_data_map(vehicles)
    enabled_filters = CONFIG.get('filters', {}).get('enabled', list(FILTER_ORDER))
    enabled_filters = [key for key in FILTER_ORDER if key in enabled_filters]

    stats_config = CONFIG.get('cardStats', {})
    stats_enabled = bool(stats_config.get('enabled', True))
    stats = {}
    if stats_enabled:
        for vehicle in values:
            stats[str(vehicle.intCD)] = vehicle_data[int(vehicle.intCD)]['stats']

    summary = (len(values), len(stats), sum(1 for value in stats.values() if value.get('battles', 0) > 0))
    if summary != LAST_DATA_SUMMARY:
        LAST_DATA_SUMMARY = summary
        LOGGER.info('Carousel data: %d vehicles, %d stat records, %d with battles', *summary)

    filters = []
    for filter_id in enabled_filters:
        count = sum(1 for vehicle in values
                    if vehicle_data[int(vehicle.intCD)]['matches'].get(filter_id, False))
        filters.append({'id': filter_id, 'count': count})

    return {
        'version': MOD_VERSION,
        'language': getClientLanguage(),
        'debug': bool(CONFIG.get('debug', False)),
        'enabled': bool(CONFIG.get('enabled', True)),
        'filterMode': 'native_toggles',
        'filters': filters,
        'stats': stats,
        'statsConfig': stats_config,
        'sorting': {
            'enabled': bool(CONFIG.get('sorting', {}).get('enabled', True)),
            'options': [key for key in SORT_ORDER
                        if key in CONFIG.get('sorting', {}).get('options', SORT_ORDER)],
            'mode': _sort_mode(),
            'descending': _sort_descending(),
            'directional': _sort_mode() != 'priority'
        },
        'actionCards': CONFIG.get('actionCards', {}),
        'nativeFeatures': ['premium', 'elite', 'rented', 'daily_bonus', 'battle_pass_available'],
        'carousel': {
            'rows': _carousel_rows() or 2,
            'mode': 'auto' if _carousel_auto() else 'manual',
            'supportedRows': [1, 2, 3, 4]
        },
        'trackedLastPlayed': len(RUNTIME_STATE.get('lastPlayed', {})),
        'totalVehicles': len(values)
    }


def _build_state_json():
    global STATE_JSON_CACHE
    if STATE_JSON_CACHE is None:
        STATE_JSON_CACHE = json.dumps(
            _build_payload(), ensure_ascii=False, separators=(',', ':'))
    return STATE_JSON_CACHE


class HangarCarouselPlusModel(ViewModel):
    __slots__ = ('onToggleFilter', 'onRefresh', 'onSetCarouselRows', 'onSetSorting')

    def __init__(self, properties=2, commands=4):
        super(HangarCarouselPlusModel, self).__init__(properties=properties, commands=commands)
        self.onToggleFilter += self.__on_toggle_filter
        self.onRefresh += self.__on_refresh
        self.onSetCarouselRows += self.__on_set_carousel_rows
        self.onSetSorting += self.__on_set_sorting
        MODELS.add(self)
        BigWorld.callback(0.1, self.refresh)

    def getStateJson(self):
        return self._getString(0)

    def setStateJson(self, value):
        self._setString(0, value)

    def getActiveFiltersJson(self):
        return self._getString(1)

    def setActiveFiltersJson(self, value):
        self._setString(1, value)

    def _initialize(self):
        super(HangarCarouselPlusModel, self)._initialize()
        self._addStringProperty('stateJson', '{}')
        self._addStringProperty('activeFiltersJson', '[]')
        self.onToggleFilter = self._addCommand('onToggleFilter')
        self.onRefresh = self._addCommand('onRefresh')
        self.onSetCarouselRows = self._addCommand('onSetCarouselRows')
        self.onSetSorting = self._addCommand('onSetSorting')

    def refresh(self):
        try:
            _remove_legacy_playlists()
            self.setStateJson(_build_state_json())
            self.setActiveFiltersJson(json.dumps(sorted(ACTIVE_FILTERS), separators=(',', ':')))
        except Exception:
            LOGGER.exception('Unable to refresh Hangar Carousel Plus data')

    def __on_refresh(self, *_args, **_kwargs):
        _invalidate_vehicle_data()
        _refresh_native_vehicle_model()
        self.refresh()

    def __on_toggle_filter(self, args):
        filter_id = args.get('id', '') if args else ''
        if filter_id not in FILTER_ORDER:
            return
        try:
            _set_filter_state(filter_id)
            for model in list(MODELS):
                model.refresh()
        except Exception:
            LOGGER.exception('Unable to toggle smart filter %s', filter_id)

    def __on_set_carousel_rows(self, args):
        try:
            _set_carousel_rows(args.get('rows', 2) if args else 2)
        except Exception:
            LOGGER.exception('Unable to change carousel row count')

    def __on_set_sorting(self, args):
        try:
            _set_sorting(
                args.get('mode', 'default') if args else 'default',
                args.get('descending') if args and 'descending' in args else None)
        except Exception:
            LOGGER.exception('Unable to change carousel sorting')

class HangarCarouselPlusTooltipModel(ViewModel):
    __slots__ = ()

    def __init__(self, properties=1, commands=0):
        super(HangarCarouselPlusTooltipModel, self).__init__(
            properties=properties, commands=commands)

    def getStateJson(self):
        return self._getString(0)

    def setStateJson(self, value):
        self._setString(0, value)

    def _initialize(self):
        super(HangarCarouselPlusTooltipModel, self)._initialize()
        self._addStringProperty('stateJson', '{}')


def _patch_vehicle_filter_model():
    if getattr(VehicleFilterModel, '_hcp_patched', False):
        return

    original_init = VehicleFilterModel.__init__
    original_initialize = VehicleFilterModel._initialize

    def patched_init(self, properties=4, commands=3):
        original_init(self, properties=properties + 4, commands=commands)

    def patched_initialize(self):
        original_initialize(self)
        gf_mod_inject(
            self,
            'HangarCarouselPlus',
            styles=[CSS_URL],
            modules=[I18N_URL, JS_URL]
        )
        self._addViewModelProperty('hangarCarouselPlus', HangarCarouselPlusModel())
        self._addBoolProperty('hcpCarouselAuto', _carousel_auto())
        self._addStringProperty('hcpSortJson', _build_sort_json())

    def get_hcp_carousel_auto(self):
        return self._getBool(6)

    def set_hcp_carousel_auto(self, value):
        self._setBool(6, value)

    def get_hcp_sort_json(self):
        return self._getString(7)

    def set_hcp_sort_json(self, value):
        self._setString(7, value)

    VehicleFilterModel.__init__ = patched_init
    VehicleFilterModel._initialize = patched_initialize
    VehicleFilterModel.getHcpCarouselAuto = get_hcp_carousel_auto
    VehicleFilterModel.setHcpCarouselAuto = set_hcp_carousel_auto
    VehicleFilterModel.getHcpSortJson = get_hcp_sort_json
    VehicleFilterModel.setHcpSortJson = set_hcp_sort_json
    VehicleFilterModel._hcp_patched = True


def _build_tooltip_payload(vehicle):
    return {
        'version': MOD_VERSION,
        'language': getClientLanguage(),
        'stats': _vehicle_data(vehicle)['stats'],
        'statsConfig': CONFIG.get('cardStats', {})
    }


def _patch_vehicle_tooltip():
    if getattr(CarouselVehicleTooltipModel, '_hcp_patched', False):
        return

    original_model_init = CarouselVehicleTooltipModel.__init__
    original_model_initialize = CarouselVehicleTooltipModel._initialize
    original_view_loading = CarouselVehicleTooltipView._onLoading

    def patched_model_init(self, properties=7, commands=0):
        original_model_init(self, properties=properties + 1, commands=commands)

    def patched_model_initialize(self):
        original_model_initialize(self)
        self._addViewModelProperty(
            'hangarCarouselPlusTooltip', HangarCarouselPlusTooltipModel())

    def get_hcp_tooltip_model(self):
        return self._getViewModel(7)

    def patched_view_loading(self, *args, **kwargs):
        global TOOLTIP_PAYLOAD_LOGGED
        result = original_view_loading(self, *args, **kwargs)
        try:
            vehicle = self._itemsCache.items.getVehicle(self._inventoryId)
            if vehicle is None:
                return result
            payload = _build_tooltip_payload(vehicle)
            with self.viewModel.transaction() as model:
                model.hangarCarouselPlusTooltip.setStateJson(
                    json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
            if not TOOLTIP_PAYLOAD_LOGGED:
                TOOLTIP_PAYLOAD_LOGGED = True
                LOGGER.info('Vehicle tooltip statistics model populated for %s', vehicle.intCD)
        except Exception:
            LOGGER.exception('Unable to populate HCP vehicle tooltip statistics')
        return result

    CarouselVehicleTooltipModel.__init__ = patched_model_init
    CarouselVehicleTooltipModel._initialize = patched_model_initialize
    CarouselVehicleTooltipModel.hangarCarouselPlusTooltip = property(get_hcp_tooltip_model)
    CarouselVehicleTooltipView._onLoading = patched_view_loading
    CarouselVehicleTooltipModel._hcp_patched = True


def _patch_vehicle_filters_provider():
    if getattr(VehicleFiltersDataProvider, '_hcp_rows_patched', False):
        return

    original_on_loading = VehicleFiltersDataProvider._onLoading
    original_finalize = VehicleFiltersDataProvider._finalize
    original_type_changed = VehicleFiltersDataProvider._VehicleFiltersDataProvider__onCarouselTypeChanged

    def patched_on_loading(self, *args, **kwargs):
        result = original_on_loading(self, *args, **kwargs)
        _register_filter_provider(self)
        with self.viewModel.transaction() as model:
            model.setHcpCarouselAuto(_carousel_auto())
            model.setHcpSortJson(_build_sort_json())
        rows = _carousel_rows()
        if not rows:
            rows = max(1, min(4, int(self.viewModel.getCarouselRowCount())))
            if _carousel_rows() != rows:
                RUNTIME_STATE['carouselRows'] = rows
                _save_runtime()
                _invalidate_render_cache(include_sort=False)
        _apply_rows_to_providers(rows, (self,))
        return result

    def patched_finalize(self):
        try:
            _unregister_filter_provider(self)
        finally:
            original_finalize(self)

    def patched_type_changed(self, args):
        rows = max(1, min(4, int(args.get('rowCount', 2))))
        if self is not ACTIVE_FILTER_PROVIDER or self not in FILTER_PROVIDERS:
            return None
        if bool(args.get('hcpAuto', False)):
            _request_automatic_carousel_rows(rows, self)
            return None
        if rows <= 2:
            _cancel_pending_automatic_rows()
            previous_rows = _carousel_rows()
            was_automatic = _carousel_auto()
            model_rows = int(self.viewModel.getCarouselRowCount())
            provider_rows = int(getattr(
                self, '_VehicleFiltersDataProvider__rowCount', model_rows))
            result = None
            if model_rows != rows or provider_rows != rows:
                result = original_type_changed(self, {'rowCount': rows})
            state_changed = previous_rows != rows or was_automatic
            if state_changed:
                RUNTIME_STATE['carouselRows'] = rows
                RUNTIME_STATE['carouselRowsMode'] = 'manual'
                _save_runtime()
                _invalidate_render_cache(include_sort=False)
                if was_automatic:
                    _sync_carousel_auto_property(False)
                for model in list(MODELS):
                    model.refresh()
            return result
        _set_carousel_rows(rows, provider=self)
        return None

    VehicleFiltersDataProvider._onLoading = patched_on_loading
    VehicleFiltersDataProvider._finalize = patched_finalize
    VehicleFiltersDataProvider._VehicleFiltersDataProvider__onCarouselTypeChanged = patched_type_changed
    VehicleFiltersDataProvider._hcp_rows_patched = True


def _patch_vehicle_statistics_presenter():
    if getattr(VehiclesStatisticsPresenter, '_hcp_patched', False):
        return

    original_init = VehiclesStatisticsPresenter.__init__
    original_finalize = VehiclesStatisticsPresenter._finalize
    original_update = VehiclesStatisticsPresenter._VehiclesStatisticsPresenter__updateVehicles
    original_on_update = VehiclesStatisticsPresenter._VehiclesStatisticsPresenter__onUpdateVehicles

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        STATISTICS_PRESENTERS.append(self)

    def patched_finalize(self):
        try:
            if self in STATISTICS_PRESENTERS:
                STATISTICS_PRESENTERS.remove(self)
        finally:
            original_finalize(self)

    def patched_update(self, vehicles):
        filtered = _filtered_vehicle_map(vehicles)
        with self.viewModel.transaction() as model:
            model.getStatistics().clear()
        return original_update(self, filtered)

    def patched_on_update(self, diff):
        diff = list(diff)
        _invalidate_vehicle_data(diff)
        if not ACTIVE_FILTERS:
            result = original_on_update(self, diff)
            _schedule_models_refresh()
            return result

        included = []
        excluded = []
        vehicles = self._vehiclesComponent.vehicles
        for int_cd in diff:
            vehicle = vehicles.get(int_cd)
            if vehicle is not None and _matches_active_filters(vehicle):
                included.append(int_cd)
            else:
                excluded.append(str(int_cd))

        if excluded:
            with self.viewModel.transaction() as model:
                statistics = model.getStatistics()
                for key in excluded:
                    if key in statistics:
                        statistics.remove(key)
        if included:
            result = original_on_update(self, included)
        else:
            result = None
        _schedule_models_refresh()
        return result

    VehiclesStatisticsPresenter.__init__ = patched_init
    VehiclesStatisticsPresenter._finalize = patched_finalize
    VehiclesStatisticsPresenter._VehiclesStatisticsPresenter__updateVehicles = patched_update
    VehiclesStatisticsPresenter._VehiclesStatisticsPresenter__onUpdateVehicles = patched_on_update
    VehiclesStatisticsPresenter._hcp_patched = True


def _patch_legacy_playlist_cleanup():
    if getattr(VehiclePlaylistsPresenter, '_hcp_cleanup_patched', False):
        return
    original_on_loading = VehiclePlaylistsPresenter._onLoading

    def patched_on_loading(self, *args, **kwargs):
        _remove_legacy_playlists()
        return original_on_loading(self, *args, **kwargs)

    VehiclePlaylistsPresenter._onLoading = patched_on_loading
    VehiclePlaylistsPresenter._hcp_cleanup_patched = True


SETTINGS_TEXT = {
    'en': {
        'filters': u'Smart filters', 'display': u'Carousel and cards',
        'sorting': u'Sorting', 'protection': u'Currency protection',
        'native': u'Already provided by the client: Premium, Elite, rented/temporary, daily bonus and Battle Pass points available.',
        'enabled': u'Enable Hangar Carousel Plus', 'cardStats': u'Show statistics on vehicle cards',
        'minBattles': u'Minimum battles for card statistics', 'rows': u'Carousel rows',
        'auto': u'Automatic', 'sortMode': u'Default sorting', 'descending': u'Descending order',
        'hideBuyTank': u'Hide "Buy vehicle" cell', 'hideBuySlot': u'Hide "Buy slot" cell',
        'hideRestoreTank': u'Hide "Restore vehicle" cell', 'lockGold': u'Lock gold',
        'lockFreeXP': u'Lock Free XP', 'lockBonds': u'Lock bonds',
        'filterHint': u'Show this toggle in the native vehicle filter popover.',
        'restart': u'Changes are applied immediately; restart the client after changing the master switch.',
        'filter_reward_special': u'Reward / special vehicles', 'filter_not_ready': u'Not ready for battle',
        'filter_no_mastery': u'Without Ace Tanker', 'filter_marks_incomplete': u'Fewer than three Marks of Excellence',
        'filter_research_ready': u'Enough XP for research', 'filter_field_mod_incomplete': u'Field Modification incomplete',
        'filter_crew_not_maxed': u'Crew training incomplete', 'filter_non_elite': u'Research incomplete'
    },
    'ru': {
        'filters': u'Умные фильтры', 'display': u'Карусель и карточки',
        'sorting': u'Сортировка', 'protection': u'Защита валют',
        'native': u'Уже есть в клиенте: премиум, элитная, арендная/временная техника, ежедневный бонус и доступные очки Боевого пропуска.',
        'enabled': u'Включить Hangar Carousel Plus', 'cardStats': u'Показывать статистику на карточках техники',
        'minBattles': u'Минимум боёв для статистики', 'rows': u'Ряды карусели',
        'auto': u'Автоматически', 'sortMode': u'Сортировка по умолчанию', 'descending': u'По убыванию',
        'hideBuyTank': u'Скрыть ячейку «Купить машину»', 'hideBuySlot': u'Скрыть ячейку «Купить слот»',
        'hideRestoreTank': u'Скрыть ячейку «Восстановить машину»', 'lockGold': u'Заблокировать золото',
        'lockFreeXP': u'Заблокировать свободный опыт', 'lockBonds': u'Заблокировать боны',
        'filterHint': u'Показывать этот переключатель в стандартном окне фильтров.',
        'restart': u'Изменения применяются сразу; после главного выключателя перезапустите клиент.',
        'filter_reward_special': u'Наградная / акционная техника', 'filter_not_ready': u'Не готова к бою',
        'filter_no_mastery': u'Без «Мастера»', 'filter_marks_incomplete': u'Меньше трёх отметок',
        'filter_research_ready': u'Хватает опыта для исследования', 'filter_field_mod_incomplete': u'Полевая модернизация не завершена',
        'filter_crew_not_maxed': u'Экипаж не прокачан', 'filter_non_elite': u'Исследование не завершено'
    },
    'uk': {
        'filters': u'Розумні фільтри', 'display': u'Карусель і картки',
        'sorting': u'Сортування', 'protection': u'Захист валют',
        'native': u'Уже є в клієнті: преміум, елітна, орендна/тимчасова техніка, щоденний бонус і доступні очки Бойової перепустки.',
        'enabled': u'Увімкнути Hangar Carousel Plus', 'cardStats': u'Показувати статистику на картках техніки',
        'minBattles': u'Мінімум боїв для статистики', 'rows': u'Ряди каруселі',
        'auto': u'Автоматично', 'sortMode': u'Типове сортування', 'descending': u'За спаданням',
        'hideBuyTank': u'Приховати клітинку «Купити машину»', 'hideBuySlot': u'Приховати клітинку «Купити слот»',
        'hideRestoreTank': u'Приховати клітинку «Відновити машину»', 'lockGold': u'Заблокувати золото',
        'lockFreeXP': u'Заблокувати вільний досвід', 'lockBonds': u'Заблокувати бони',
        'filterHint': u'Показувати цей перемикач у стандартному вікні фільтрів.',
        'restart': u'Зміни застосовуються одразу; після головного вимикача перезапустіть клієнт.',
        'filter_reward_special': u'Нагородна / акційна техніка', 'filter_not_ready': u'Не готова до бою',
        'filter_no_mastery': u'Без «Майстра»', 'filter_marks_incomplete': u'Менше трьох відміток',
        'filter_research_ready': u'Вистачає досвіду для дослідження', 'filter_field_mod_incomplete': u'Польову модернізацію не завершено',
        'filter_crew_not_maxed': u'Екіпаж не прокачаний', 'filter_non_elite': u'Дослідження не завершено'
    }
}

SETTINGS_VISIBLE_KEYS = (
    'filters', 'display', 'sorting', 'protection', 'cardStats', 'minBattles',
    'rows', 'auto', 'sortMode', 'descending', 'hideBuyTank', 'hideBuySlot',
    'hideRestoreTank', 'lockGold', 'lockFreeXP', 'lockBonds',
    'filter_reward_special', 'filter_not_ready', 'filter_no_mastery',
    'filter_marks_incomplete', 'filter_research_ready',
    'filter_field_mod_incomplete', 'filter_crew_not_maxed', 'filter_non_elite'
)

SETTINGS_VISIBLE_I18N = {
    'bg': (u'Интелигентни филтри', u'Карусел и карти', u'Сортиране', u'Защита на валути', u'Статистика върху картите', u'Минимум битки за статистика', u'Редове на карусела', u'Автоматично', u'Сортиране по подразбиране', u'Низходящо', u'Скрий „Купи машина“', u'Скрий „Купи слот“', u'Скрий „Възстанови машина“', u'Заключи златото', u'Заключи свободния опит', u'Заключи боновете', u'Наградни / специални машини', u'Неготови за бой', u'Без „Майстор“', u'Под три отличителни знака', u'Достъпно проучване', u'Незавършена полева модификация', u'Екипажът не е напълно обучен', u'Незавършено проучване'),
    'cs': (u'Chytré filtry', u'Karusel a karty', u'Řazení', u'Ochrana měn', u'Statistiky na kartách', u'Minimum bitev pro statistiky', u'Řádky karuselu', u'Automaticky', u'Výchozí řazení', u'Sestupně', u'Skrýt „Koupit vozidlo“', u'Skrýt „Koupit stání“', u'Skrýt „Obnovit vozidlo“', u'Uzamknout zlaťáky', u'Uzamknout volné zkušenosti', u'Uzamknout bony', u'Odměnová / speciální vozidla', u'Nepřipraveno k bitvě', u'Bez esa', u'Méně než tři znaky', u'Výzkum je dostupný', u'Nedokončené polní modifikace', u'Nedokončený výcvik posádky', u'Nedokončený výzkum'),
    'da': (u'Smarte filtre', u'Karrusel og kort', u'Sortering', u'Valutabesk yttelse', u'Statistik på kort', u'Minimum antal kampe', u'Karruselrækker', u'Automatisk', u'Standardsortering', u'Faldende', u'Skjul „Køb køretøj“', u'Skjul „Køb plads“', u'Skjul „Gendan køretøj“', u'Lås guld', u'Lås fri XP', u'Lås obligationer', u'Belønnings- / specialkøretøjer', u'Ikke kampklar', u'Uden Ace Tanker', u'Færre end tre mærker', u'Forskning tilgængelig', u'Feltmodifikation ikke fuldført', u'Besætningen er ikke fuldt trænet', u'Forskning ikke fuldført'),
    'de': (u'Intelligente Filter', u'Karussell und Karten', u'Sortierung', u'Währungsschutz', u'Statistiken auf Fahrzeugkarten', u'Mindestgefechte für Statistiken', u'Karussellreihen', u'Automatisch', u'Standardsortierung', u'Absteigend', u'„Fahrzeug kaufen“ ausblenden', u'„Stellplatz kaufen“ ausblenden', u'„Fahrzeug wiederherstellen“ ausblenden', u'Gold sperren', u'Freie EP sperren', u'Anleihen sperren', u'Belohnungs- / Spezialfahrzeuge', u'Nicht gefechtsbereit', u'Ohne Panzerass', u'Weniger als drei Markierungen', u'Erforschung verfügbar', u'Feldmodifikation nicht abgeschlossen', u'Besatzung nicht vollständig ausgebildet', u'Erforschung nicht abgeschlossen'),
    'el': (u'Έξυπνα φίλτρα', u'Καρουζέλ και κάρτες', u'Ταξινόμηση', u'Προστασία νομισμάτων', u'Στατιστικά στις κάρτες', u'Ελάχιστες μάχες για στατιστικά', u'Σειρές καρουζέλ', u'Αυτόματα', u'Βασική ταξινόμηση', u'Φθίνουσα', u'Απόκρυψη «Αγορά οχήματος»', u'Απόκρυψη «Αγορά θέσης»', u'Απόκρυψη «Ανάκτηση οχήματος»', u'Κλείδωμα χρυσού', u'Κλείδωμα ελεύθερης εμπειρίας', u'Κλείδωμα ομολόγων', u'Οχήματα ανταμοιβής / ειδικά', u'Μη έτοιμα για μάχη', u'Χωρίς Άσο', u'Λιγότερα από τρία σήματα', u'Διαθέσιμη έρευνα', u'Η Διαμόρφωση Πεδίου δεν ολοκληρώθηκε', u'Το πλήρωμα δεν εκπαιδεύτηκε πλήρως', u'Η έρευνα δεν ολοκληρώθηκε'),
    'es': (u'Filtros inteligentes', u'Carrusel y tarjetas', u'Ordenación', u'Protección de divisas', u'Estadísticas en las tarjetas', u'Batallas mínimas para estadísticas', u'Filas del carrusel', u'Automático', u'Orden predeterminado', u'Descendente', u'Ocultar «Comprar vehículo»', u'Ocultar «Comprar espacio»', u'Ocultar «Recuperar vehículo»', u'Bloquear oro', u'Bloquear experiencia libre', u'Bloquear bonos', u'Vehículos de recompensa / especiales', u'No listo para la batalla', u'Sin As de Batalla', u'Menos de tres marcas', u'Investigación disponible', u'Modificación de campo incompleta', u'Tripulación sin entrenar por completo', u'Investigación incompleta'),
    'fi': (u'Älykkäät suodattimet', u'Karuselli ja kortit', u'Lajittelu', u'Valuuttasuojaus', u'Tilastot ajoneuvokorteissa', u'Tilastojen vähimmäistaistelut', u'Karusellirivit', u'Automaattinen', u'Oletuslajittelu', u'Laskeva', u'Piilota „Osta ajoneuvo“', u'Piilota „Osta paikka“', u'Piilota „Palauta ajoneuvo“', u'Lukitse kulta', u'Lukitse vapaa kokemus', u'Lukitse bondit', u'Palkinto- / erikoisajoneuvot', u'Ei taisteluvalmis', u'Ilman Ässämerkkiä', u'Alle kolme merkkiä', u'Tutkimus saatavilla', u'Kenttämuokkaus kesken', u'Miehistö ei ole täysin koulutettu', u'Tutkimus kesken'),
    'fr': (u'Filtres intelligents', u'Carrousel et cartes', u'Tri', u'Protection des monnaies', u'Statistiques sur les cartes', u'Batailles minimales pour les statistiques', u'Lignes du carrousel', u'Automatique', u'Tri par défaut', u'Décroissant', u'Masquer «Acheter un véhicule»', u'Masquer «Acheter une place»', u'Masquer «Récupérer un véhicule»', u'Verrouiller l’or', u'Verrouiller l’EXP libre', u'Verrouiller les obligations', u'Véhicules de récompense / spéciaux', u'Pas prêt au combat', u'Sans As du char', u'Moins de trois marques', u'Recherche disponible', u'Modification de terrain incomplète', u'Équipage pas entièrement entraîné', u'Recherche incomplète'),
    'hr': (u'Pametni filtri', u'Vrtuljak i kartice', u'Razvrstavanje', u'Zaštita valuta', u'Statistika na karticama', u'Minimalni broj bitaka', u'Redovi vrtuljka', u'Automatski', u'Zadano razvrstavanje', u'Silazno', u'Sakrij „Kupi vozilo“', u'Sakrij „Kupi mjesto“', u'Sakrij „Obnovi vozilo“', u'Zaključaj zlato', u'Zaključaj slobodno iskustvo', u'Zaključaj obveznice', u'Nagradna / posebna vozila', u'Nije spremno za bitku', u'Bez Majstora tenkista', u'Manje od tri oznake', u'Istraživanje dostupno', u'Terenska modifikacija nije dovršena', u'Posada nije potpuno obučena', u'Istraživanje nije dovršeno'),
    'hu': (u'Intelligens szűrők', u'Járműsáv és kártyák', u'Rendezés', u'Valutavédelem', u'Statisztikák a kártyákon', u'Minimális csataszám', u'Járműsáv sorai', u'Automatikus', u'Alapértelmezett rendezés', u'Csökkenő', u'„Jármű vásárlása” elrejtése', u'„Férőhely vásárlása” elrejtése', u'„Jármű visszaállítása” elrejtése', u'Arany zárolása', u'Szabad XP zárolása', u'Kötvények zárolása', u'Jutalom- / különleges járművek', u'Nem harckész', u'Ász nélkül', u'Háromnál kevesebb kiválóságjel', u'Kutatás elérhető', u'Befejezetlen harctéri módosítás', u'A legénység nincs teljesen kiképezve', u'Befejezetlen kutatás'),
    'it': (u'Filtri intelligenti', u'Carosello e schede', u'Ordinamento', u'Protezione valute', u'Statistiche sulle schede', u'Battaglie minime per le statistiche', u'Righe del carosello', u'Automatico', u'Ordinamento predefinito', u'Decrescente', u'Nascondi «Acquista veicolo»', u'Nascondi «Acquista posto»', u'Nascondi «Recupera veicolo»', u'Blocca oro', u'Blocca Exp tecnica', u'Blocca titoli', u'Veicoli ricompensa / speciali', u'Non pronto alla battaglia', u'Senza Asso carrista', u'Meno di tre marchi', u'Ricerca disponibile', u'Modifica tecnica incompleta', u'Equipaggio non completamente addestrato', u'Ricerca incompleta'),
    'lt': (u'Išmanieji filtrai', u'Karuselė ir kortelės', u'Rikiavimas', u'Valiutų apsauga', u'Statistika kortelėse', u'Mažiausias mūšių skaičius', u'Karuselės eilutės', u'Automatiškai', u'Numatytasis rikiavimas', u'Mažėjančiai', u'Slėpti „Pirkti mašiną“', u'Slėpti „Pirkti vietą“', u'Slėpti „Atkurti mašiną“', u'Užrakinti auksą', u'Užrakinti laisvąją patirtį', u'Užrakinti obligacijas', u'Atlygio / specialiosios mašinos', u'Nepasirengusi mūšiui', u'Be Tankisto aso', u'Mažiau nei trys žymės', u'Galima tyrinėti', u'Neužbaigta lauko modifikacija', u'Įgula nevisiškai išmokyta', u'Neužbaigtas tyrimas'),
    'lv': (u'Viedie filtri', u'Karuselis un kartītes', u'Kārtošana', u'Valūtu aizsardzība', u'Statistika kartītēs', u'Minimālais kauju skaits', u'Karuseļa rindas', u'Automātiski', u'Noklusējuma kārtošana', u'Dilstoši', u'Paslēpt „Pirkt transportlīdzekli“', u'Paslēpt „Pirkt vietu“', u'Paslēpt „Atjaunot transportlīdzekli“', u'Bloķēt zeltu', u'Bloķēt brīvo pieredzi', u'Bloķēt obligācijas', u'Balvu / īpašie transportlīdzekļi', u'Nav gatavs kaujai', u'Bez Tankista dūža', u'Mazāk par trim atzīmēm', u'Pieejama izpēte', u'Nepabeigta lauka modifikācija', u'Apkalpe nav pilnībā apmācīta', u'Nepabeigta izpēte'),
    'nl': (u'Slimme filters', u'Carrousel en kaarten', u'Sortering', u'Valutabescherming', u'Statistieken op kaarten', u'Minimaal aantal gevechten', u'Carrouselrijen', u'Automatisch', u'Standaardsortering', u'Aflopend', u'„Voertuig kopen“ verbergen', u'„Plaats kopen“ verbergen', u'„Voertuig herstellen“ verbergen', u'Goud vergrendelen', u'Vrije ervaring vergrendelen', u'Obligaties vergrendelen', u'Belonings- / speciale voertuigen', u'Niet gevechtsklaar', u'Zonder Tank Ace', u'Minder dan drie markeringen', u'Onderzoek beschikbaar', u'Veldmodificatie niet voltooid', u'Bemanning niet volledig opgeleid', u'Onderzoek niet voltooid'),
    'no': (u'Smarte filtre', u'Karusell og kort', u'Sortering', u'Valutabesk yttelse', u'Statistikk på kort', u'Minimum antall kamper', u'Karusellrader', u'Automatisk', u'Standardsortering', u'Synkende', u'Skjul „Kjøp kjøretøy“', u'Skjul „Kjøp plass“', u'Skjul „Gjenopprett kjøretøy“', u'Lås gull', u'Lås fri XP', u'Lås obligasjoner', u'Belønnings- / spesialkjøretøy', u'Ikke kampklar', u'Uten Tank Ace', u'Færre enn tre merker', u'Forskning tilgjengelig', u'Feltmodifikasjon ikke fullført', u'Mannskapet er ikke fullt trent', u'Forskning ikke fullført'),
    'pl': (u'Inteligentne filtry', u'Karuzela i karty', u'Sortowanie', u'Ochrona walut', u'Statystyki na kartach', u'Minimalna liczba bitew', u'Rzędy karuzeli', u'Automatycznie', u'Sortowanie domyślne', u'Malejąco', u'Ukryj „Kup pojazd“', u'Ukryj „Kup miejsce“', u'Ukryj „Odzyskaj pojazd“', u'Zablokuj złoto', u'Zablokuj wolne doświadczenie', u'Zablokuj obligacje', u'Pojazdy-nagrody / specjalne', u'Niegotowy do bitwy', u'Bez Asa pancernego', u'Mniej niż trzy odznaki', u'Dostępne badanie', u'Nieukończona modyfikacja polowa', u'Załoga nie jest w pełni wyszkolona', u'Nieukończone badania'),
    'pt': (u'Filtros inteligentes', u'Carrossel e cartões', u'Ordenação', u'Proteção de moedas', u'Estatísticas nos cartões', u'Mínimo de batalhas', u'Linhas do carrossel', u'Automático', u'Ordenação padrão', u'Decrescente', u'Ocultar „Comprar veículo“', u'Ocultar „Comprar vaga“', u'Ocultar „Recuperar veículo“', u'Bloquear ouro', u'Bloquear experiência livre', u'Bloquear títulos', u'Veículos de recompensa / especiais', u'Não está pronto para batalha', u'Sem Ás do Tanque', u'Menos de três marcas', u'Pesquisa disponível', u'Modificação de Campo incompleta', u'Tripulação não totalmente treinada', u'Pesquisa incompleta'),
    'ro': (u'Filtre inteligente', u'Carusel și carduri', u'Sortare', u'Protecția monedelor', u'Statistici pe carduri', u'Număr minim de bătălii', u'Rânduri carusel', u'Automat', u'Sortare implicită', u'Descrescător', u'Ascunde „Cumpără vehicul“', u'Ascunde „Cumpără loc“', u'Ascunde „Recuperează vehicul“', u'Blochează aurul', u'Blochează experiența liberă', u'Blochează obligațiunile', u'Vehicule recompensă / speciale', u'Nepregătit de luptă', u'Fără Asul tanchiștilor', u'Mai puțin de trei însemne', u'Cercetare disponibilă', u'Modificare de teren incompletă', u'Echipaj incomplet instruit', u'Cercetare incompletă'),
    'sr': (u'Pametni filteri', u'Karusel i kartice', u'Sortiranje', u'Zaštita valuta', u'Statistika na karticama', u'Minimalni broj bitaka', u'Redovi karusela', u'Automatski', u'Podrazumevano sortiranje', u'Opadajuće', u'Sakrij „Kupi vozilo“', u'Sakrij „Kupi mesto“', u'Sakrij „Obnovi vozilo“', u'Zaključaj zlato', u'Zaključaj slobodno iskustvo', u'Zaključaj obveznice', u'Nagradna / specijalna vozila', u'Nije spremno za bitku', u'Bez Tenkovskog asa', u'Manje od tri oznake', u'Istraživanje dostupno', u'Terenska modifikacija nije završena', u'Posada nije potpuno obučena', u'Istraživanje nije završeno'),
    'sv': (u'Smarta filter', u'Karusell och kort', u'Sortering', u'Valutaskydd', u'Statistik på kort', u'Minsta antal strider', u'Karusellrader', u'Automatiskt', u'Standardsortering', u'Fallande', u'Dölj „Köp fordon“', u'Dölj „Köp plats“', u'Dölj „Återställ fordon“', u'Lås guld', u'Lås fri erfarenhet', u'Lås obligationer', u'Belönings- / specialfordon', u'Inte stridsklar', u'Utan Tank Ace', u'Färre än tre märken', u'Forskning tillgänglig', u'Fältmodifiering inte slutförd', u'Besättningen är inte fullt tränad', u'Forskning inte slutförd'),
    'tr': (u'Akıllı filtreler', u'Araç paneli ve kartlar', u'Sıralama', u'Para birimi koruması', u'Kartlarda istatistik', u'İstatistik için minimum savaş', u'Araç paneli satırları', u'Otomatik', u'Varsayılan sıralama', u'Azalan', u'„Araç satın al“ı gizle', u'„Yuva satın al“ı gizle', u'„Aracı geri al“ı gizle', u'Altını kilitle', u'Serbest deneyimi kilitle', u'Bonoları kilitle', u'Ödül / özel araçlar', u'Savaşa hazır değil', u'Tank Ası olmadan', u'Üçten az işaret', u'Araştırma mevcut', u'Saha Modifikasyonu tamamlanmadı', u'Mürettebat tam eğitilmedi', u'Araştırma tamamlanmadı')
}

SETTINGS_SORT_OPTIONS = {
    'bg': (u'Стандартен ред', u'Битки', u'Победи', u'Средни щети', u'Отличителни знаци', u'Последно играна'),
    'cs': (u'Výchozí pořadí', u'Bitvy', u'Vítězství', u'Průměrné poškození', u'Znaky na dělu', u'Naposledy hráno'),
    'da': (u'Standardrækkefølge', u'Kampe', u'Sejrsprocent', u'Gennemsnitlig skade', u'Mærker på kanonen', u'Sidst spillet'),
    'de': (u'Standardreihenfolge', u'Gefechte', u'Siegrate', u'Durchschnittsschaden', u'Erfolgsmarkierungen', u'Zuletzt gespielt'),
    'el': (u'Βασική σειρά', u'Μάχες', u'Ποσοστό νικών', u'Μέση ζημιά', u'Σήματα αριστείας', u'Τελευταία χρήση'),
    'es': (u'Orden predeterminado', u'Batallas', u'Victorias', u'Daño medio', u'Marcas de excelencia', u'Última batalla'),
    'fi': (u'Oletusjärjestys', u'Taistelut', u'Voittoprosentti', u'Keskivahinko', u'Erinomaisuusmerkit', u'Viimeksi pelattu'),
    'fr': (u'Ordre par défaut', u'Batailles', u'Taux de victoires', u'Dégâts moyens', u'Marques d’excellence', u'Dernière bataille'),
    'hr': (u'Zadani redoslijed', u'Bitke', u'Postotak pobjeda', u'Prosječna šteta', u'Oznake izvrsnosti', u'Posljednje igrano'),
    'hu': (u'Alapértelmezett sorrend', u'Csaták', u'Győzelmi arány', u'Átlagsebzés', u'Kiválóságjelek', u'Utoljára játszott'),
    'it': (u'Ordine predefinito', u'Battaglie', u'Percentuale vittorie', u'Danno medio', u'Marchi d’Eccellenza', u'Ultima battaglia'),
    'lt': (u'Numatytoji tvarka', u'Mūšiai', u'Pergalių santykis', u'Vidutinė žala', u'Meistriškumo žymės', u'Vėliausiai žaista'),
    'lv': (u'Noklusējuma secība', u'Kaujas', u'Uzvaru attiecība', u'Vidējie bojājumi', u'Izcilības atzīmes', u'Pēdējā kauja'),
    'nl': (u'Standaardvolgorde', u'Gevechten', u'Winstpercentage', u'Gemiddelde schade', u'Uitmuntendheidsmarkeringen', u'Laatst gespeeld'),
    'no': (u'Standardrekkefølge', u'Kamper', u'Seiersprosent', u'Gjennomsnittlig skade', u'Utmerkelsesmerker', u'Sist spilt'),
    'pl': (u'Kolejność domyślna', u'Bitwy', u'Procent zwycięstw', u'Średnie uszkodzenia', u'Odznaki biegłości', u'Ostatnia bitwa'),
    'pt': (u'Ordem padrão', u'Batalhas', u'Taxa de vitórias', u'Dano médio', u'Marcas de Excelência', u'Última batalha'),
    'ro': (u'Ordine implicită', u'Bătălii', u'Rata victoriilor', u'Daune medii', u'Însemne de excelență', u'Ultima bătălie'),
    'sr': (u'Podrazumevani redosled', u'Bitke', u'Procenat pobeda', u'Prosečna šteta', u'Oznake izuzetnosti', u'Poslednje igrano'),
    'sv': (u'Standardordning', u'Strider', u'Segerfrekvens', u'Genomsnittlig skada', u'Skicklighetsmärken', u'Senast spelad'),
    'tr': (u'Varsayılan sıra', u'Savaşlar', u'Galibiyet oranı', u'Ortalama hasar', u'Mükemmellik İşaretleri', u'Son oynanan')
}

SETTINGS_PRIORITY_SORT_OPTIONS = {
    'bg': u'Основни > полева модификация > стандартно',
    'cs': u'Hlavní > polní modifikace > výchozí',
    'da': u'Primære > feltmodifikation > standard',
    'de': u'Primär > Feldmodifikation > Standard',
    'el': u'Κύρια > Διαμόρφωση Πεδίου > βασική σειρά',
    'es': u'Principales > modificación de campo > orden predeterminado',
    'fi': u'Ensisijaiset > kenttämuokkaus > oletus',
    'fr': u'Principaux > modification de terrain > ordre par défaut',
    'hr': u'Primarna > terenska modifikacija > zadano',
    'hu': u'Elsődleges > harctéri módosítás > alapértelmezett',
    'it': u'Principali > modifica tecnica > ordine predefinito',
    'lt': u'Pagrindinės > lauko modifikacija > numatyta tvarka',
    'lv': u'Galvenie > lauka modifikācija > noklusējums',
    'nl': u'Primair > veldmodificatie > standaard',
    'no': u'Primære > feltmodifikasjon > standard',
    'pl': u'Podstawowe > modyfikacja polowa > domyślnie',
    'pt': u'Principais > Modificação de Campo > ordem padrão',
    'ro': u'Principale > modificare de teren > ordine implicită',
    'sr': u'Primarna > terenska modifikacija > podrazumevano',
    'sv': u'Primära > fältmodifiering > standard',
    'tr': u'Birincil > Saha Modifikasyonu > varsayılan'
}

SETTINGS_BATTLE_PASS_SORT_OPTIONS = {
    'bg': u'Точки за Бойния пропуск', 'cs': u'Body Battle Passu',
    'da': u'Battle Pass-point', 'de': u'Battle-Pass-Punkte',
    'el': u'Πόντοι Battle Pass', 'es': u'Puntos del Pase de Batalla',
    'fi': u'Taistelupassin pisteet', 'fr': u'Points du Passe de combat',
    'hr': u'Bodovi Bojne propusnice', 'hu': u'Csatabelépő-pontok',
    'it': u'Punti Pass di Battaglia', 'lt': u'Kovos paso taškai',
    'lv': u'Kaujas caurlaides punkti', 'nl': u'Battle Pass-punten',
    'no': u'Battle Pass-poeng', 'pl': u'Punkty Przepustki Bitewnej',
    'pt': u'Pontos do Passe de Batalha', 'ro': u'Puncte Battle Pass',
    'sr': u'Poeni Borbene propusnice', 'sv': u'Battle Pass-poäng',
    'tr': u'Savaş Kartı Puanları'
}


def _settings_language():
    language = (getClientLanguage() or 'en').lower().replace('-', '_')
    language = {
        'en_gb': 'en', 'en_us': 'en', 'en_zw': 'en',
        'es_ar': 'es', 'es_mx': 'es', 'pt_br': 'pt', 'sr_latn': 'sr'
    }.get(language, language)
    return language if language in SETTINGS_TEXT or language in SETTINGS_VISIBLE_I18N else language.split('_')[0]


def _settings_labels():
    language = _settings_language()
    result = dict(SETTINGS_TEXT['en'])
    result.update(SETTINGS_TEXT.get(language, {}))
    if language in SETTINGS_VISIBLE_I18N:
        result.update(dict(zip(SETTINGS_VISIBLE_KEYS, SETTINGS_VISIBLE_I18N[language])))
    return result


def _settings_filter_enabled(filter_id):
    return filter_id in CONFIG.get('filters', {}).get('enabled', [])


def _register_settings():
    global SETTINGS_REGISTERED
    if SETTINGS_REGISTERED:
        return
    try:
        from gui.modsSettingsApi import g_modsSettingsApi, templates
        text = _settings_labels()
        language = _settings_language()
        sort_options = [u'Default', u'Battles', u'Win rate', u'Average damage',
                        u'Marks of Excellence', u'Battle Pass points', u'Last played',
                        u'Primary > Field Modification > default']
        if language == 'ru':
            sort_options = [u'Обычная', u'Бои', u'Победы', u'Средний урон',
                            u'Отметки', u'Очки Боевого пропуска', u'Последний бой',
                            u'Основные > полевая модернизация > обычный порядок']
        elif language == 'uk':
            sort_options = [u'Звичайна', u'Бої', u'Перемоги', u'Середня шкода',
                            u'Відмітки', u'Очки Бойової перепустки', u'Останній бій',
                            u'Основні > польова модернізація > звичайний порядок']
        elif language in SETTINGS_SORT_OPTIONS:
            sort_options = list(SETTINGS_SORT_OPTIONS[language])
            sort_options.insert(5, SETTINGS_BATTLE_PASS_SORT_OPTIONS.get(
                language, u'Battle Pass points'))
            sort_options.append(SETTINGS_PRIORITY_SORT_OPTIONS.get(language, sort_options[-1]))
        rows_value = 0 if _carousel_auto() else (_carousel_rows() or 2)
        column1 = [templates.createLabel(text['filters'], text['native'])]
        for filter_id in FILTER_ORDER:
            if filter_id == 'all':
                continue
            column1.append(templates.createCheckbox(
                text.get('filter_' + filter_id, filter_id), 'filter_' + filter_id,
                _settings_filter_enabled(filter_id), text['filterHint']))
        column1.extend([
            templates.createEmpty(8),
            templates.createLabel(text['display']),
            templates.createCheckbox(text['cardStats'], 'cardStatsEnabled',
                                     bool(CONFIG.get('cardStats', {}).get('enabled', True))),
            templates.createNumericStepper(text['minBattles'], 'minimumBattles',
                                           int(CONFIG.get('cardStats', {}).get('minimumBattles', 1)),
                                           0, 1000, 1, manual=True),
            templates.createDropdown(text['rows'], 'carouselRows',
                                     [text['auto'], u'1', u'2', u'3', u'4'], rows_value)
        ])
        column2 = [
            templates.createLabel(text['sorting']),
            templates.createCheckbox(text['sorting'], 'sortingEnabled',
                                     bool(CONFIG.get('sorting', {}).get('enabled', True))),
            templates.createDropdown(text['sortMode'], 'sortMode', sort_options, SORT_ORDER.index(_sort_mode())),
            templates.createCheckbox(text['descending'], 'sortDescending', _sort_descending()),
            templates.createEmpty(8),
            templates.createCheckbox(text['hideBuyTank'], 'hideBuyTank',
                                     bool(CONFIG.get('actionCards', {}).get('hideBuyTank', False))),
            templates.createCheckbox(text['hideBuySlot'], 'hideBuySlot',
                                     bool(CONFIG.get('actionCards', {}).get('hideBuySlot', False))),
            templates.createCheckbox(text['hideRestoreTank'], 'hideRestoreTank',
                                     bool(CONFIG.get('actionCards', {}).get('hideRestoreTank', False)))
        ]
        template = {
            'modDisplayName': u'Hangar Carousel Plus',
            'settingsVersion': 2,
            'enabled': bool(CONFIG.get('enabled', True)),
            'column1': column1,
            'column2': column2
        }
        g_modsSettingsApi.setModTemplate(
            'com.rcooler.hangar_carousel_plus', template, _on_settings_changed)
        SETTINGS_REGISTERED = True
        LOGGER.info('ModsSettingsAPI integration registered')
    except Exception:
        LOGGER.exception('Unable to register ModsSettingsAPI integration')


def _on_settings_changed(linkage, settings):
    if linkage != 'com.rcooler.hangar_carousel_plus':
        return
    try:
        CONFIG['enabled'] = bool(settings.get('enabled', CONFIG.get('enabled', True)))
        enabled_filters = ['all']
        for filter_id in FILTER_ORDER:
            if filter_id != 'all' and bool(settings.get('filter_' + filter_id, _settings_filter_enabled(filter_id))):
                enabled_filters.append(filter_id)
        CONFIG.setdefault('filters', {})['enabled'] = enabled_filters
        CONFIG.setdefault('cardStats', {})['enabled'] = bool(settings.get('cardStatsEnabled', True))
        CONFIG['cardStats']['minimumBattles'] = max(0, int(settings.get('minimumBattles', 1)))
        CONFIG.setdefault('sorting', {})['enabled'] = bool(settings.get('sortingEnabled', True))
        CONFIG['sorting']['descending'] = bool(settings.get('sortDescending', True))
        actions = CONFIG.setdefault('actionCards', {})
        actions['hideBuyTank'] = bool(settings.get('hideBuyTank', False))
        actions['hideBuySlot'] = bool(settings.get('hideBuySlot', False))
        actions['hideRestoreTank'] = bool(settings.get('hideRestoreTank', False))
        requested_sort = int(settings.get('sortMode', SORT_ORDER.index(_sort_mode())))
        requested_sort = max(0, min(len(SORT_ORDER) - 1, requested_sort))
        CONFIG['sorting']['default'] = SORT_ORDER[requested_sort]
        _save_config()

        for filter_id in list(ACTIVE_FILTERS):
            if filter_id not in enabled_filters:
                ACTIVE_FILTERS.discard(filter_id)
        if not CONFIG['enabled']:
            ACTIVE_FILTERS.clear()
        RUNTIME_STATE['activeFilters'] = sorted(ACTIVE_FILTERS)
        _save_runtime()
        _set_sorting(SORT_ORDER[requested_sort], bool(settings.get('sortDescending', True)))
        _set_carousel_rows(int(settings.get('carouselRows', 0)))
        _refresh_native_vehicle_model()
        for model in list(MODELS):
            model.refresh()
    except Exception:
        LOGGER.exception('Unable to apply ModsSettingsAPI settings')


try:
    BigWorld.callback(0.1, _register_settings)
except Exception:
    LOGGER.exception('Hangar Carousel Plus services failed to initialize')

if CONFIG.get('enabled', True):
    try:
        _patch_vehicle_filter_model()
        _patch_vehicle_filters_provider()
        _patch_vehicle_tooltip()
        _patch_vehicle_statistics_presenter()
        _patch_legacy_playlist_cleanup()
        _register_battle_pass_events()
        g_playerEvents.onAvatarReady += _track_last_played
        LOGGER.info('Hangar Carousel Plus %s loaded', MOD_VERSION)
    except Exception:
        LOGGER.exception('Hangar Carousel Plus failed to initialize')
