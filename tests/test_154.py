import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

m154 = importlib.import_module("154")
aggregate_brand_mentions = m154.aggregate_brand_mentions
build_report_json = m154.build_report_json
sentiment_tier = m154.sentiment_tier


def test_aggregate_brand_mentions_core_flow():
    mentions = [
        {
            "brand": "HeyLou",
            "channel": "google_reviews",
            "text": "Clean hotel, friendly staff, excellent stay, great service.",
        },
        {
            "brand": "HeyLou",
            "channel": "x",
            "text": "Dirty room, rude staff, awful check-in, terrible delay.",
        },
        {
            "brand": "9dots",
            "channel": "linkedin",
            "text": "Reliable platform, fast onboarding, helpful support, good product.",
        },
        {
            "brand": "LexVance",
            "channel": "reddit",
            "text": "The service exists and the response time was okay.",
        },
        {
            "brand": "UnknownBrand",
            "channel": "forum",
            "text": "Should be ignored completely.",
        },
    ]

    report = aggregate_brand_mentions(mentions)

    assert report["auto_response_enabled"] is False
    assert report["summary"]["total_mentions"] == 4

    assert sentiment_tier("excellent great helpful") == "positive"
    assert sentiment_tier("awful terrible rude broken") == "negative"
    assert sentiment_tier("ordinary statement without signal") == "neutral"

    heylou = report["brands"]["HeyLou"]
    assert heylou["sector"] == "Hotels"
    assert heylou["mention_count"] == 2
    assert heylou["sentiment_tiers"] == {"positive": 1, "neutral": 0, "negative": 1}
    assert heylou["channel_distribution"] == {"google_reviews": 1, "x": 1}

    nine_dots = report["brands"]["9dots"]
    assert nine_dots["sector"] == "SaaS"
    assert nine_dots["mention_count"] == 1
    assert nine_dots["sentiment_tiers"]["positive"] == 1

    lexvance = report["brands"]["LexVance"]
    assert lexvance["sector"] == "Legal"
    assert lexvance["mention_count"] == 1
    assert lexvance["sentiment_tiers"] == {"positive": 0, "neutral": 1, "negative": 0}

    assert report["summary"]["sentiment_tiers"] == {"positive": 2, "neutral": 1, "negative": 1}
    assert report["summary"]["channel_distribution"] == {
        "google_reviews": 1,
        "linkedin": 1,
        "reddit": 1,
        "x": 1,
    }

    report_json = build_report_json(mentions)
    assert '"auto_response_enabled": false' in report_json
    assert '"total_mentions": 4' in report_json
