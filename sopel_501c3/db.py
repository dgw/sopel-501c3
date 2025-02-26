"""Database module for sopel-501c3 plugin.

Copyright (c) 2025 dgw, technobabbl.es

Licensed under the Eiffel Forum License 2.
"""
from __future__ import annotations

import itertools
import time
from typing import TYPE_CHECKING

from sqlalchemy import Column, String
from sqlalchemy.sql import select

from sopel.db import BASE, MYSQL_TABLE_ARGS
from sopel.tools import get_logger

from .types import NPO

if TYPE_CHECKING:
    from typing import Iterable

    from sopel.bot import Sopel


LOGGER = get_logger('501c3.db')


class NPOs(BASE):
    """Table for storing 501(c)(3) nonprofit organizations."""
    __tablename__ = '501c3_npos'
    __table_args__ = MYSQL_TABLE_ARGS

    ein = Column(String(9), index=True, primary_key=True)
    name = Column(String(), index=True)
    city = Column(String(), index=True)
    state = Column(String(), index=True)
    country = Column(String(), index=True)
    deductibility_codes = Column(String(), index=True)

    @classmethod
    def from_npo(cls, npo: NPO):
        """Create a new instance from an NPO dataclass object."""
        return cls(
            ein=npo.ein,
            name=npo.name,
            city=npo.city,
            state=npo.state,
            country=npo.country,
            deductibility_codes=npo.deductibility_codes,
        )


class NPODB:
    """Database interface for the sopel-501c3 plugin."""

    def __init__(self, bot: Sopel):
        self.db = bot.db
        BASE.metadata.create_all(self.db.engine)

    def bulk_add_NPOs(
        self,
        it: Iterable[NPO],
        batch_size: int = 10000,
        background: bool = True,
    ):
        """Add multiple nonprofit organizations to the database."""
        if background:
            LOGGER.info('Processing bulk NPO add in the background')
        else:
            LOGGER.info('Processing bulk NPO add in the foreground')
        LOGGER.info('Bulk NPO add batch size: %d', batch_size)

        batch_iterator = iter(it)
        batches = 0
        with self.db.session() as session:
            for first in batch_iterator:
                batch = itertools.chain(
                    [first], itertools.islice(batch_iterator, batch_size - 1)
                )
                for npo in batch:
                    session.merge(NPOs.from_npo(npo))

                batches += 1
                session.commit()

                # report progress every 10 batches, or after every batch if the
                # batch size is over 10k
                if batch_size > 10000 or batches % 10 == 0:
                    LOGGER.debug(
                        'Bulk added %d NPOs so far',
                        batches * batch_size,
                    )

                if background:
                    time.sleep(1)

            session.commit()

        LOGGER.info(
            'Finished bulk adding %d NPOs',
            batches * batch_size + len(batch),
        )

    def add_npo(self, npo: NPO):
        """Add a new nonprofit organization to the database."""
        org = NPOs.from_npo(npo)

        with self.db.session() as session:
            session.add(org)
            session.commit()

    def find_npos(self, query: str) -> list[NPO]:
        """Search for nonprofit organizations by name or EIN."""
        if (no_hyphens := ''.join(c for c in query if c != '-')).isdigit():
            # EIN lookup; discard hyphens
            query = no_hyphens

        with self.db.session() as session:
            results = session.execute(
                select(NPOs).where(
                    (NPOs.name.ilike(f'%{query}%')) | (NPOs.ein == query)
                )
            ).scalars().all()
        return [NPO.from_db_row(row) for row in results]

    def get_npo(self, ein) -> NPO | None:
        """Retrieve a nonprofit organization by its EIN."""
        with self.db.session() as session:
            result = session.execute(
                select(NPOs).where(NPOs.ein == ein)
            ).scalar_one_or_none()
        if result:
            return NPO.from_db_row(result)
        # not found
        return None

    def remove_npo(self, ein):
        """Remove a nonprofit organization from the database by its EIN."""
        with self.db.session() as session:
            org = session.execute(
                select(NPOs).where(NPOs.ein == ein)
            ).scalar_one_or_none()

            if org:
                session.delete(org)
                session.commit()

    def update_npo(self, npo: NPO):
        """Update a nonprofit organization in the database."""
        org = NPOs.from_npo(npo)

        with self.db.session() as session:
            session.merge(org)
            session.commit()
