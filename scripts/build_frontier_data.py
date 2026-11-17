#!/usr/bin/env python3
"""
FL3 — build the canonical results feed, the availability graph and the
mechanical cross-checks that everything else depends on.

Reads (all committed, official-sourced):
  data/week_results_2026.csv         148 transcribed games
  data/official/results_feed.json    the one-game correction + exclusions
  data/official/game_books_week10.json  official Game Book availability
  data/depth_risk.json               Ourlads depth order (third-party, declared) for Week 10
  data/injuries_week10.json          official report (availability only)

Writes:
  data/official/results_feed.csv            149 rows, one per final game
  data/official/club_reconciliation.csv     32 rows, corpus vs official standings
  data/availability/availability_graph.csv  expected-vs-actual, one row per club/game
  data/availability/replacement_depth.csv   depth of the replacement, not just presence
  data/availability/injury_surprise.csv     designation surprise vs the played reality

Rules enforced here (and re-asserted by scripts/check_frontier.py):
  * a game without an official final score is never in the feed
  * a club's aggregate must equal the official standings exactly, or the build fails
  * a replacement is only "confirmed" when the Game Book shows the depth-1 player
    genuinely did not play and the depth-2+ player is in the lineup
  * every availability row names the official document it came from
"""
from __future__ import annotations

import csv
import json
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def load(path):
    with open(os.path.join(DATA, path), encoding="utf-8") as fh:
        return json.load(fh)


def write_csv(relpath, header, rows):
    path = os.path.join(DATA, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {relpath}: {len(rows)} rows")
    return len(rows)


# ---------------------------------------------------------------------------
# 1. results feed
# ---------------------------------------------------------------------------
OFFICIAL_STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"

# Read from https://www.nfl.com/standings/league/2026/REG on 2026-11-17T02:47Z.
# W, L, T, PF, PA for all 32 clubs, in the order the page renders them.
OFFICIAL = {
    "BUF": (8, 1, 0, 287, 199), "SF": (8, 1, 0, 281, 196), "CHI": (7, 2, 0, 241, 184),
    "CIN": (7, 2, 0, 278, 193), "DEN": (7, 2, 0, 198, 186), "DET": (7, 2, 0, 257, 199),
    "JAX": (7, 2, 0, 269, 144), "KC": (7, 2, 0, 237, 156), "MIN": (7, 2, 0, 176, 126),
    "PIT": (6, 3, 0, 198, 182), "NYG": (5, 3, 1, 203, 196), "CLE": (6, 4, 0, 188, 220),
    "GB": (6, 4, 0, 226, 221), "LA": (6, 4, 0, 248, 187), "SEA": (6, 4, 0, 223, 175),
    "NE": (5, 5, 0, 221, 242), "BAL": (4, 5, 0, 189, 236), "CAR": (4, 5, 0, 219, 236),
    "DAL": (4, 6, 0, 286, 282), "LV": (4, 6, 0, 251, 289), "WAS": (3, 5, 1, 196, 223),
    "HOU": (3, 6, 0, 233, 219), "NO": (3, 6, 0, 202, 236), "TB": (3, 6, 0, 202, 178),
    "AZ": (3, 7, 0, 184, 289), "ATL": (3, 7, 0, 201, 258), "IND": (3, 7, 0, 208, 271),
    "PHI": (2, 7, 0, 148, 221), "NYJ": (2, 8, 0, 194, 254), "MIA": (1, 8, 0, 148, 224),
    "TEN": (1, 8, 0, 167, 239), "LAC": (0, 8, 0, 121, 219),
}


def build_results_feed():
    with open(os.path.join(DATA, "week_results_2026.csv"), newline="", encoding="utf-8") as fh:
        corpus = list(csv.DictReader(fh))
    decl = load("official/results_feed.json")

    feed = []
    for r in corpus:
        feed.append({
            "game_id": f"REG{r['week']}-{r['away_abbr']}-{r['home_abbr']}",
            "week": int(r["week"]),
            "date": r["game_date"],
            "away": r["away_abbr"], "away_pts": int(r["away_pts"]),
            "home": r["home_abbr"], "home_pts": int(r["home_pts"]),
            "neutral_note": r["neutral_site_note"],
            "source_url": r["source_url"],
            "status": "FINAL_VERIFIED",
            "origin": "corpus_148",
        })

    # the one correction, taken from the declaration file (which cites the official page)
    corr = decl["reconciliation"]["correction"]
    feed.append({
        "game_id": corr["game_id"], "week": 10, "date": corr["date"],
        "away": corr["away"], "away_pts": corr["away_pts"],
        "home": corr["home"], "home_pts": corr["home_pts"],
        "neutral_note": "", "source_url": corr["source_url"],
        "status": "FINAL_VERIFIED", "origin": "correction_2026-11-17",
    })

    # settlement key: the identity a forecast must resolve against
    for g in feed:
        g["settlement_key"] = f"{g['away']}@{g['home']}@{g['date']}"
        g["margin_home"] = g["home_pts"] - g["away_pts"]
        g["total_points"] = g["home_pts"] + g["away_pts"]
        g["winner"] = ("HOME" if g["margin_home"] > 0 else
                       "AWAY" if g["margin_home"] < 0 else "TIE")

    header = ["game_id", "week", "date", "away", "away_pts", "home", "home_pts",
              "margin_home", "total_points", "winner", "neutral_note",
              "settlement_key", "status", "origin", "source_url"]
    feed.sort(key=lambda g: (g["week"], g["date"], g["game_id"]))
    write_csv("official/results_feed.csv", header,
              [[g[h] for h in header] for g in feed])

    # ---------------------------------------------------------------- check
    agg = defaultdict(lambda: dict(g=0, w=0, l=0, t=0, pf=0, pa=0))
    for g in feed:
        for tm, pts, opp in ((g["away"], g["away_pts"], g["home_pts"]),
                             (g["home"], g["home_pts"], g["away_pts"])):
            s = agg[tm]
            s["g"] += 1
            s["pf"] += pts
            s["pa"] += opp
            if pts > opp:
                s["w"] += 1
            elif pts < opp:
                s["l"] += 1
            else:
                s["t"] += 1
    rows, bad = [], []
    for tm, (w, l, t, pf, pa) in sorted(OFFICIAL.items()):
        s = agg[tm]
        ok = (s["w"], s["l"], s["t"], s["pf"], s["pa"]) == (w, l, t, pf, pa)
        if not ok:
            bad.append(tm)
        rows.append([tm, s["g"], s["w"], w, s["l"], l, s["t"], t, s["pf"], pf,
                     s["pa"], pa, "MATCH" if ok else "MISMATCH",
                     OFFICIAL_STANDINGS_URL])
    write_csv("official/club_reconciliation.csv",
              ["club", "corpus_games", "corpus_w", "official_w", "corpus_l", "official_l",
               "corpus_t", "official_t", "corpus_pf", "official_pf", "corpus_pa",
               "official_pa", "verdict", "source_url"], rows)
    if bad:
        raise SystemExit(f"FATAL: results feed does not reconcile to official standings: {bad}")
    if len(feed) != decl["reconciliation"]["result_after_correction"]["games"]:
        raise SystemExit("FATAL: feed game count differs from the declaration")
    print(f"results feed reconciles: {len(feed)} games, 32/32 clubs exact")
    return feed


# ---------------------------------------------------------------------------
# 2. availability graph  (expected = depth-1 from the declared order source;
#    actual = Game Book lineup / did-not-play / not-active)
# ---------------------------------------------------------------------------
ORD = {"QB": "QB", "RB": "RB", "WR": "WR", "TE": "TE", "T": "T", "G": "G", "C": "C",
       "DT": "DT", "DE": "DE", "LB": "LB", "CB": "CB", "S": "S", "FB": "FB",
       "LS": "LS", "P": "P"}


POS_TOKENS = r"^(3QB|ILB|OLB|NT|DL|DB|EDGE|DE|DT|LB|CB|SS|FS|S|QB|RB|FB|WR/RS|WR|TE|OT|LT|RT|LG|RG|C/G|G/T|T/G|OL|C|G|T|K|P|LS)\s+"
SUFFIX = re.compile(r"\s+(jr\.?|sr\.?|ii|iii|iv|v)$", re.I)


def name_key(raw: str):
    """Return (initial, surname) for both 'Drake London' and 'WR 5 D.London'.

    Game Books print 'D.London'; depth charts print 'Drake London'. Both reduce
    to ('d', 'london'). Suffixes (Jr./Sr./III) are dropped. A two-token surname
    ('St. Brown') is joined, so 'A.St. Brown' -> ('a', 'stbrown').
    """
    s = re.sub(POS_TOKENS, "", raw.strip(), flags=re.I)
    s = re.sub(r"^OL\s*B\s+", "", s)
    s = re.sub(r"^\d+\s*", "", s)                      # jersey number
    s = re.sub(r"[^A-Za-z.\- ]", "", s).strip()
    s = SUFFIX.sub("", s)
    if "." in s:                                        # D.London / T.J. Hockenson
        head, _, tail = s.partition(".")
        tail = tail.replace(".", "").replace(" ", "")
        return (head[:1].lower() if head else "", tail.lower())
    parts = [p for p in re.split(r"[\s\-]+", s) if p]
    if not parts:
        return ("", "")
    if len(parts) == 1:
        return ("", parts[0].lower())
    # surname keeps its hyphen so both spellings reduce identically
    surname = "".join(parts[1:]).lower()
    return (parts[0][:1].lower(), surname)


ALIASES = {
    # 'name as printed in the Game Book' -> 'name as printed on the depth chart'
    "t|jhockenson": "t|hockenson",
    "t|ingramdawkins": "t|ingram-dawkins",
    "a|alshaair": "a|al-shaair",
}


def nkey(raw: str) -> str:
    i, sn = name_key(raw)
    k = f"{i}|{sn}"
    return ALIASES.get(k, k)


def build_availability(feed):
    gb = load("official/game_books_week10.json")
    depth = load("depth_risk.json")["depth"]
    injuries = load("injuries_week10.json")

    # The official report prints full names; the depth chart prints the same
    # names. The join is therefore on (initial, surname). Where one club lists
    # two players with the same initial and surname the join is ambiguous and
    # the row is marked rather than guessed.
    report = {}
    surname_index = defaultdict(list)
    for g in injuries["games"]:
        for t in g["teams"]:
            for p in t["players"]:
                k = nkey(p["name"])
                report[(t["abbr"], k)] = p
                surname_index[(t["abbr"], k.split("|")[1])].append(p)

    # depth-1 expectations, grouped: a club may publish several rank-1 players
    # at one position (readiness R041/R075). The group size is published so a
    # reader can see that "the starter" is not a single named player.
    exp = defaultdict(list)
    for d in depth:
        if d["depth"] == 1:
            exp[(d["team"], d["position"])].append(d)
    group_size = {k: len(v) for k, v in exp.items()}

    book = {}
    for g in gb["games"]:
        if g["status"] != "CAPTURED":
            continue
        for tm, blocks in g["teams"].items():
            book[tm] = (g, blocks)

    rows = []
    for tm in sorted(book):
        game, blocks = book[tm]
        opp = game["home"] if tm == game["away"] else game["away"]
        off = {nkey(x) for x in blocks.get("starters_offense", [])}
        dfn = {nkey(x) for x in blocks.get("starters_defense", [])}
        starters = off | dfn
        dnp = {nkey(x) for x in blocks.get("did_not_play", [])}
        inactive = {nkey(x) for x in blocks.get("not_active", [])}
        # The Game Book has four blocks. This capture transcribes three of them
        # (Lineups, Did Not Play, Not Active) plus a partial Substitutions list.
        # Text extraction interleaves the two clubs' substitution tables and
        # sometimes drops them, so ABSENCE FROM THE TRANSCRIBED BLOCKS PROVES
        # NOTHING. A player who is in none of them is reported as
        # NOT_LISTED_IN_TRANSCRIBED_BLOCKS and is never described as having
        # played. Only the presence of a name in a block is evidence.
        block_complete = bool(off) and bool(dfn)

        for (team, position), entries in sorted(exp.items()):
            if team != tm:
                continue
            for d in entries:
                d1 = nkey(d["player"])
                r = report.get((tm, d1))
                join_basis = "initial+surname"
                if r is None:
                    cands = surname_index.get((tm, d1.split("|")[1]), [])
                    if d1.split("|")[0] == "" or len({c["name"] for c in cands}) == 1:
                        r = cands[0] if cands else None
                        join_basis = "surname only" if r else "not on report"
                r = r or {}
                join_basis = "initial+surname" if (tm, d1) in report else (
                    "surname only" if r else "not on report")
                gs = (r.get("game_status") or "").strip()
                practice = (r.get("practice") or "").strip()

                if d1 in inactive:
                    actual, basis = "NOT_ACTIVE", "GAME_BOOK_NOT_ACTIVE"
                elif d1 in dnp:
                    actual, basis = "DID_NOT_PLAY", "GAME_BOOK_DID_NOT_PLAY"
                elif d1 in starters:
                    actual, basis = "STARTED", "GAME_BOOK_LINEUP"
                elif block_complete:
                    actual, basis = "NOT_LISTED_IN_TRANSCRIBED_BLOCKS", "NAME_ABSENT_FROM_3_OF_4_BLOCKS"
                else:
                    actual, basis = "UNRESOLVED_BLOCK_INCOMPLETE", "GAME_BOOK_STARTER_BLOCK_MISSING"

                # ---- replacement depth -------------------------------------
                pool = sorted([x for x in depth if x["team"] == tm
                               and x["position"] == d["position"] and x["depth"] > d["depth"]],
                              key=lambda x: x["depth"])
                repl = repl_depth = repl_state = ""
                if actual in ("NOT_ACTIVE", "DID_NOT_PLAY"):
                    for cand in pool:
                        cn = nkey(cand["player"])
                        if cn in inactive or cn in dnp:
                            continue
                        repl, repl_depth = cand["player"], cand["depth"]
                        repl_state = ("CONFIRMED_STARTER" if cn in starters else
                                      "LISTED_NEXT_BUT_NOT_STARTING")
                        break
                    if not repl:
                        repl_state = "NO_DEEPER_PLAYER_LISTED"

                rows.append([tm, game["game_id"], opp, position, d["player"], d["depth"],
                             group_size[(tm, position)],
                             actual, basis, gs, practice,
                             repl, repl_depth, repl_state,
                             join_basis, d["src_depth"],
                             game["gamebook_pdf"], game["game_url"]])

    header = ["club", "game_id", "opponent", "position", "depth1_player", "depth_rank",
              "slot_group_size", "actual_state", "evidence_basis", "official_game_status",
              "official_practice", "replacement", "replacement_depth", "replacement_state",
              "report_join_basis", "depth_source", "gamebook_pdf", "game_url"]
    write_csv("availability/availability_graph.csv", header, rows)

    # ---------------------------------------------------------- club summary
    clubs = defaultdict(lambda: defaultdict(int))
    for r in rows:
        clubs[r[0]][r[7]] += 1
    summary = []
    for tm in sorted(clubs):
        c = clubs[tm]
        summary.append([tm, sum(c.values()), c.get("STARTED", 0),
                        c.get("NOT_ACTIVE", 0),
                        c.get("DID_NOT_PLAY", 0),
                        c.get("NOT_LISTED_IN_TRANSCRIBED_BLOCKS", 0),
                        c.get("UNRESOLVED_BLOCK_INCOMPLETE", 0),
                        sum(1 for r in rows if r[0] == tm and r[13] == "CONFIRMED_STARTER"),
                        sum(1 for r in rows if r[0] == tm and r[13] == "LISTED_NEXT_BUT_NOT_STARTING"),
                        sum(1 for r in rows if r[0] == tm and r[13] == "NO_DEEPER_PLAYER_LISTED")])
    write_csv("availability/club_availability_summary.csv",
              ["club", "depth1_slots", "started", "not_active",
               "did_not_play", "not_listed", "unresolved", "replacement_confirmed",
               "replacement_listed_not_starting", "no_deeper_player_listed"], summary)
    return rows


def build_replacement_depth(avail_rows):
    """Aggregate the replacement depth distribution (how far down the chart)."""
    from collections import Counter
    dist = Counter(r[12] for r in avail_rows if r[12] != "")
    rows = [[d, dist[d]] for d in sorted(dist, key=lambda x: int(x))]
    write_csv("availability/replacement_depth_distribution.csv",
              ["replacement_depth", "slots"], rows)
    return rows


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None, None)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def build_injury_surprise(avail_rows):
    """Level vs surprise, and the empirical play rate of each designation.

    Level   = the official game-status designation (what the report said).
    Surprise= whether the player actually started or sat, which the level alone
    does not tell you. Only Game Book evidence decides the outcome.
    """
    rows = []
    for r in avail_rows:
        tm, gid, player, pos, actual, gs, practice, gb = (
            r[0], r[1], r[4], r[3], r[7], r[9], r[10], r[16])
        started = actual == "STARTED"
        sat = actual in ("NOT_ACTIVE", "DID_NOT_PLAY")
        played = started          # only a starting-lineup sighting is evidence
        if actual.startswith("UNRESOLVED") or actual == "NOT_LISTED_IN_TRANSCRIBED_BLOCKS":
            cls = "UNRESOLVED"
        elif gs == "Out" and sat:
            cls = "AS_DECLARED_OUT_SAT"
        elif gs == "Out" and played:
            cls = "DECLARED_OUT_BUT_PLAYED"
        elif gs == "Doubtful" and sat:
            cls = "DECLARED_DOUBTFUL_SAT"
        elif gs == "Doubtful" and played:
            cls = "DECLARED_DOUBTFUL_PLAYED"
        elif gs == "Questionable" and sat:
            cls = "DECLARED_QUESTIONABLE_SAT"
        elif gs == "Questionable" and played:
            cls = "DECLARED_QUESTIONABLE_PLAYED"
        elif not gs and played:
            cls = "NO_DESIGNATION_PLAYED"
        elif not gs and sat:
            cls = "NO_DESIGNATION_SAT"
        else:
            cls = "OTHER"
        rows.append([tm, gid, player, pos, gs, practice, actual,
                     "STARTED" if started else ("SAT" if sat else "NOT_OBSERVED"),
                     cls, gb])
    write_csv("availability/injury_surprise.csv",
              ["club", "game_id", "player", "position", "official_game_status",
               "official_practice", "actual_state", "outcome", "surprise_class",
               "gamebook_pdf"], rows)

    cal = []
    for label in ["Out", "Doubtful", "Questionable", ""]:
        sub = [r for r in rows if r[4] == label and r[7] in ("STARTED", "SAT")]
        n = len(sub)
        played = sum(1 for r in sub if r[7] == "STARTED")
        started = played
        unobserved = sum(1 for r in rows if r[4] == label and r[7] == "NOT_OBSERVED")
        p, lo, hi = wilson(played, n)
        ps, los, his = wilson(started, n)
        cal.append([label or "(blank)", n, played, started,
                    "" if p is None else round(p, 3),
                    "" if lo is None else round(lo, 3),
                    "" if hi is None else round(hi, 3),
                    "" if ps is None else round(ps, 3),
                    "" if los is None else round(los, 3),
                    "" if his is None else round(his, 3),
                    unobserved])
    write_csv("availability/designation_empirical.csv",
              ["designation", "n_observed", "n_started", "n_started_again",
               "start_rate", "start_rate_lo95", "start_rate_hi95",
               "same_col", "same_lo", "same_hi", "n_not_observed"], cal)
    from collections import Counter
    print("surprise classes:", dict(Counter(r[8] for r in rows)))
    return rows


def main():
    feed = build_results_feed()
    avail = build_availability(feed)
    build_replacement_depth(avail)
    build_injury_surprise(avail)


if __name__ == "__main__":
    main()
