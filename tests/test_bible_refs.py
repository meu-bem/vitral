"""Referências bíblicas: leitura, formato brasileiro, versificação e salmos."""

from pathlib import Path

import pytest

from vitral.bible import Ref, default_versification, parse_ref

ROOT = str(Path(__file__).resolve().parents[1])


@pytest.mark.parametrize("text, style, expected", [
    ("ISA|63:16b-17,19b;64:2b-7", "ta", "Is 63,16b-17.19b;64,2b-7"),
    ("MAL|1:14b-2:1-2,8-10", "ta", "Ml 1,14b-2,2.8-10"),
    ("1CH|29:10b.11ab.11cd-12a.12b-d", "ta", "1Cr 29,10b.11ab.11cd-12a.12b-d"),
    ("Psalm 16:1-2a and 5, 7-8", "en", "Sl 15(16),1-2a.5.7-8"),
    ("Cf. John 4:42, 15", "en", "cf. Jo 4,42.15"),
    ("Psalm 18 (19)", "en", "Sl 18(19)"),
    ("Acts 15:41-16:5, 16:22b", "en", "At 15,41-16,5.22b"),
    ("PHM|7-20", "ta", "Fm 7-20"),
])
def test_parse_and_render(text, style, expected):
    assert parse_ref(text, style).br() == expected


@pytest.mark.parametrize("ref", [
    "Sl 79(80),2ac.3b.15-16.18-19", "Gn 1,1-2,2", "Sl 115(116B),10-11.15-16", "Sl 146(147A),1-2",
    "Sl 147(147B),12-13.14-15.19-20", "Sl 113A(114),1-2", "Sl 9A(9),2-3", "Sl 1,1-2.3.4.6", "Sl 150,1-2",
    "Sl 41(42),2.4abc;Sl 42(43),3.4", "Fm 7-20", "Ap 11,19a;12,1-6a.10ab",
])
def test_brazilian_format_round_trip(ref):
    assert parse_ref(ref, "br").br() == ref


def test_psalm_numbering_matches_directory_forms():
    # Convenção brasileira: numeração grega com a hebraica entre parênteses; salmos divididos com A/B.
    assert parse_ref("PSA|51:3", "ta").br().startswith("Sl 50(51)")
    assert parse_ref("PSA|116:12", "ta").br().startswith("Sl 115(116B)")
    assert parse_ref("PSA|116:1", "ta").br().startswith("Sl 114(116A)")
    assert parse_ref("PSA|147:12", "ta").br().startswith("Sl 147(147B)")
    assert parse_ref("PSA|147:1", "ta").br().startswith("Sl 146(147A)")
    assert parse_ref("PSA|114:1", "ta").br().startswith("Sl 113A(114)")


def test_english_to_hebrew_versification():
    vrs = default_versification(ROOT)
    assert vrs.to_org(parse_ref("PSA|19:7-10", "ta")).br() == "Sl 18(19),8-11"
    assert vrs.to_org(parse_ref("MAL|4:1-2a", "ta")).br() == "Ml 3,19-20a"
    assert vrs.to_org(parse_ref("JOL|2:28-32", "ta")).br() == "Jl 3,1-5"
    assert vrs.to_org(parse_ref("MAT|5:1-12", "ta")).br() == "Mt 5,1-12"


def test_whole_verse_comparison():
    mv = default_versification(ROOT).max_verses
    a, b = parse_ref("Sl 94(95),1-2.6-7a.7b-9", "br"), parse_ref("Sl 94(95),1-2.6-7.8-9", "br")
    assert a.normalized(mv) != b.normalized(mv)
    assert a.verses(mv) == b.verses(mv)
    assert Ref.from_verses("PSA", a.verses(mv), mv).br() == "Sl 94(95),1-2.6-9"
    cross = parse_ref("Gn 1,30-2,2", "br").verses(mv)
    assert (1, 31) in cross and (2, 1) in cross


def test_versification_neighbour_inference_and_greek_parts():
    from vitral.bible import greek_daniel_to_catholic
    vrs = default_versification(ROOT)
    assert vrs.to_org(parse_ref("ISA|63:16b-17;64:1,3b-8", "ta")).br() == "Is 63,16b-17.19;64,2b-7"
    assert vrs.to_org(parse_ref("PSA|13:5,6", "ta")).br() == "Sl 12(13),6"
    assert vrs.to_org(parse_ref("DAN|3:14-20,24-25,28", "ta")).br() == "Dn 3,14-20.91-92.95"
    assert greek_daniel_to_catholic(parse_ref("DAN|1:29-33", "ta"), vrs).br() == "Dn 3,52-56"
    assert greek_daniel_to_catholic(parse_ref("DAN|2:41c-62", "ta"), vrs).br() == "Dn 13,41-62"
    assert parse_ref("EST|4:17k-m,r-t", "ta").br() == "Est 4,17k-m.17r-t"
