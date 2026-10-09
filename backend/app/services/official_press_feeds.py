"""Public press-release feeds used to find a primary source for publisher items."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OfficialPressFeed:
    key: str
    name: str
    url: str
    # Politics feeds mix companies and parties. Keep a release only when it names an authority.
    require_institution_word: bool = False


_POLICE_STATE_IDS: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16)

OFFICIAL_PRESS_FEEDS: tuple[OfficialPressFeed, ...] = (
    OfficialPressFeed(
        key="presseportal_polizei",
        name="Polizei",
        url="https://www.presseportal.de/rss/polizei.rss2",
    ),
    *(
        OfficialPressFeed(
            key=f"presseportal_polizei_{state_id}",
            name="Polizei",
            url=f"https://www.presseportal.de/rss/polizei/laender/{state_id}.rss2",
        )
        for state_id in _POLICE_STATE_IDS
    ),
    OfficialPressFeed(
        key="presseportal_politik",
        name="Behörde",
        url="https://www.presseportal.de/rss/politik.rss2",
        require_institution_word=True,
    ),
)
