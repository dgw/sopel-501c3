"""Utilities for sopel-501c3 plugin

Copyright (c) 2025 dgw, technobabbl.es

Licensed under the Eiffel Forum License 2.
"""
from __future__ import annotations

import csv
from io import BytesIO
from typing import TYPE_CHECKING
from urllib.error import HTTPError
from urllib.request import urlopen
import zipfile

from .types import NPO

if TYPE_CHECKING:
    from typing import BinaryIO, Generator


# custom CSV dialect for reading Publication 78 data files
csv.register_dialect(
    'pub78',
    delimiter='|',
    quotechar=None,
    doublequote=False,
    skipinitialspace=True,
    lineterminator='\r\n',
    quoting=csv.QUOTE_NONE,
)


def read_data_entries(
    zip_file: BinaryIO,
    filename: str = 'data-download-pub78.txt',
) -> Generator[NPO, None, None]:
    """Load Publication 78 data from an IRS ZIP file.

    The ``zip_file`` should be the ZIP archive as a file-like object.

    Optionally specify the ``filename`` of the file to read from the ZIP archive
    if it differs from the default (``data-download-pub78.txt``).
    """
    with zipfile.Path(zip_file, at=filename).open('r') as pub78_file:
        reader = csv.reader(pub78_file, dialect='pub78')

        for row in reader:
            if not row:
                # the file starts and/or ends with a blank line(s) sometimes
                continue

            ein, name, city, state, country, deductibility_codes = row
            yield NPO(
                ein,
                name,
                city,
                state,
                country,
                deductibility_codes,
            )


def fetch_pub78_data(
    url: str = 'https://apps.irs.gov/pub/epostcard/data-download-pub78.zip',
    filename: str = 'data-download-pub78.txt',
) -> Generator[NPO, None, None]:
    """Fetch Publication 78 data from the IRS website.

    Optionally specify a different ``url`` to download the ZIP archive from.

    Optionally specify a different ``filename`` to load from the ZIP archive.

    At time of writing, Exempt Organization data downloads are available at:
    https://www.irs.gov/charities-non-profits/tax-exempt-organization-search-bulk-data-downloads
    """
    try:
        with urlopen(url) as response:
            yield from read_data_entries(BytesIO(response.read()), filename)
    except HTTPError:
        raise RuntimeError(f'Failed to fetch Publication 78 data from {url}')
