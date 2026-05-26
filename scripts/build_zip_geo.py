#!/usr/bin/env python3
import argparse
import csv
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass

KEN_ALL_COLS = [
    "code1", "old_zip5", "zip7",
    "kana_pref", "kana_city", "kana_town",
    "pref", "city", "town",
    "flag1", "flag2", "flag3", "flag4", "flag5", "flag6",
]

LATEST_RENAME = {
    "都道府県名": "pref",
    "市区町村名": "city",
    "大字町丁目名": "town",
    "大字町丁目名カナ": "kana_town",
    "緯度": "lat",
    "経度": "lon",
}

KANJI_DIGITS = "〇一二三四五六七八九"


@dataclass
class MatchResult:
    score: int
    match_type: str


def normalize_text(s: str) -> str:
    if s is None:
        return ""
    t = unicodedata.normalize("NFKC", str(s))
    t = t.replace("　", "").replace(" ", "")
    t = t.replace("ヶ", "ケ").replace("ヵ", "カ")
    t = t.replace("之", "ノ")
    t = re.sub(r"（.*?）", "", t)
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"[ー\-‐‑‒–—―]", "", t)
    return t.strip()


def maybe_expand_town(town: str) -> list[str]:
    n = normalize_text(town)
    m = re.match(r"^(.*?)(\d+)[〜~](\d+)丁目$", n)
    if not m:
        return [n]

    base, start, end = m.group(1), int(m.group(2)), int(m.group(3))
    if start > end or end - start > 200:
        return [n]

    out = []
    for i in range(start, end + 1):
        if i < 10:
            num = KANJI_DIGITS[i]
        elif i == 10:
            num = "十"
        elif i < 20:
            num = f"十{KANJI_DIGITS[i % 10]}"
        else:
            tens = i // 10
            ones = i % 10
            if tens < len(KANJI_DIGITS):
                num = f"{KANJI_DIGITS[tens]}十{KANJI_DIGITS[ones] if ones else ''}"
            else:
                num = str(i)
        out.append(f"{base}{num}丁目")
        out.append(f"{base}{i}丁目")
    return out


def score_match(town: str, kana_town: str, cand_town: str, cand_kana: str) -> MatchResult:
    town_candidates = maybe_expand_town(town)
    ct = normalize_text(cand_town)
    k = normalize_text(kana_town)
    ck = normalize_text(cand_kana)

    if any(t and t == ct for t in town_candidates):
        return MatchResult(100, "town_exact")
    if any(t and (ct.startswith(t) or t.startswith(ct)) for t in town_candidates):
        return MatchResult(80, "town_prefix")
    if k and ck and k == ck:
        return MatchResult(70, "kana_exact")
    if k and ck and (k in ck or ck in k):
        return MatchResult(50, "kana_partial")
    return MatchResult(0, "unmatched")


def load_ken_all(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for raw in reader:
            padded = (raw + [""] * len(KEN_ALL_COLS))[:len(KEN_ALL_COLS)]
            row = dict(zip(KEN_ALL_COLS, padded))
            zip7 = row.get("zip7", "")
            if not re.fullmatch(r"\d{7}", zip7):
                continue
            if row.get("town", "") == "以下に掲載がない場合":
                continue
            rows.append({
                "zip7": zip7,
                "pref": row.get("pref", ""),
                "city": row.get("city", ""),
                "town": row.get("town", ""),
                "kana_town": row.get("kana_town", ""),
            })
    return rows


def load_latest(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = {LATEST_RENAME.get(k, k): (v or "") for k, v in raw.items()}
            lat, lon = row.get("lat", ""), row.get("lon", "")
            if not str(lat).strip() or not str(lon).strip():
                continue
            rows.append({
                "pref": row.get("pref", ""),
                "city": row.get("city", ""),
                "town": row.get("town", ""),
                "kana_town": row.get("kana_town", ""),
                "lat": lat,
                "lon": lon,
            })
    return rows


def build(ken_rows: list[dict], latest_rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in latest_rows:
        grouped[(row["pref"], row["city"])].append(row)

    out = []
    for row in ken_rows:
        cands = grouped.get((row["pref"], row["city"]), [])
        if not cands:
            continue

        best = None
        best_result = MatchResult(-1, "unmatched")
        for c in cands:
            m = score_match(row["town"], row["kana_town"], c["town"], c["kana_town"])
            if m.score > best_result.score:
                best_result = m
                best = c

        if best and best_result.score > 0:
            try:
                lat = float(best["lat"])
                lon = float(best["lon"])
            except ValueError:
                continue
            out.append({
                "zip7": row["zip7"],
                "pref": row["pref"],
                "city": row["city"],
                "town": row["town"],
                "lat": lat,
                "lon": lon,
                "score": best_result.score,
                "match_type": best_result.match_type,
            })

    dedup = {r["zip7"]: r for r in out}
    return sorted(dedup.values(), key=lambda x: x["zip7"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ken-all", required=True)
    parser.add_argument("--latest", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    ken_rows = load_ken_all(args.ken_all)
    latest_rows = load_latest(args.latest)
    result = build(ken_rows, latest_rows)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"written: {args.out} ({len(result)} records)")


if __name__ == "__main__":
    main()
