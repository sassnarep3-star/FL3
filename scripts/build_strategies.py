"""Strategy engine: registry, validation gates, leaderboard, correlation, luck removal.

Design rule that governs the whole file: NO PERFORMANCE NUMBER IS EVER MADE UP.
The leaderboard is empty until real graded results are ingested. What the engine
does ship is the machinery - every strategy carries a pass/fail record for each
gate, and a strategy cannot reach the board while a gate is red.
"""
import json
import math

# ---------------------------------------------------------------- gate definitions
GATES = [
  {"id": "G1", "name": "Sample size", "rule": ">= 200 settled bets before a strategy may appear on the leaderboard.",
   "why": "Below ~200 bets a 55% hit rate and a 50% hit rate are statistically indistinguishable at 95% confidence."},
  {"id": "G2", "name": "Holdout discipline", "rule": "Parameters fixed on seasons 1..n-1, scored on an untouched season n. The holdout is used once.",
   "why": "Prevents the backtest from being the model."},
  {"id": "G3", "name": "Noise floor", "rule": "Beats a permutation/null distribution at p < 0.05 over 10,000 shuffles.",
   "why": "Separates signal from a lucky ordering of the same outcomes."},
  {"id": "G4", "name": "Closing-line value", "rule": "Positive closing-line value over the sample.",
   "why": "CLV is the least noisy evidence of genuine edge."},
  {"id": "G5", "name": "Vig survivorship", "rule": "Positive return at -110 pricing; break-even is 52.38%.",
   "why": "A strategy that only works at 0 vig does not work."},
  {"id": "G6", "name": "Stability", "rule": "Does not depend on one season, one team or one week (leave-one-out changes ROI by < 5 pts).",
   "why": "A single outlier cluster is not an edge."},
  {"id": "G7", "name": "Correlation control", "rule": "Correlated legs are priced with a correlation-adjusted joint probability, not the product of marginals.",
   "why": "Parlays that multiply marginals systematically overstate the true chance."},
  {"id": "G8", "name": "Luck removal", "rule": "Reported skill is computed after removing one-score games, garbage time and turnover-luck residuals.",
   "why": "The brief asks for selectively skill-based strategies, not winning streaks."},
]

# ---------------------------------------------------------------- strategy registry
def strat(**kw):
    kw.setdefault("gates", {g["id"]: {"status": "not-run", "evidence": None} for g in GATES})
    return kw

STRATS = [
  strat(id="STR-01", name="Shrunk offense-vs-defense line", family="single-bet", market="spread",
        thesis="Teams whose scoring rate diverges from the league mean after shrinkage have an exploitable expected margin.",
        inputs=["S01 team PF/PA", "S03 schedule"], params={"k": 4.0, "hfa": 0.0},
        status="untested", notes="The line model this repo ships (data/lines.json). No graded results exist, so every gate is not-run."),
  strat(id="STR-02", name="Rest/bye differential", family="single-bet", market="spread",
        thesis="Teams off a bye outperform their baseline in the following game.",
        inputs=["S03 schedule"], params={}, status="blocked-input",
        notes="Blocked: the repo has the Week 10 bye list but no historical rest-vs-performance data."),
  strat(id="STR-03", name="Backup-exposure fade", family="single-bet", market="spread",
        thesis="When the official report rules out a high-pedigree starter and the listed backup is a late-round or undrafted player, the team under-performs its baseline.",
        inputs=["S02 injuries", "S04 depth order", "S01 results"], params={"pedigree_weight_table": "see data/lineup_risk.json"},
        status="untested", notes="This is the brief's injury requirement turned into a testable hypothesis. 43 confirmed starter losses were logged this week; none are graded yet."),
  strat(id="STR-04", name="Offensive-line continuity", family="single-bet", market="total",
        thesis="Multiple starting linemen out depresses offensive efficiency more than the market prices.",
        inputs=["S02", "S04"], params={}, status="untested",
        notes="Week 10 has usable cases (TEN Skoronski, NO Fuaga + McCoy, BUF Brown, HOU Rutledge). Not graded."),
  strat(id="STR-05", name="Two-leg correlated parlay: same-game QB/WR", family="parlay", market="player props",
        thesis="A QB passing-yards over and his WR1 receiving-yards over are positively correlated; naive multiplication understates the joint probability.",
        inputs=["per-player game logs"], params={"rho_prior": 0.35}, status="blocked-input",
        notes="Blocked: no per-player game logs are in the repo, so rho cannot be estimated - only assumed. A parlay built on an assumed rho is not validated."),
  strat(id="STR-06", name="Three-leg team-total parlay", family="parlay", market="team totals",
        thesis="Team totals in the same game are negatively correlated through the game script; the market sometimes prices them as independent.",
        inputs=["S01", "S03"], params={}, status="untested",
        notes="Needs a same-game correlation estimate, which needs play-by-play. Not collected."),
  strat(id="STR-07", name="Player prop: RB volume vs. opponent run-defense", family="player-prop", market="rushing yards",
        thesis="Backup-forced defensive front changes (see STR-03) shift RB efficiency.",
        inputs=["S02", "S04", "per-player logs"], params={}, status="blocked-input",
        notes="Blocked on per-player logs and defensive snap data."),
  strat(id="STR-08", name="Injury-report timing drift", family="single-bet", market="spread",
        thesis="Lines move systematically when a Friday designation lands; the drift is exploitable before close.",
        inputs=["S02 snapshots", "historical odds"], params={}, status="blocked-input",
        notes="Blocked: it needs historical odds, which this environment cannot access. This is the single most valuable unblocked dependency (see Q-04)."),
]

# ---------------------------------------------------------------- correlation
# Documented priors only where defensible; otherwise the field is null and marked unverified.
CORR = [
 {"pair": "QB passing yards over  <->  his WR1 receiving yards over", "rho": None, "basis": "not estimated - requires per-player game logs (not in repo)", "status": "unverified"},
 {"pair": "Team total over  <->  opponent team total under (same game)", "rho": None, "basis": "not estimated - requires play-by-play", "status": "unverified"},
 {"pair": "Spread cover  <->  game total over (same game)", "rho": None, "basis": "not estimated - requires play-by-play", "status": "unverified"},
 {"pair": "RB rushing yards over  <->  team total over", "rho": None, "basis": "not estimated - requires per-player logs", "status": "unverified"},
 {"pair": "Two different games, same week", "rho": 0.0, "basis": "independence is the defensible default when no shared mechanism is identified", "status": "assumption"},
]

def parlay_price(legs, rho):
    """Joint probability for 2 legs given a correlation, using a Gaussian copula.

    Shown on the site so the arithmetic is auditable. Returns None if rho is None,
    because pricing a parlay on an unestimated correlation is exactly the failure
    mode the brief asks to avoid.
    """
    if rho is None or len(legs) != 2:
        return None
    p1, p2 = legs
    # bivariate normal CDF via a 64-point Gauss-Hermite style approximation
    z1, z2 = norm_ppf(p1), norm_ppf(p2)
    total = 0.0
    N = 64
    for i in range(N):
        for j in range(N):
            x = (i + 0.5) / N * 8 - 4
            y = (j + 0.5) / N * 8 - 4
            d = (x * x - 2 * rho * x * y + y * y) / (2 * (1 - rho * rho))
            pdf = math.exp(-d) / (2 * math.pi * math.sqrt(1 - rho * rho))
            total += (1 if x < z1 else 0) * (1 if y < z2 else 0) * pdf * (8 / N) * (8 / N)
    return round(total, 4)

def norm_ppf(p):
    # Acklam's rational approximation - accurate to ~1.15e-9
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    dd = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
          3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((dd[0]*q+dd[1])*q+dd[2])*q+dd[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((dd[0]*q+dd[1])*q+dd[2])*q+dd[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)

# demonstrate the correlation penalty on two 55% legs at a few rhos
DEMO = []
for rho in (0.0, 0.2, 0.4, 0.6):
    naive = 0.55 * 0.55
    joint = parlay_price((0.55, 0.55), rho)
    DEMO.append({"rho": rho, "naive_product": round(naive, 4), "copula_joint": joint,
                 "fair_decimal_naive": round(1 / naive, 3),
                 "fair_decimal_copula": round(1 / joint, 3) if joint else None,
                 "delta_pct_points": round((joint - naive) * 100, 2) if joint else None})

# ---------------------------------------------------------------- luck removal
LUCK = {
  "title": "Removing luck from the equation",
  "principle": "A strategy is only 'skill based' if its edge survives removing the outcomes that are mostly variance.",
  "procedures": [
    {"id": "L1", "name": "One-score-game exclusion", "method": "Recompute ROI excluding games decided by <= 8 points, then require the sign to hold.",
     "status": "not-run", "blocker": "needs settled bet records (none exist)"},
    {"id": "L2", "name": "Garbage-time strip", "method": "Recompute excluding plays in the final 5 minutes with a >= 17 point margin.",
     "status": "not-run", "blocker": "needs play-by-play (not collected)"},
    {"id": "L3", "name": "Turnover-luck regression", "method": "Model turnovers as a mean-reverting series and subtract the non-persistent component from team efficiency.",
     "status": "not-run", "blocker": "needs play-by-play"},
    {"id": "L4", "name": "Permutation null", "method": "Shuffle outcomes 10,000 times within strata; keep the strategy only if it clears the 95th percentile.",
     "status": "not-run", "blocker": "needs settled bet records"},
    {"id": "L5", "name": "Deflated Sharpe", "method": "Deflate the observed Sharpe ratio for the number of strategies tried (multiple-comparisons correction).",
     "status": "not-run", "blocker": "needs settled bet records"},
    {"id": "L6", "name": "Bootstrap CI", "method": "10,000-sample bootstrap of ROI; report the 5th-95th percentile band, not the point estimate.",
     "status": "not-run", "blocker": "needs settled bet records"},
  ],
  "multiple_comparisons_note": "Eight strategies are registered here. Testing all eight and reporting the best one inflates the apparent edge; L5 exists specifically to deflate for that."
}

# ---------------------------------------------------------------- leaderboard
LEADERBOARD = {
  "status": "empty-by-design",
  "why": "A leaderboard row requires settled, graded bets. Zero bets have been settled in this repo, so no strategy has a record.",
  "what_would_fill_it": [
    "A settled-bet log with strategy id, market, price taken, closing price, stake and result.",
    "At least 200 settled bets per strategy before a row is displayed (gate G1).",
    "All eight gates recorded pass/fail with linked evidence."
  ],
  "reward_scheme": {
    "design_only": True,
    "scoring": "risk-adjusted: ROI / stdev of ROI, then deflated by the number of strategies tried (L5). Raw ROI is explicitly not the ranking metric.",
    "tiers": [
      {"tier": "Provisional", "requirement": "G1..G3 pass", "reward": "listed, no capital"},
      {"tier": "Validated", "requirement": "G1..G6 pass", "reward": "eligible for the smallest unit stake"},
      {"tier": "Promoted", "requirement": "G1..G8 pass on an out-of-sample season", "reward": "scaled stake, reviewed monthly"}
    ],
    "warning": "The reward scheme is a proposal. It allocates no money and has no verified historical returns behind it."
  },
  "rows": []
}

doc = {
 "meta": {"title": "Strategy registry, validation gates, correlation and luck removal",
          "as_of": "2026-11-14",
          "core_claim": "No strategy in this repo has been validated. The registry documents what would have to be true for one to be.",
          "sources": ["S01","S02","S03","S04","S05"]},
 "gates": GATES,
 "strategies": STRATS,
 "correlation": {"pairs": CORR, "demonstration": DEMO,
                 "demonstration_note": "Two 55% legs. The naive product is 0.3025. Higher correlation raises the true joint probability of two 'over' legs, so multiplying marginals understates the parlay - which is why G7 exists."},
 "luck_removal": LUCK,
 "leaderboard": LEADERBOARD
}
json.dump(doc, open("data/strategies.json","w"), indent=1)
print("gates", len(GATES), "strategies", len(STRATS))
print("blocked strategies:", sum(1 for s in STRATS if s["status"]=="blocked-input"))
for d in DEMO:
    print("  rho=%.1f naive=%.4f copula=%s" % (d["rho"], d["naive_product"], d["copula_joint"]))
print("norm_ppf(0.55) =", round(norm_ppf(0.55), 6))
