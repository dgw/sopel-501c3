"""sopel-501c3

501(c)(3) nonprofit lookup plugin for Sopel IRC bots. Based on Publication 78 data.

Copyright (c) 2025 dgw, technobabbl.es

Licensed under the Eiffel Forum License 2.
"""
from __future__ import annotations

from datetime import datetime, timezone
from threading import Thread

from sopel import plugin
from sopel.tools import get_logger

from .config import init_config, wizard
from .db import NPODB
from .util import fetch_pub78_data


LOGGER = get_logger('501c3')
NPO_DB = '501c3_npo_db'


def configure(config):
    wizard(config)


def setup(bot):
    init_config(bot)

    bot.memory[NPO_DB] = NPODB(bot)

    # Check for updates on startup ONLY if the DB has never been populated.
    # Otherwise let, startup continue and wait for the interval to fire.
    # Slightly stale data is better than delaying startup for up to several
    # minutes if the `update_interval` has elapsed
    if not bot.db.get_plugin_value('501c3', 'last_update', 0):
        check_pub78_updates(bot, force=True, background=False)


@plugin.interval(3600)
def check_pub78_updates(bot, force=False, background=True):
    # wrapper triggered by interval, but the actual work is in a separate
    # function that can be run in a new thread
    job = Thread(
        name='pub78_db',
        target=_check_pub78_updates_impl,
        args=(bot,),
        kwargs={'force': force, 'background': background},
    )
    LOGGER.info('Starting Publication 78 update check in a new thread')
    job.start()
    LOGGER.info('Waiting for Publication 78 update check to complete...')
    job.join()


def _check_pub78_updates_impl(bot, force=False, background=True):
    now = datetime.now(timezone.utc)
    last_update = datetime.fromtimestamp(
        bot.db.get_plugin_value('501c3', 'last_update', 0),
        timezone.utc,
    )
    if not force and not (
        (delta := (now - last_update)).days >= bot.settings.five01c3.update_interval
    ):
        LOGGER.info(
            'Skipping Publication 78 data update. '
            'Update interval of %d days has not yet elapsed; delta is %s.',
            bot.settings.five01c3.update_interval,
            delta,
        )
        return

    LOGGER.info('Checking for updates to Publication 78 data...')
    if last_update.timestamp() == 0:
        LOGGER.info(
            'Starting/resuming initial data import. '
            'This might take a while.'
        )

    gen = fetch_pub78_data(
        bot.settings.five01c3.zip_url,
        bot.settings.five01c3.data_name,
    )
    bot.memory[NPO_DB].bulk_add_NPOs(
        gen,
        1000 if background else 10000,
        background=background,
    )

    # finally, store the last_update timestamp (loading the data is expected to
    # take a few moments, but the difference between when we start (`now`) and
    # when we finish is immaterial on the check interval time scale of days)
    bot.db.set_plugin_value('501c3', 'last_update', now.timestamp())
    LOGGER.info('Publication 78 update complete')


def shutdown(bot):
    del bot.memory[NPO_DB]


@plugin.command('npo', '501c3')
@plugin.output_prefix('[501c3] ')
def npo_lookup(bot, trigger):
    if not (query := trigger.group(2).strip()):
        bot.reply('You must provide a search query.')
        return

    results = bot.memory[NPO_DB].find_npos(query)
    if not results:
        bot.reply('No results found.')
        return

    for npo in results[:3]:
        body = npo.name
        trailing = f' ({npo.ein_display}) in '
        if (city := npo.city) and (state := npo.state):
            trailing += f'{city}, {state} '
        elif state and not city:
            trailing += f'{state} '
        elif city and not state:
            trailing += f'{city} '
        trailing += f'({npo.country})'
        trailing += f' | https://projects.propublica.com/nonprofits/organizations/{npo.ein}'
        bot.say(body, truncation='…', trailing=trailing)
