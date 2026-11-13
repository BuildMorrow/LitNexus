"""Test suite for SJR journal ranking and lookup service."""

from app.services.sjr_service import normalize_issn, normalize_title, sjr_service


def test_normalize_issn():
    assert normalize_issn("0162-8828") == "0162-8828"
    assert normalize_issn("01628828") == "0162-8828"
    assert normalize_issn("2162237X") == "2162-237X"
    assert normalize_issn(None) is None


def test_normalize_title():
    assert (
        normalize_title("IEEE Transactions on Pattern Analysis and Machine Intelligence")
        == "IEEE TRANSACTIONS ON PATTERN ANALYSIS AND MACHINE INTELLIGENCE"
    )
    assert normalize_title("The Lancet: Digital Health!") == "THE LANCET DIGITAL HEALTH"


def test_sjr_lookup_by_issn():
    res = sjr_service.lookup(issn="0162-8828", journal_title=None)
    assert res.quartile == "Q1"
    assert res.sjr_score is not None and res.sjr_score > 4.0


def test_sjr_lookup_by_title():
    res = sjr_service.lookup(
        issn=None,
        journal_title="IEEE Transactions on Biomedical Engineering",
    )
    assert res.quartile == "Q1"
    assert res.sjr_score == 1.85


def test_sjr_lookup_unknown_fallback():
    res = sjr_service.lookup(issn="9999-9999", journal_title="Unknown Workshop on AI")
    assert res.quartile is None
    assert res.sjr_score is None
