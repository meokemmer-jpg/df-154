from __future__ import annotations

import json
from collections import Counter
from datetime import date
from typing import Dict, Iterable, List, Mapping, Optional


_BRAND_CHANNELS = {
    "HeyLou": "Hotels",
    "9dots": "SaaS",
    "LexVance": "Legal",
}

_POSITIVE_WORDS = {
    "excellent",
    "great",
    "good",
    "love",
    "loved",
    "amazing",
    "fast",
    "helpful",
    "clean",
    "friendly",
    "smooth",
    "reliable",
    "happy",
    "pleasant",
    "recommend",
}

_NEGATIVE_WORDS = {
    "bad",
    "poor",
    "slow",
    "broken",
    "hate",
    "hated",
    "awful",
    "dirty",
    "rude",
    "buggy",
    "issue",
    "issues",
    "delay",
    "delayed",
    "terrible",
    "complaint",
}


def _normalize_text(text: str) -> List[str]:
    cleaned = []
    for ch in text.lower():
        cleaned.append(ch if ch.isalnum() else " ")
    return "".join(cleaned).split()


def sentiment_score(text: str) -> int:
    tokens = _normalize_text(text)
    pos = sum(1 for token in tokens if token in _POSITIVE_WORDS)
    neg = sum(1 for token in tokens if token in _NEGATIVE_WORDS)
    return pos - neg


def sentiment_tier(text: str) -> str:
    score = sentiment_score(text)
    if score >= 2:
        return "positive"
    if score <= -2:
        return "negative"
    return "neutral"


def aggregate_brand_mentions(
    mentions: Iterable[Mapping[str, object]],
    *,
    brands: Optional[Iterable[str]] = None,
) -> Dict[str, object]:
    allowed_brands = set(brands or _BRAND_CHANNELS.keys())

    filtered_mentions = []
    for mention in mentions:
        brand = str(mention.get("brand", "")).strip()
        if brand not in allowed_brands:
            continue

        text = str(mention.get("text", ""))
        channel = str(mention.get("channel", "unknown")).strip() or "unknown"
        tier = sentiment_tier(text)

        filtered_mentions.append(
            {
                "brand": brand,
                "channel": channel,
                "text": text,
                "sentiment_tier": tier,
            }
        )

    by_brand: Dict[str, Dict[str, object]] = {}
    total_channel_counter: Counter[str] = Counter()

    for brand in allowed_brands:
        brand_mentions = [m for m in filtered_mentions if m["brand"] == brand]
        brand_channel_counter = Counter(m["channel"] for m in brand_mentions)
        brand_sentiment_counter = Counter(m["sentiment_tier"] for m in brand_mentions)

        total_channel_counter.update(brand_channel_counter)

        by_brand[brand] = {
            "sector": _BRAND_CHANNELS.get(brand, "unknown"),
            "mention_count": len(brand_mentions),
            "sentiment_tiers": {
                "positive": brand_sentiment_counter.get("positive", 0),
                "neutral": brand_sentiment_counter.get("neutral", 0),
                "negative": brand_sentiment_counter.get("negative", 0),
            },
            "channel_distribution": dict(sorted(brand_channel_counter.items())),
            "mentions": brand_mentions,
        }

    overall_sentiment = Counter(m["sentiment_tier"] for m in filtered_mentions)

    return {
        "date": date.today().isoformat(),
        "auto_response_enabled": False,
        "brands": by_brand,
        "summary": {
            "total_mentions": len(filtered_mentions),
            "sentiment_tiers": {
                "positive": overall_sentiment.get("positive", 0),
                "neutral": overall_sentiment.get("neutral", 0),
                "negative": overall_sentiment.get("negative", 0),
            },
            "channel_distribution": dict(sorted(total_channel_counter.items())),
        },
    }


def build_report_json(
    mentions: Iterable[Mapping[str, object]],
    *,
    brands: Optional[Iterable[str]] = None,
    indent: int = 2,
) -> str:
    report = aggregate_brand_mentions(mentions, brands=brands)
    return json.dumps(report, indent=indent, sort_keys=True)
# [CRUX-MK]
