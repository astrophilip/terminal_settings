#!/usr/bin/env python3
"""Estimate Claude Code spend (session, month to date, year to date) from local transcripts.

Run in the background by statusline-command.sh with the current session's
transcript path. Writes <config>/cost-cache/<session-id>.json and a matching .sh
fragment (COST_SESSION, COST_MTD, COST_YTD) that the status line sources.

<config> is $CLAUDE_CONFIG_DIR, or ~/.claude. Prices come from pricing.json next
to this script, or from the file named by $CLAUDE_COST_PRICING.

This is an estimate at API list prices, not a bill: a claude.ai subscription is
not charged these amounts, and totals run somewhat low because some auxiliary
Claude Code requests record no usage in the transcript.
"""
import datetime as dt, glob, json, os, sys

CONFIG_DIR = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
PROJECTS_DIR = os.path.join(CONFIG_DIR, "projects")
CACHE_DIR = os.path.join(CONFIG_DIR, "cost-cache")
PRICING_FILE = os.environ.get("CLAUDE_COST_PRICING") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "pricing.json")
CACHE_KEEP_DAYS = 7
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
    """Yield (local_date, usd) for each unique API response in one transcript."""
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
            yield day, usd


def main():
    current = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else None
    try:
        pricing, models = load_pricing(PRICING_FILE)
    except (OSError, ValueError, KeyError) as e:
        sys.exit(f"cost-refresh: cannot load pricing from {PRICING_FILE}: {e}")

    today = dt.date.today()
    session = mtd = ytd = 0.0
    unpriced = set()
    # Subagent transcripts sit under <project>/<session-id>/subagents/, so search
    # recursively, and count a session's subagents toward that session.
    current_subdir = os.path.splitext(current)[0] + os.sep if current else None
    for f in glob.glob(os.path.join(PROJECTS_DIR, "**", "*.jsonl"), recursive=True):
        f = os.path.abspath(f)
        is_current = current is not None and (f == current or f.startswith(current_subdir))
        for day, usd in call_costs(f, pricing, models, unpriced):
            if is_current:
                session += usd
            if day is None:
                continue
            if day.year == today.year:
                ytd += usd
                if day.month == today.month:
                    mtd += usd

    cache, sh_cache = cache_paths(current)
    payload = {"session": round(session, 4), "mtd": round(mtd, 4),
               "ytd": round(ytd, 4),
               "updated": dt.datetime.now().isoformat(timespec="seconds"),
               "transcript": current, "unpriced_models": sorted(unpriced)}
    for path, text in ((cache, json.dumps(payload)), (sh_cache, (
            f'COST_SESSION={payload["session"]:.2f}\n'
            f'COST_MTD={payload["mtd"]:.2f}\n'
            f'COST_YTD={payload["ytd"]:.2f}\n'))):
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            fh.write(text)
        os.replace(tmp, path)   # atomic; readers never see a partial file
    prune()


if __name__ == "__main__":
    main()
