from app.services.news_attribution import public_source_fields
from app.services.primary_source import PrimarySourceLink, extract_primary_source
from app.services.publisher_editorial import publisher_editorial_instructions
from app.services.rss_entry_normalization import NormalizedFeedEntry, normalize_feedparser_entry


def test_extracts_official_link_and_ignores_publisher_and_media() -> None:
    html: str = (
        '<p>Siehe <a href="https://www.zeit.de/politik/2026">ZEIT</a> und '
        '<a href="https://polizei.nrw.de/presse/messerangriff">Polizei NRW</a> '
        'sowie <a href="https://www.spiegel.de/panorama/x">SPIEGEL</a>.</p>'
    )

    found: PrimarySourceLink | None = extract_primary_source(html, "https://www.zeit.de/politik/2026")

    assert found is not None
    assert found.url == "https://polizei.nrw.de/presse/messerangriff"
    assert found.name == "Polizei NRW"


def test_single_non_media_link_is_kept() -> None:
    html: str = '<p>Dokument: <a href="https://example.org/statement.pdf">Erklärung</a></p>'

    found: PrimarySourceLink | None = extract_primary_source(html, "https://www.welt.de/article")

    assert found is not None
    assert found.url == "https://example.org/statement.pdf"
    assert found.name == "Erklärung"


def test_ambiguous_external_links_are_not_guessed() -> None:
    html: str = (
        '<a href="https://example.org/a">A</a> <a href="https://example.com/b">B</a>'
    )

    assert extract_primary_source(html, "https://www.bild.de/x") is None


def test_social_and_same_site_links_are_ignored() -> None:
    html: str = (
        '<a href="https://www.welt.de/a">Artikel</a> '
        '<a href="https://twitter.com/welt/status/1">Tweet</a>'
    )

    assert extract_primary_source(html, "https://www.welt.de/a") is None


def test_normalize_feed_entry_stores_primary_source() -> None:
    normalized: NormalizedFeedEntry | None = normalize_feedparser_entry(
        {
            "id": "urn:1",
            "title": "Messerangriff",
            "link": "https://www.zeit.de/politik/1",
            "summary": '<p>Die <a href="https://polizei.berlin.de/pressemitteilung">Polizei Berlin</a> teilte mit.</p>',
            "published": "Thu, 24 Apr 2026 12:00:00 GMT",
        }
    )

    assert normalized is not None
    assert normalized.primary_source_url == "https://polizei.berlin.de/pressemitteilung"
    assert normalized.primary_source_name == "Polizei Berlin"
    assert "href" not in normalized.summary


def test_licensed_publisher_is_cited_as_itself() -> None:
    name: str
    url: str
    name, url = public_source_fields(
        source_key="bild",
        publisher_name="BILD",
        publisher_url="https://www.bild.de/article",
        primary_source_url="https://polizei.berlin.de/pressemitteilung",
        primary_source_name="Polizei Berlin",
        rights_verified=True,
        licence="Written permission",
        licence_url="https://www.bild.de/permission",
    )

    assert name == "BILD"
    assert url == "https://www.bild.de/article"


def test_public_source_keeps_official_publisher() -> None:
    name: str
    url: str
    name, url = public_source_fields(
        source_key="destatis",
        publisher_name="Statistisches Bundesamt (Destatis)",
        publisher_url="https://www.destatis.de/example",
        primary_source_url=None,
        primary_source_name=None,
    )

    assert name == "Statistisches Bundesamt (Destatis)"
    assert url == "https://www.destatis.de/example"


def test_public_source_uses_primary_link_for_publisher() -> None:
    name: str
    url: str
    name, url = public_source_fields(
        source_key="die_zeit",
        publisher_name="Die Zeit",
        publisher_url="https://www.zeit.de/politik/1",
        primary_source_url="https://www.cdu.de/aktuelles/statement",
        primary_source_name="CDU",
    )

    assert name == "CDU"
    assert url == "https://www.cdu.de/aktuelles/statement"


def test_original_article_stays_linked_when_primary_source_is_missing() -> None:
    name: str
    url: str
    name, url = public_source_fields(
        source_key="welt",
        publisher_name="WELT",
        publisher_url="https://www.welt.de/article",
        primary_source_url=None,
        primary_source_name=None,
    )

    assert name == ""
    assert url == "https://www.welt.de/article"


def test_editorial_prompt_follows_primary_source() -> None:
    text: str = publisher_editorial_instructions(
        "die_zeit",
        sensitive=False,
        primary_source_name="Polizei Berlin",
        primary_source_url="https://polizei.berlin.de/pressemitteilung",
    )

    assert "Polizei Berlin" in text
    assert "короткую собственную новость" in text
    assert "не сокращённый перевод или пересказ другого СМИ" in text
    assert "Не называй ZEIT" in text


def test_editorial_prompt_hides_source_when_primary_link_is_missing() -> None:
    text: str = publisher_editorial_instructions("bild", sensitive=False)

    assert "Не пиши «по данным»" in text
    assert "по данным BILD" not in text
