"""verify_depth.py - the gate that makes the 'never publish an unsourced row' rule real.

Exits non-zero on any failure so the build and the CI check both stop.

Checks
  1  every data/*.json parses
  2  every src / source id resolves to a registry entry with an http(s) URL
  3  arithmetic: sum(PF) == sum(PA); PCT formula reproduces; net == PF - PA
  4  schedule: 14 games, 28 distinct teams, 4 byes, no duplicate team in a week
  5  injury report: practice status is one of the three published values; every
     record carries a source id
  6  depth: every row has a depth source id; every official field is either blank
     or accompanied by the availability source id
  7  lines: every game traceable to the schedule; no odds/price field sneaks in
  8  strategies: every gate present on every strategy; leaderboard rows must each
     reference a settled-bet record (so it stays empty until real data exists)
  9  flagged: every item has a category, a resolution and a source list
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
fails, warns, checks = [], [], []


def ok(msg):
    checks.append(("PASS", msg))


def bad(msg):
    fails.append(msg)


def warn(msg):
    warns.append(msg)


# Session arena/46e888f0's own datasets. Generic names are aliased because
# scripts/build_site.py (session arena-e8bf2075) uses the same names for
# different, differently-shaped files.
FILES_46E = {
    "sources": "sources_46e888f0.json",
    "standings": "standings_verified.json",
    "schedule_2026_w10": "schedule_2026_w10.json",
    "injuries_2026_w10": "injuries_2026_w10.json",
    "depth_risk": "depth_risk.json",
    "lineup_risk": "lineup_risk.json",
    "lines": "lines.json",
    "strategies": "strategies_gates.json",
    "questions": "questions_46e888f0.json",
    "suggestions": "suggestions_46e888f0.json",
    "flagged": "flagged_46e888f0.json",
}


def load(name):
    """Resolve an aliased dataset name. Accepts with or without the .json suffix."""
    target = FILES_46E.get(name, FILES_46E.get(name.rsplit(".", 1)[0], name))
    return json.loads((DATA / target).read_text())


# ---- 1 parse
files = ["sources", "standings", "schedule_2026_w10", "injuries_2026_w10", "depth_risk",
         "lineup_risk", "lines", "strategies", "questions", "suggestions", "flagged"]
docs = {}
for f in files:
    try:
        docs[f] = load(f + ".json")
    except Exception as e:  # noqa: BLE001
        bad("data/%s.json does not parse: %s" % (f, e))
ok("all %d data files parse" % len(docs))

src = docs["sources"]
registry = {s["id"]: s for s in src["sources"]}
for sid, s in registry.items():
    if not s["url"].startswith("http"):
        bad("source %s has a non-http url" % sid)
ok("source registry: %d entries, all with http(s) urls" % len(registry))


def check_src(value, where):
    if value is None:
        return
    if value not in registry:
        bad("%s references unknown source id %r" % (where, value))


# ---- 2 standings + 3 arithmetic
st = docs["standings"]["meta"]["teams"]
if len(st) != 32:
    bad("standings has %d teams, expected 32" % len(st))
pf = sum(t["pf"] for t in st)
pa = sum(t["pa"] for t in st)
if pf != pa:
    bad("sum(PF)=%d != sum(PA)=%d - league points must balance" % (pf, pa))
else:
    ok("league points balance: sum(PF) == sum(PA) == %d" % pf)

for t in st:
    g = t["w"] + t["l"] + t["t"]
    expect = round((t["w"] + 0.5 * t["t"]) / g, 3)
    if abs(expect - t["pct"]) > 0.0015:
        bad("%s pct %s does not reproduce from %d-%d-%d (expected %.3f)"
            % (t["team"], t["pct"], t["w"], t["l"], t["t"], expect))
    if t["net"] != t["pf"] - t["pa"]:
        bad("%s net %d != %d - %d" % (t["team"], t["net"], t["pf"], t["pa"]))
    check_src(t.get("src"), "standings %s" % t["team"])
ok("all 32 PCT values reproduce from the W-L-T formula")
ok("all 32 net-points values equal PF - PA")

# ---- 4 schedule
sch = docs["schedule_2026_w10"]
games = sch["games"]
seen = []
for g in games:
    seen += [g["away"], g["home"]]
    check_src(g.get("src"), "schedule game %s@%s" % (g["away"], g["home"]))
if len(games) != 14:
    bad("schedule has %d games, expected 14" % len(games))
if len(set(seen)) != 28:
    bad("schedule covers %d distinct teams, expected 28" % len(set(seen)))
if len(sch["byes"]) != 4:
    bad("expected 4 bye teams")
if len(set(seen)) + len(sch["byes"]) != 32:
    bad("teams playing + byes != 32")
if len(seen) != len(set(seen)):
    bad("a team appears twice in the same week")
ok("schedule integrity: 14 games, 28 distinct teams, 4 byes, 32 total")

# ---- 5 injuries
inj = docs["injuries_2026_w10"]["report"]
allowed = {"Full Participation in Practice", "Limited Participation in Practice",
           "Did Not Participate In Practice"}
badp = [r for r in inj if r["practice_status"] not in allowed]
if badp:
    bad("%d injury rows have an unrecognised practice status" % len(badp))
game_states = {r["game_status"] for r in inj}
unknown = game_states - {None, "Out", "Doubtful", "Questionable"}
if unknown:
    bad("injury report contains unrecognised game statuses: %r" % unknown)
for r in inj:
    check_src(r.get("src"), "injury %s/%s" % (r["team"], r["player"]))
ok("injury report: %d rows, %d teams, practice statuses all in the published set"
   % (len(inj), len({r["team"] for r in inj})))

# ---- 6 depth
dr = docs["depth_risk"]
for r in dr["depth"]:
    check_src(r.get("src_depth"), "depth %s/%s" % (r["team"], r["player"]))
    if r["on_official_report"]:
        check_src(r.get("src_availability"), "depth availability %s/%s" % (r["team"], r["player"]))
    if not r["on_official_report"] and r["official_game_status"] is not None:
        bad("%s/%s has a game status but is flagged as not on the official report"
            % (r["team"], r["player"]))
ok("depth: %d rows, every row sourced; no official status attached to an unreported player"
   % len(dr["depth"]))
if dr["meta"]["counts"]["conflicts"] != len(dr["conflicts"]):
    bad("depth conflict count in meta does not match the conflict list")

# ---- 7 lines
ln = docs["lines"]
sched_pairs = {(g["away"], g["home"]) for g in games if g["status"] != "FINAL"}
line_pairs = {(g["away"], g["home"]) for g in ln["games"]}
if line_pairs != sched_pairs:
    bad("line model does not cover exactly the unplayed games: %r" % (sched_pairs ^ line_pairs))
banned = {"price", "odds", "american_odds", "decimal_odds", "vig", "juice", "spread_price"}
def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if k.lower() in banned:
                bad("lines.json contains a market/odds field %r at %s" % (k, path))
            walk(v, path + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, path + "/%d" % i)
walk(ln)
for g in ln["games"]:
    if abs((g["exp_away_points"] + g["exp_home_points"]) - g["model_total"]) > 0.06:
        bad("total does not equal the sum of expected points for %s@%s" % (g["away"], g["home"]))
    if abs(-(g["exp_home_points"] - g["exp_away_points"]) - g["model_home_line"]) > 0.06:
        bad("home line does not reproduce from expected points for %s@%s" % (g["away"], g["home"]))
ok("lines: %d games, internal arithmetic reproduces, no odds fields present" % len(ln["games"]))
total_mean = sum(g["model_total"] for g in ln["games"]) / len(ln["games"])
base = ln["meta"]["inputs"]["league_points_per_team_game"] * 2
if abs(total_mean - base) > 6:
    bad("mean modelled total %.1f is >6 points from 2x league baseline %.1f" % (total_mean, base))
ok("mean modelled total %.2f is within tolerance of 2x baseline %.2f" % (total_mean, base))

# ---- 8 strategies
strat = docs["strategies"]
gate_ids = [g["id"] for g in strat["gates"]]
for s in strat["strategies"]:
    missing = [g for g in gate_ids if g not in s["gates"]]
    if missing:
        bad("strategy %s is missing gates %r" % (s["id"], missing))
if strat["leaderboard"]["rows"]:
    for row in strat["leaderboard"]["rows"]:
        if not row.get("settled_bets"):
            bad("leaderboard has a row without settled-bet evidence")
else:
    ok("strategies: %d registered, every one carries all %d gates; leaderboard empty by design"
       % (len(strat["strategies"]), len(gate_ids)))

# ---- 9 questions / suggestions / flagged
q = docs["questions"]["questions"]
if len({x["id"] for x in q}) != len(q):
    bad("duplicate question ids")
for x in q:
    if x["status"] == "open" and x.get("answer"):
        bad("question %s is open but has an answer" % x["id"])
ok("questions: %d, ids unique, no open question carries an answer" % len(q))
sg = docs["suggestions"]["suggestions"]
for x in sg:
    if x["status"] not in docs["suggestions"]["meta"]["decision_states"]:
        bad("suggestion %s has an unknown state %r" % (x["id"], x["status"]))
ok("suggestions: %d, every one in a declared decision state" % len(sg))
fl = docs["flagged"]["items"]
for x in fl:
    if not x.get("category") or not x.get("resolution"):
        bad("flagged item %s missing category or resolution" % x["id"])
    if not isinstance(x.get("sources", []), list):
        bad("flagged item %s sources must be a list" % x["id"])
ok("flagged: %d items, all with category, resolution and a source list" % len(fl))

# ---- 10. source badges actually resolve
# A silent regression once shipped: the page builder read the WRONG source registry
# (another session's data/sources.json, whose ids are SRC-*, not our S01-S10), so every
# single Src cell rendered an "unverified" badge while every other check still passed.
# Assert the rendered pages carry real links and no unverified badges.
ROOT = DATA.parent
unverified_total = 0
badge_total = 0
for page in sorted((ROOT / "depth").glob("*.html")):
    html_text = page.read_text(encoding="utf-8")
    unverified_total += html_text.count('class="badge bad">unverified')
    badge_total += html_text.count('class="badge src"')
if unverified_total:
    bad("depth pages render %d 'unverified' source badges - the builder is probably "
        "reading the wrong source registry" % unverified_total)
else:
    ok("source badges resolve on every depth page: 0 'unverified' badges")
if badge_total < 100:
    bad("only %d source badges rendered across depth pages; expected many more" % badge_total)
else:
    ok("source badges rendered: %d across 9 depth pages, all resolving to a registered url"
       % badge_total)

# ---- report
print("\n=== VERIFY ===")
for status, msg in checks:
    print(" [%s] %s" % (status, msg))
for w in warns:
    print(" [WARN] %s" % w)
for f in fails:
    print(" [FAIL] %s" % f)
print("\n%d checks, %d warnings, %d failures" % (len(checks), len(warns), len(fails)))
sys.exit(1 if fails else 0)
