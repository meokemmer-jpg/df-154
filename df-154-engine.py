
# K16: Concurrent-Spawn-Mutex (fcntl-based, Trinity-CONSERVATIVE 2026-05-17)
def k16_lock_or_exit(df_name: str):
    """Acquire exclusive lock or exit(3). Prevents concurrent DF runs."""
    import fcntl, os, sys
    lock_path = f"/tmp/df-trinity-{df_name}.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_WRONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except BlockingIOError:
        sys.exit(3)


# K13: External-Anchor-Mock-RFC3161 (Trinity-CONSERVATIVE 2026-05-17)
def k13_anchor(payload_hash: str) -> dict:
    """Mock RFC3161-style timestamp anchor."""
    from datetime import datetime, timezone
    return {
        "anchor_type": "rfc3161-mock",
        "iso_ts": datetime.now(timezone.utc).isoformat(),
        "payload_hash": payload_hash,
    }


# K12: HMAC-SHA256-Provenance (Trinity-CONSERVATIVE 2026-05-17)
def k12_provenance(payload: bytes, key: bytes = b"df-trinity-conservative-v1") -> dict:
    """Returns payload_hash + HMAC-SHA256 signature."""
    import hashlib, hmac
    return {
        "payload_hash": hashlib.sha256(payload).hexdigest(),
        "hmac_sha256": hmac.new(key, payload, hashlib.sha256).hexdigest(),
    }

"""PVG brand mention cross aggregator engine for DF-154."""

import re
import os
import json
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime, timezone


DF_DIR = Path(__file__).parent
LOCK_DIR = Path("/tmp/df-154.lock")
DF_ID = "154"
DECISION_KEYWORDS_REGEX = re.compile(
    r"\b(entscheid[a-z]*|empfehl(?:e|en|t|st)|sollt(?:e|en|est)|recommend[a-z]*|decid[a-z]*|advis[a-z]*|propos[a-z]*)\b",
    re.IGNORECASE,
)


@dataclass
class TrackerOutput:
    welle: str = "25"
    df: str = "DF-154"
    iso_timestamp: str = ""
    source: str = "mock"
    mentions_total: int = 0
    mentions_per_brand: dict = field(default_factory=dict)
    sentiment_per_brand: dict = field(default_factory=dict)
    top_channels: list = field(default_factory=list)
    viral_events: list = field(default_factory=list)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _file_stable(path, min_age_sec=300) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    try:
        return (time.time() - p.stat().st_mtime) >= min_age_sec
    except OSError:
        return False


def acquire_lock_with_identity() -> bool:
    stale_after_sec = 6 * 60 * 60

    try:
        LOCK_DIR.mkdir(mode=0o700)
    except FileExistsError:
        try:
            age = time.time() - LOCK_DIR.stat().st_mtime
            if age > stale_after_sec:
                for child in LOCK_DIR.iterdir():
                    if child.is_file() or child.is_symlink():
                        child.unlink(missing_ok=True)
                LOCK_DIR.rmdir()
                LOCK_DIR.mkdir(mode=0o700)
            else:
                return False
        except OSError:
            return False

    identity = {
        "df_id": DF_ID,
        "pid": os.getpid(),
        "created_at": iso_now(),
        "cwd": os.getcwd(),
    }
    try:
        (LOCK_DIR / "identity.json").write_text(
            json.dumps(identity, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        release_lock()
        return False

    return True


def release_lock() -> None:
    try:
        if LOCK_DIR.exists():
            for child in LOCK_DIR.iterdir():
                if child.is_file() or child.is_symlink():
                    child.unlink(missing_ok=True)
            LOCK_DIR.rmdir()
    except OSError:
        pass


def k17_pre_action_verification(anchors) -> dict:
    missing = []
    for anchor in anchors or []:
        if not anchor:
            continue
        path = Path(str(anchor))
        env_name = str(anchor)
        if env_name in os.environ:
            continue
        if path.exists():
            continue
        missing.append(str(anchor))

    return {
        "ok": not missing,
        "missing_anchors": missing,
        "env_tag": os.environ.get("DF_154_ENV_TAG", "local"),
    }


def _is_real_api_enabled() -> bool:
    return os.environ.get("DF_154_REAL_API_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


def scan_output_for_decision_keywords(text) -> list:
    if text is None:
        return []
    found = DECISION_KEYWORDS_REGEX.findall(str(text))
    unique = []
    seen = set()
    for item in found:
        normalized = item.lower()
        if normalized not in seen:
            seen.add(normalized)
            unique.append(item)
    return unique


def assert_no_decision_keywords(output) -> None:
    hits = scan_output_for_decision_keywords(output)
    if hits:
        raise ValueError("Q_0/K_0 blocked terms found: " + ", ".join(hits))


def _load_json_env(name, default):
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return default
    return value if isinstance(value, type(default)) else default


def collect_tracker_output() -> TrackerOutput:
    output = TrackerOutput(iso_timestamp=iso_now())

    if _is_real_api_enabled():
        output.source = "real"
        output.mentions_total = int(os.environ.get("DF_154_MENTIONS_TOTAL", "0") or 0)
        output.mentions_per_brand = _load_json_env("DF_154_MENTIONS_PER_BRAND", {})
        output.sentiment_per_brand = _load_json_env("DF_154_SENTIMENT_PER_BRAND", {})
        output.top_channels = _load_json_env("DF_154_TOP_CHANNELS", [])
        output.viral_events = _load_json_env("DF_154_VIRAL_EVENTS", [])
        return output

    output.source = "mock"
    output.mentions_per_brand = {
        "Atlas": 42,
        "Northstar": 31,
        "Helio": 18,
    }
    output.sentiment_per_brand = {
        "Atlas": {"positive": 24, "neutral": 14, "negative": 4},
        "Northstar": {"positive": 16, "neutral": 11, "negative": 4},
        "Helio": {"positive": 7, "neutral": 9, "negative": 2},
    }
    output.top_channels = ["search", "social", "news", "forums"]
    output.viral_events = [
        {"brand": "Atlas", "channel": "social", "mentions": 19, "tag": "launch-spike"},
        {"brand": "Northstar", "channel": "news", "mentions": 12, "tag": "press-cycle"},
    ]
    output.mentions_total = sum(int(v) for v in output.mentions_per_brand.values())
    return output


def main() -> int:
    if not acquire_lock_with_identity():
        return 3

    try:
        anchors_raw = os.environ.get("DF_154_K17_ANCHORS", "")
        anchors = [item.strip() for item in anchors_raw.split(",") if item.strip()]
        pav = k17_pre_action_verification(anchors)
        if not pav.get("ok"):
            return 3

        output = collect_tracker_output()
        payload = asdict(output)
        payload["k17_pre_action_verification"] = pav

        report_text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        assert_no_decision_keywords(report_text)

        report_dir = DF_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        date_tag = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        report_path = report_dir / f"df-154-{date_tag}.json"
        report_path.write_text(report_text + "\n", encoding="utf-8")
        return 0
    except Exception as exc:
        sys.stderr.write(str(exc) + "\n")
        return 3
    finally:
        release_lock()


if __name__ == "__main__":
    sys.exit(main())