"""Match a publisher headline to a recent official press release."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import feedparser  # type: ignore[import-untyped]
import httpx

from app.services.official_press_feeds import OFFICIAL_PRESS_FEEDS, OfficialPressFeed
from app.services.rss_entry_normalization import normalize_feedparser_entry

logger: logging.Logger = logging.getLogger(__name__)

_TOKEN_RE: re.Pattern[str] = re.compile(r"[a-z0-9äöüß]+", re.IGNORECASE)
_MAX_RELEASES_PER_FEED: int = 40
# Longer phrases first so "bundespolizei" is not labelled as Polizei.
_INSTITUTIONS: tuple[tuple[str, str], ...] = (
    ("bundespolizei", "Bundespolizei"),
    ("polizei", "Polizei"),
    ("deutsche bahn", "Deutsche Bahn"),
    ("bundesagentur", "Bundesagentur für Arbeit"),
    ("arbeitsagentur", "Bundesagentur für Arbeit"),
    ("robert koch", "Robert Koch-Institut"),
    ("koch-institut", "Robert Koch-Institut"),
    ("gkv-spitzenverband", "GKV-Spitzenverband"),
    ("spitzenverband", "GKV-Spitzenverband"),
    ("krankenkasse", "Krankenkasse"),
    ("bundestag", "Bundestag"),
    ("bundesrat", "Bundesrat"),
    ("bundesregierung", "Bundesregierung"),
    ("bundeskanzler", "Bundesregierung"),
    ("landesregierung", "Landesregierung"),
    ("staatsanwaltschaft", "Staatsanwaltschaft"),
    ("bundesamt", "Bundesamt"),
    ("gericht", "Gericht"),
    ("ministerium", "Ministerium"),
    ("minister", "Ministerium"),
)
_STOPWORDS: frozenset[str] = frozenset(
    {
        "aber",
        "als",
        "also",
        "am",
        "an",
        "auch",
        "auf",
        "aus",
        "bei",
        "beim",
        "bis",
        "das",
        "dass",
        "dem",
        "den",
        "der",
        "des",
        "die",
        "dies",
        "diese",
        "dieser",
        "ein",
        "eine",
        "einem",
        "einen",
        "einer",
        "eines",
        "er",
        "es",
        "für",
        "hat",
        "im",
        "in",
        "ist",
        "ihr",
        "ihre",
        "mit",
        "nach",
        "nicht",
        "oder",
        "sich",
        "sie",
        "sind",
        "über",
        "und",
        "vom",
        "von",
        "vor",
        "war",
        "wird",
        "wurde",
        "wurden",
        "zu",
        "zum",
        "zur",
    }
)


@dataclass(frozen=True)
class OfficialRelease:
    title: str
    url: str
    name: str
    published_at: datetime


def distinctive_tokens(text: str) -> set[str]:
    """Return words that can identify an event, without German function words."""
    tokens: set[str] = set()
    for raw in _TOKEN_RE.findall(text.casefold()):
        if raw in _STOPWORDS:
            continue
        if len(raw) < 4 and not any(char.isdigit() for char in raw):
            continue
        tokens.add(raw)
    return tokens


def _tokens_overlap(left: str, right: str) -> bool:
    if left == right:
        return True
    shorter: str
    longer: str
    shorter, longer = (left, right) if len(left) <= len(right) else (right, left)
    return len(shorter) >= 5 and longer.startswith(shorter)


def _shared_token_count(query: set[str], release: set[str]) -> int:
    shared: int = 0
    for token in release:
        if any(_tokens_overlap(token, other) for other in query):
            shared += 1
    return shared


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def institution_label(text: str) -> str | None:
    """Return the public authority name named in the text, if one is recognised."""
    folded: str = text.casefold()
    for phrase, label in _INSTITUTIONS:
        if phrase in folded:
            return label
    return None


def _is_same_release(left: OfficialRelease, right: OfficialRelease) -> bool:
    """Whether two feed copies describe one press release, even with different URLs."""
    left_tokens: set[str] = distinctive_tokens(left.title)
    right_tokens: set[str] = distinctive_tokens(right.title)
    if not left_tokens or not right_tokens:
        return False
    shared: int = _shared_token_count(left_tokens, right_tokens)
    smaller: int = min(len(left_tokens), len(right_tokens))
    return shared / smaller >= 0.8


def find_official_release(
    title: str,
    summary: str,
    published_at: datetime,
    releases: list[OfficialRelease],
    *,
    min_shared_tokens: int,
    min_title_coverage: float,
    max_age_hours: int,
) -> OfficialRelease | None:
    """Return one clearly matching press release, or None when the match is weak or ambiguous.

    Copies of the same release from the national and a state feed count as one candidate.
    Two different events with a similar score are left unmatched.
    """
    query: set[str] = distinctive_tokens(f"{title}\n{summary}")
    if len(query) < min_shared_tokens:
        return None
    published: datetime = _as_utc(published_at)
    max_age: timedelta = timedelta(hours=max_age_hours)
    ranked: list[tuple[float, int, OfficialRelease]] = []
    for release in releases:
        if abs(_as_utc(release.published_at) - published) > max_age:
            continue
        release_tokens: set[str] = distinctive_tokens(release.title)
        if len(release_tokens) < min_shared_tokens:
            continue
        shared: int = _shared_token_count(query, release_tokens)
        if shared < min_shared_tokens:
            continue
        coverage: float = shared / len(release_tokens)
        if coverage < min_title_coverage:
            continue
        ranked.append((coverage, shared, release))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], -item[1], item[2].url))
    best_coverage, _best_shared, best = ranked[0]
    close: list[OfficialRelease] = [
        release for coverage, _shared, release in ranked if best_coverage - coverage < 0.15
    ]
    if any(not _is_same_release(best, release) for release in close):
        return None
    return best


def release_from_entry(entry: Mapping[str, Any], feed: OfficialPressFeed) -> OfficialRelease | None:
    """Map one official feed entry, dropping politics items that name no authority."""
    normalized = normalize_feedparser_entry(entry)
    if normalized is None or not normalized.url or not normalized.title:
        return None
    text: str = f"{normalized.title}\n{normalized.summary}"
    label: str | None = institution_label(text)
    public_name: str
    if feed.require_institution_word:
        if label is None:
            return None
        public_name = label
    else:
        public_name = feed.name
    return OfficialRelease(
        title=normalized.title,
        url=normalized.url,
        name=public_name,
        published_at=normalized.published_at,
    )


class OfficialPressCatalog:
    """Recent official releases fetched once per ingestion run."""

    def __init__(self) -> None:
        self._releases: list[OfficialRelease] = []

    @classmethod
    def from_releases(cls, releases: list[OfficialRelease]) -> OfficialPressCatalog:
        catalog: OfficialPressCatalog = cls()
        catalog._releases = list(releases)
        return catalog

    def load(self, client: httpx.Client) -> None:
        releases: list[OfficialRelease] = []
        seen_urls: set[str] = set()
        for feed in OFFICIAL_PRESS_FEEDS:
            try:
                response: httpx.Response = client.get(feed.url)
                response.raise_for_status()
            except httpx.HTTPError as error:
                logger.warning("Official press feed failed key=%s error=%s", feed.key, error)
                continue
            parsed: feedparser.FeedParserDict = feedparser.parse(response.content)
            for entry in list(parsed.entries[:_MAX_RELEASES_PER_FEED]):
                release: OfficialRelease | None = release_from_entry(entry, feed)
                if release is None or release.url in seen_urls:
                    continue
                seen_urls.add(release.url)
                releases.append(release)
        self._releases = releases
        logger.info("Official press catalog size=%s", len(releases))

    def match(
        self,
        title: str,
        summary: str,
        published_at: datetime,
        *,
        min_shared_tokens: int,
        min_title_coverage: float,
        max_age_hours: int,
    ) -> OfficialRelease | None:
        return find_official_release(
            title,
            summary,
            published_at,
            self._releases,
            min_shared_tokens=min_shared_tokens,
            min_title_coverage=min_title_coverage,
            max_age_hours=max_age_hours,
        )
