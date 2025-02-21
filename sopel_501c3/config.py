"""Configuration types & helpers for the sopel-501c3 plugin.

Copyright (c) 2025 dgw, technobabbl.es

Licensed under the Eiffel Forum License 2.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sopel.config import types

if TYPE_CHECKING:
    from sopel.config import Config
    from sopel.bot import Sopel


SECTION_NAME = 'five01c3'


class Five01c3Section(types.StaticSection):
    """Configuration section for the sopel-501c3 plugin.

    Includes some extra settings that don't appear in the config wizard. Using
    these settings, minor changes to the ZIP file location or the name of the
    file inside it can be adapted to without code changes.

    If the file *format* changes, the plugin will need to be updated. You can
    only (reasonably) do so much with config!
    """
    update_interval = types.ValidatedAttribute(
        'update_interval',
        parse=int,
        default=7
    )
    """How often to check for updates to the Publication 78 data (in days)."""

    zip_url = types.ValidatedAttribute(
        'zip_url',
        default='https://apps.irs.gov/pub/epostcard/data-download-pub78.zip'
    )
    """URL from which to download the Publication 78 ZIP archive.

    Shouldn't be needed, but can be overridden if the IRS changes the URL.

    Omitted from wizard.
    """

    data_name = types.ValidatedAttribute(
        'data_name',
        default='data-download-pub78.txt'
    )
    """Name of the file inside the ZIP archive containing the Pub78 data.

    Shouldn't be needed, but can be overridden if the IRS changes the filename.

    Omitted from wizard.
    """


def wizard(config: Config):
    """Configure the sopel-501c3 plugin."""
    config.define_section(SECTION_NAME, Five01c3Section, validate=False)
    config.five01c3.configure_setting(
        'update_interval',
        'How often should I check for updates to the Publication 78 data? (days)'
    )


def init_config(bot: Sopel):
    """Initialize the sopel-501c3 plugin configuration."""
    bot.config.define_section(SECTION_NAME, Five01c3Section)
