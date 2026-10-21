"""Public press-release feeds used to find a primary source for publisher items."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OfficialPressFeed:
    key: str
    name: str
    url: str
    # Mixed topic feeds include companies. Keep a release only when it names an authority.
    require_institution_word: bool = False


_POLICE_STATE_IDS: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16)

# Own press feeds. The public name is the institution readers should see.
_AUTHORITY_FEEDS: tuple[OfficialPressFeed, ...] = (
    OfficialPressFeed(
        key="bundestag_press",
        name="Bundestag",
        url="https://www.bundestag.de/static/appdata/includes/rss/pressemitteilungen.rss",
    ),
    OfficialPressFeed(
        key="bundesregierung_press",
        name="Bundesregierung",
        url="https://www.bundesregierung.de/service/rss/breg-de/1151244/feed.xml",
    ),
    OfficialPressFeed(
        key="bmas_news",
        name="Bundesministerium für Arbeit und Soziales",
        url="https://www.bmas.de/SiteGlobals/Functions/RSSFeed/DE/RSSNewsfeed/RSSNewsfeed.xml",
    ),
    OfficialPressFeed(
        key="bmg_press",
        name="Bundesministerium für Gesundheit",
        url="https://www.bundesgesundheitsministerium.de/pressemitteilungen.xml",
    ),
    OfficialPressFeed(
        key="bmf_press",
        name="Bundesministerium der Finanzen",
        url="https://www.bundesfinanzministerium.de/SiteGlobals/Functions/RSSFeed/DE/Pressemitteilungen/RSSPressemitteilungen.xml",
    ),
    OfficialPressFeed(
        key="gkv_press",
        name="GKV-Spitzenverband",
        url=(
            "https://www.gkv-spitzenverband.de/gkv_spitzenverband/presse/"
            "pressemitteilungen_und_statements/rss_pressemitteilungen.xml"
        ),
    ),
)

# BAMF, the employment agency, RKI and Deutsche Bahn do not publish a stable own RSS.
# Their releases still appear in these topic feeds; institution wording selects them.
_TOPIC_FEEDS: tuple[OfficialPressFeed, ...] = (
    OfficialPressFeed(
        key="presseportal_politik",
        name="Behörde",
        url="https://www.presseportal.de/rss/politik.rss2",
        require_institution_word=True,
    ),
    OfficialPressFeed(
        key="presseportal_soziales",
        name="Behörde",
        url="https://www.presseportal.de/rss/soziales.rss2",
        require_institution_word=True,
    ),
    OfficialPressFeed(
        key="presseportal_gesundheit",
        name="Behörde",
        url="https://www.presseportal.de/rss/gesundheit-medizin.rss2",
        require_institution_word=True,
    ),
    OfficialPressFeed(
        key="presseportal_wirtschaft",
        name="Behörde",
        url="https://www.presseportal.de/rss/wirtschaft.rss2",
        require_institution_word=True,
    ),
    OfficialPressFeed(
        key="presseportal_wohnen",
        name="Behörde",
        url="https://www.presseportal.de/rss/bau-immobilien.rss2",
        require_institution_word=True,
    ),
    OfficialPressFeed(
        key="presseportal_verkehr",
        name="Behörde",
        url="https://www.presseportal.de/rss/auto-verkehr.rss2",
        require_institution_word=True,
    ),
)

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
    *_AUTHORITY_FEEDS,
    *_TOPIC_FEEDS,
)
