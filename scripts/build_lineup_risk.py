"""Compute the backup-deficiency index from data/depth_risk.json.

The idea: a team is more exposed when a player who is confirmed OUT by the official
NFL report has to be replaced by a player who is (a) low on the depth chart and
(b) lacking equivalent draft investment. We compute that exposure, label every
input, and refuse to guess where the source is silent.

ALL of this is descriptive. It does not claim to predict point spreads, and the
report says so on every page that shows the output.
"""
import json
from collections import defaultdict

d = json.load(open("data/depth_risk.json"))
rows = d["depth"]

# Draft-pedigree weight. Deliberately simple and published so it can be argued with.
def pedigree_weight(kind, rnd):
    if kind == "draft" and rnd:
        return {1: 1.00, 2: 0.85, 3: 0.70, 4: 0.55, 5: 0.45, 6: 0.35, 7: 0.25}.get(rnd, 0.25)
    if kind == "udfa":
        return 0.20
    if kind == "street-fa":
        return 0.25
    if kind and kind.startswith("veteran"):
        return 0.60          # proven veteran acquired by FA/trade
    return 0.30              # unknown / not captured

def depth_weight(depth):
    return {1: 1.00, 2: 0.70, 3: 0.45, 4: 0.30, 5: 0.20}.get(depth, 0.15)

for r in rows:
    r["pedigree_weight"] = pedigree_weight(r["pedigree_kind"], r["draft_round"])
    r["depth_weight"] = depth_weight(r["depth"])

out = defaultdict(list)
for r in rows:
    out[r["team"]].append(r)

TEAM_NAME = {t["team"]: t["name"] for t in json.load(open("data/standings_verified.json"))["meta"]["teams"]}

findings = []
for team, rs in out.items():
    # who is officially OUT or DOUBTFUL and is the listed starter at his position
    losses = []
    for r in rs:
        if r["official_game_status"] in ("Out", "Doubtful") and r["depth"] == 1:
            # the replacement is the next man up at that position on the chart
            repl = [x for x in rs if x["position"] == r["position"] and x["depth"] == 2]
            repl = repl[0] if repl else None
            gap = None
            if repl:
                gap = round(r["pedigree_weight"] * r["depth_weight"]
                            - repl["pedigree_weight"] * repl["depth_weight"], 3)
            losses.append({
                "position": r["position"],
                "starter": r["player"],
                "starter_code": r["depth_code"],
                "starter_draft_round": r["draft_round"],
                "status": r["official_game_status"],
                "injury": r["official_injury"],
                "replacement": repl["player"] if repl else None,
                "replacement_code": repl["depth_code"] if repl else None,
                "replacement_draft_round": repl["draft_round"] if repl else None,
                "replacement_also_on_report": bool(repl and repl["on_official_report"] and repl["official_game_status"]) if repl else None,
                "replacement_status": repl["official_game_status"] if repl else None,
                "pedigree_gap": gap,
                "replacement_unverified": (repl is None),
            })
    assessed = [l for l in losses if l["pedigree_gap"] is not None]
    total = round(sum(max(0.0, l["pedigree_gap"]) for l in assessed), 3)
    worst = sorted(assessed, key=lambda l: -l["pedigree_gap"])[:3]
    depth_of_issue = [l for l in assessed if (l["replacement_draft_round"] or 8) >= 5
                      or l["replacement_code"] in (None, "")]
    findings.append({
        "team": team, "team_name": TEAM_NAME.get(team, team),
        "confirmed_starter_losses": len(losses),
        "assessable_losses": len(assessed),
        "ungraded_losses": len(losses) - len(assessed),
        "replacement_risk_index": total,
        "worst_gaps": worst,
        "losses": losses,
        "src_availability": "S02", "src_depth": "S04",
    })

findings.sort(key=lambda x: -x["replacement_risk_index"])

doc = {
 "meta": {
   "title": "Backup-deficiency index - 2026 Week 10",
   "as_of": "2026-11-14",
   "what_this_is": "A descriptive exposure score: how much proven depth a team loses, per its own depth chart, when the official NFL report rules a starter Out or Doubtful.",
   "what_this_is_not": "It is not a point-spread model, not a projection and not betting advice. It ranks exposure, nothing more.",
   "formula": {
     "pedigree_weight": "draft round 1=1.00 2=0.85 3=0.70 4=0.55 5=0.45 6=0.35 7=0.25; UDFA=0.20; street FA=0.25; proven veteran FA/trade=0.60; unknown=0.30",
     "depth_weight": "depth 1=1.00 2=0.70 3=0.45 4=0.30 5=0.20",
     "gap": "starter(pedigree_weight x depth_weight) - replacement(pedigree_weight x depth_weight)",
     "index": "sum of positive gaps across a team's confirmed starter losses"
   },
   "known_weaknesses": [
     "Draft pedigree is a proxy for ability, not a measurement of it. A 7th-round starter who has played well scores badly here.",
     "The model cannot see snap counts, target share, pressure rate or any per-play data - none is in the repo.",
     "Losses where the backup is himself unverified on the official report are counted in confirmed_starter_losses but excluded from the index (ungraded_losses).",
     "A team with zero confirmed starter losses scores 0.0 - that means 'nothing published', not 'fully healthy'."
   ],
   "sources": ["S02", "S04", "S05"]
 },
 "teams": findings,
 "league_note": "Teams absent from this table had no starter carrying an Out or Doubtful designation at capture time on the positions transcribed. That is an absence of evidence, not evidence of health."
}
json.dump(doc, open("data/lineup_risk.json", "w"), indent=1)
print("teams scored", len(findings))
for f in findings[:10]:
    print("  %-4s %-24s losses=%d index=%.2f ungraded=%d" % (f["team"], f["team_name"], f["confirmed_starter_losses"], f["replacement_risk_index"], f["ungraded_losses"]))
print("total confirmed starter losses:", sum(f["confirmed_starter_losses"] for f in findings))
