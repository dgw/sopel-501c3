"""Custom data types for the sopel-501c3 plugin.

Copyright (c) 2025 dgw, technobabbl.es

Licensed under the Eiffel Forum License 2.
"""
from __future__ import annotations

from dataclasses import dataclass

# in py3.10+ can use slots=True for optimization
# and kw_only=True to force clearer constructor calls
@dataclass(frozen=True)
class NPO:
    """A 501(c)(3) nonprofit organization listed in Publication 78."""
    ein: str
    """Employer Identification Number (EIN) of the nonprofit org."""
    name: str
    """Name of the nonprofit org."""
    city: str
    """City where the nonprofit org is located."""
    state: str
    """State where the nonprofit org is located (two-letter code)."""
    country: str
    """Country where the nonprofit org is located (usually `United States`)."""
    deductibility_codes: str
    """Deductibility codes (public charity, private foundation, lodge, etc.).

    Comma-separated string of codes.
    """

    @classmethod
    def from_db_row(cls, row) -> NPO:
        """Create a new NPO instance from a database row."""
        return cls(
            ein=row.ein,
            name=row.name,
            city=row.city,
            state=row.state,
            country=row.country,
            deductibility_codes=row.deductibility_codes,
        )

    def __post_init__(self):
        # Add a derived attribute for the deductibility codes as a tuple.
        # Checking a string's existence in the tuple is safer than checking if
        # the original comma-delimited string contains a substring, in case of
        # future codes being added that overlap with any existing ones.
        # Because the object is frozen, can't directly assign to attrs.
        object.__setattr__(
            self,
            'deductibility_codes_tuple',
            tuple(self.deductibility_codes.split(','))
        )

    @property
    def ein_display(self) -> str:
        """Formatted EIN for display to user."""
        return f'{self.ein[:2]}-{self.ein[2:]}'

    @property
    def isPC(self) -> bool:
        """Check if the entity is a public charity."""
        return 'PC' in self.deductibility_codes_tuple

    @property
    def isPF(self) -> bool:
        """Check if the entity is a private foundation."""
        return 'PF' in self.deductibility_codes_tuple

    @property
    def isPOF(self) -> bool:
        """Check if the entity is a private operating foundation."""
        return 'POF' in self.deductibility_codes_tuple

    @property
    def isForeign(self) -> bool:
        """Check if the entity is a foreign-addressed organization."""
        return 'FORGN' in self.deductibility_codes_tuple

    @property
    def isGroup(self) -> bool:
        """Check if the entity is an exemption group."""
        return 'GROUP' in self.deductibility_codes_tuple

    @property
    def isLodge(self) -> bool:
        """Check if the entity is a lodge."""
        return 'LODGE' in self.deductibility_codes_tuple

    @property
    def isEO(self) -> bool:
        """Check if the entity is an "other" exempt organization.

        This is a catch-all category for entities described in Internal Revenue
        Code section 170(c) that are neither PC nor PF.
        """
        return 'EO' in self.deductibility_codes_tuple

    @property
    def isSO(self) -> bool:
        """Check if the entity is a Type I, Type II, or functionally integrated
        Type III supporting organization."""
        return 'SO' in self.deductibility_codes_tuple

    @property
    def isSONFI(self) -> bool:
        """Check if the entity is a non-functionally integrated Type III
        supporting organization."""
        return 'SONFI' in self.deductibility_codes_tuple

    @property
    def isSOUNK(self) -> bool:
        """Check if the entity is a supporting organization of unspecified
        type."""
        return 'SOUNK' in self.deductibility_codes_tuple

    @property
    def isSupporting(self) -> bool:
        """Check if the entity is a supporting organization of any type."""
        # Useful? I don't know yet, but it's simple to just add the method.
        return self.isSO() or self.isSONFI() or self.isSOUNK()

    @property
    def isUnknown(self) -> bool:
        """Check if the entity's public charity status is undetermined."""
        return 'UNKWN' in self.deductibility_codes_tuple
