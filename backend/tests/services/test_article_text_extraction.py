from app.services.article_text_extraction import extract_article_text_from_html


def test_extract_article_text_prefers_article_paragraphs() -> None:
    html: str = """
    <html><body>
    <nav><p>Menu noise</p></nav>
    <article>
      <p>Erster Absatz der Meldung.</p>
      <p>Zweiter Absatz mit Details.</p>
    </article>
    </body></html>
    """
    text: str = extract_article_text_from_html(html, max_chars=5000)
    assert "Erster Absatz" in text
    assert "Zweiter Absatz" in text
    assert "Menu noise" not in text


def test_extract_article_text_respects_max_chars() -> None:
    html: str = "<article><p>" + ("Wort " * 500) + "</p></article>"
    text: str = extract_article_text_from_html(html, max_chars=80)
    assert len(text) <= 81
    assert text.endswith("…")
