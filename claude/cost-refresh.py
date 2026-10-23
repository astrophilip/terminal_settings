#!/usr/bin/env python3
"""Estimate Claude Code spend (this session, and the trailing 30 days) from local transcripts.

Run in the background by statusline-command.sh with the current session's
transcript path. Writes <config>/cost-cache/<session-id>.json and a matching .sh
fragment (COST_SESSION, COST_30D) that the status line sources.

<config> is $CLAUDE_CONFIG_DIR, or ~/.claude. Prices come from pricing.json next
to this script, or from the file named by $CLAUDE_COST_PRICING.

Transcripts are never re-read while unchanged: <config>/cost-cache/files.json
keeps each transcript's priced responses, keyed by its size and mtime, so a
refresh only parses the files that grew since the last one.

This is an estimate at API list prices, not a bill: a claude.ai subscription is
not charged these amounts, and totals run somewhat low because some auxiliary
Claude Code requests record no usage in the transcript.
"""
import datetime as dt, glob, hashlib, json, os, sys, time

CONFIG_DIR = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
PROJECTS_DIR = os.path.join(CONFIG_DIR, "projects")
CACHE_DIR = os.path.join(CONFIG_DIR, "cost-cache")
FILE_CACHE = os.path.join(CACHE_DIR, "files.json")
FILE_CACHE_VERSION = 1   # bump when call_costs() changes how it prices a response
PRICING_FILE = os.environ.get("CLAUDE_COST_PRICING") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "pricing.json")
CACHE_KEEP_DAYS = 7
WINDOW_DAYS = 30   # today and the 29 local calendar days before it
M = 1_000_000


def load_pricing(path):
    """Return the pricing dict and its models as (prefix, rates), longest prefix first."""
    with open(path) as fh:
        pricing = json.load(fh)
    models = sorted(pricing["models"].items(), key=lambda kv: -len(kv[0]))
    return pricing, models


def rates_for(model, models):
    """Match a model ID to its rates by prefix, so dated IDs find their base entry."""
    for prefix, rates in models:
        if model == prefix or model.startswith(prefix + "-"):
            return rates
    return None


def cache_paths(transcript):
    """Per-session cache files. Two concurrent sessions must not clobber each
    other's `session` figure, so the session id keys the filename."""
    sid = os.path.splitext(os.path.basename(transcript or ""))[0] or "unknown"
    os.makedirs(CACHE_DIR, exist_ok=True)
    return (os.path.join(CACHE_DIR, sid + ".json"),
            os.path.join(CACHE_DIR, sid + ".sh"))


def prune():
    """Drop cache files for sessions not seen recently."""
    cutoff = dt.datetime.now().timestamp() - CACHE_KEEP_DAYS * 86400
    try:
        for fn in os.listdir(CACHE_DIR):
            fp = os.path.join(CACHE_DIR, fn)
            if os.path.isfile(fp) and os.path.getmtime(fp) < cutoff:
                os.remove(fp)
    except OSError:
        pass


def call_costs(path, pricing, models, unpriced):
    """Yield (message_id, local_date, usd) for each unique API response in one transcript."""
    seen = set()
    try:
        fh = open(path, "r", errors="replace")
    except OSError:
        return
    with fh:
        for line in fh:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = d.get("message") or {}
            u = msg.get("usage")
            if not u:
                continue
            # One API response is written as one transcript line per content
            # block, each carrying a copy of the same usage object. Dedupe by
            # message id or a multi-block response is counted several times.
            mid = msg.get("id") or d.get("requestId")
            if not mid or mid in seen:
                continue
            seen.add(mid)
            model = msg.get("model") or ""
            rates = rates_for(model, models)
            if rates is None:
                if model and not model.startswith("<"):   # skip "<synthetic>" entries
                    unpriced.add(model)
                continue

            inp = rates["input"]
            cc = u.get("cache_creation") or {}
            write_5m = cc.get("ephemeral_5m_input_tokens")
            write_1h = cc.get("ephemeral_1h_input_tokens")
            if write_5m is None and write_1h is None:
                # Older transcripts lack the TTL split; Claude Code writes 1h caches.
                write_5m, write_1h = 0, u.get("cache_creation_input_tokens") or 0
            usd = (
                (u.get("input_tokens") or 0) * inp
                + (write_5m or 0) * inp * pricing["cache_write_5m"]
                + (write_1h or 0) * inp * pricing["cache_write_1h"]
                + (u.get("cache_read_input_tokens") or 0) * inp
                  * rates.get("cache_read", pricing["cache_read"])
                + (u.get("output_tokens") or 0) * rates["output"]
            ) / M
            # Haiku 5.5 bills a whole request at a higher tier once its prompt
            # (input, cache reads and cache writes together) passes a threshold.
            long_prompt = rates.get("long_prompt")
            if long_prompt:
                prompt = ((u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
                          + (write_5m or 0) + (write_1h or 0))
                if prompt > long_prompt["over"]:
                    usd *= long_prompt["multiplier"]
            if u.get("speed") == "fast":
                usd *= rates.get("fast", 1.0)
            if u.get("inference_geo") == "us":
                usd *= pricing.get("us_inference", 1.0)
            searches = (u.get("server_tool_use") or {}).get("web_search_requests") or 0
            usd += searches / 1000 * pricing.get("web_search_per_1k", 0.0)

            ts = d.get("timestamp") or ""
            try:  # stored UTC; bucket by the local calendar date
                day = (dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                       .astimezone().date())
            except ValueError:
                day = None
            yield mid, day, usd


def load_file_cache(stamp):
    """Per-transcript results from earlier runs, or {} if they were priced
    differently (pricing.json, this script's pricing logic, or the time zone changed)."""
    try:
        with open(FILE_CACHE) as fh:
            data = json.load(fh)
        if data["stamp"] == stamp:
            return data["files"]
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return {}


def file_calls(path, cache, pricing, models):
    """Return [[message_id, "YYYY-MM-DD" or None, usd], ...] and the unpriced
    models for one transcript, re-reading it only if its size or mtime changed."""
    try:
        st = os.stat(path)
    except OSError:
        return [], []
    key = [st.st_size, st.st_mtime_ns]
    hit = cache.get(path)
    if hit and hit["key"] == key:
        return hit["calls"], hit["unpriced"]
    unpriced = set()
    calls = [[mid, day.isoformat() if day else None, usd]
             for mid, day, usd in call_costs(path, pricing, models, unpriced)]
    cache[path] = {"key": key, "calls": calls, "unpriced": sorted(unpriced)}
    return calls, cache[path]["unpriced"]


def write_atomic(path, text):
    tmp = f"{path}.{os.getpid()}.tmp"   # sessions share files.json; don't share a tmp name
    with open(tmp, "w") as fh:
        fh.write(text)
    os.replace(tmp, path)   # atomic; readers never see a partial file


def main():
    current = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else None
    try:
        pricing, models = load_pricing(PRICING_FILE)
    except (OSError, ValueError, KeyError) as e:
        sys.exit(f"cost-refresh: cannot load pricing from {PRICING_FILE}: {e}")

    cache, sh_cache = cache_paths(current)
    stamp = [FILE_CACHE_VERSION, list(time.tzname),
             hashlib.sha256(json.dumps(pricing, sort_keys=True).encode()).hexdigest()]
    file_cache = load_file_cache(stamp)

    since = (dt.date.today() - dt.timedelta(days=WINDOW_DAYS - 1)).isoformat()
    session = window = 0.0
    unpriced = set()
    # Subagent transcripts sit under <project>/<session-id>/subagents/, so search
    # recursively, and count a session's subagents toward that session.
    current_subdir = os.path.splitext(current)[0] + os.sep if current else None
    def is_current(f):
        return current is not None and (f == current or f.startswith(current_subdir))
    # A forked or resumed session copies earlier responses, message ids and all,
    # into a new file. Dedupe across files, oldest file first, so copied
    # responses stay with the session that paid for them.
    def created(f):
        try:
            st = os.stat(f)
        except OSError:
            return 0
        return getattr(st, "st_birthtime", st.st_mtime)   # no birthtime on Linux
    files = sorted({os.path.abspath(f) for f in glob.glob(
        os.path.join(PROJECTS_DIR, "**", "*.jsonl"), recursive=True)}, key=created)
    seen = set()
    for f in files:
        calls, file_unpriced = file_calls(f, file_cache, pricing, models)
        unpriced.update(file_unpriced)
        f_is_current = is_current(f)
        for mid, day, usd in calls:
            if mid in seen:
                continue
            seen.add(mid)
            if f_is_current:
                session += usd
            if day is not None and day >= since:   # ISO dates compare as strings
                window += usd

    # Keep only transcripts that still exist.
    write_atomic(FILE_CACHE, json.dumps(
        {"stamp": stamp, "files": {f: file_cache[f] for f in files if f in file_cache}}))
    payload = {"session": round(session, 4), "last_30d": round(window, 4),
               "updated": dt.datetime.now().isoformat(timespec="seconds"),
               "transcript": current, "unpriced_models": sorted(unpriced)}
    write_atomic(cache, json.dumps(payload))
    write_atomic(sh_cache, f'COST_SESSION={payload["session"]:.2f}\n'
                           f'COST_30D={payload["last_30d"]:.2f}\n')
    prune()


if __name__ == "__main__":
    main()
