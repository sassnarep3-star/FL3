#!/usr/bin/env python3
"""
FL3 — NFL line origination & analytics engine, v0.1
===================================================
Deterministic, reproducible model. Every factual input below was transcribed
from an official source on 2026-11-14 (see research/sources.md). Model
parameters (weights, HFA) are DESIGN CHOICES, clearly marked, not verified facts.

Outputs (data/):
  2026-standings.csv            verified standings + per-game rates (each row links NFL.com)
  2026-week10-games.csv         Week 10 slate (verified, NFL.com)
  2026-week11-games.csv         Week 11 slate (verified, NFL.com)
  2026-week10-injuries.csv      official Week 10 game-status report, every row
  2026-week10-depth-deficiencies.csv  depth-tier deficiency tracker
  2026-week10-lines.csv         market reference + own originated lines + edges
  correlation-matrix.csv        correlations computed from verified standings
Stdlib only. Run: python3 models/originate_lines.py
"""
import csv
import math
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
W10_REPORT_URL = "https://www.nfl.com/news/nfl-week-10-injury-report-2026-season"
W10_SCHED_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
W11_SCHED_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"
ROUNDUP_URL = ("https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-"
               "from-wednesday-nov-11")

# ---------------------------------------------------------------------------
# DESIGN CHOICES (model parameters — not verified facts)
# ---------------------------------------------------------------------------
HFA = 2.0                 # points, typical NFL home-field advantage
NEUTRAL_HFA = 0.0         # neutral-site games (Munich, Mexico City)
REGRESS = 0.5             # regresses raw net-per-game toward 0 (schedule noise)
BASE_WEIGHT = {           # starter-level point value of losing the listed player
    "QB": 3.5, "RB": 1.0, "FB": 0.5, "WR": 1.0, "TE": 0.75,
    "OL": 0.5, "OT": 0.5, "G": 0.5, "C": 0.5,
    "DL": 0.75, "DT": 0.75, "DE": 0.75, "EDGE": 0.75, "OLB": 0.75,
    "LB": 0.5, "CB": 0.75, "S": 0.5, "DB": 0.5,
    "K": 0.25, "P": 0.25, "LS": 0.1,
}
TIER_MULT = {1: 1.0, 2: 0.6, 3: 0.4, 4: 0.3, None: 1.0}   # None = tier unverified
STATUS_MULT = {"OUT": 1.0, "DOUBTFUL": 0.5, "QUESTIONABLE": 0.25, "IR": 1.0}
QB_ROOM_CAP = True   # design choice: only the top-of-room QB absence is priced
                     # (one QB plays the position); further QB absences are flagged
OFF_POS = {"QB", "RB", "FB", "WR", "TE", "OL", "OT", "G", "C"}
ST_POS = {"K", "P", "LS"}

# ---------------------------------------------------------------------------
# VERIFIED DATA — 2026 NFL standings after TNF, Nov 12 2026 (NFL.com, 32 teams)
# team: (name, W, L, T, PF, PA, streak)
# ---------------------------------------------------------------------------
TEAMS = {
    "LAC": ("Los Angeles Chargers", 0, 8, 0, 121, 219, "8L"),
    "MIA": ("Miami Dolphins", 1, 7, 0, 126, 200, "2L"),
    "TEN": ("Tennessee Titans", 1, 7, 0, 144, 199, "2L"),
    "IND": ("Indianapolis Colts", 2, 7, 0, 184, 249, "5L"),
    "NYJ": ("New York Jets", 2, 7, 0, 182, 223, "4L"),
    "PHI": ("Philadelphia Eagles", 2, 7, 0, 148, 221, "7L"),
    "AZ": ("Arizona Cardinals", 3, 6, 0, 178, 255, "1L"),
    "ATL": ("Atlanta Falcons", 3, 6, 0, 188, 223, "2L"),
    "CAR": ("Carolina Panthers", 3, 5, 0, 199, 219, "3L"),
    "HOU": ("Houston Texans", 3, 5, 0, 209, 192, "1W"),
    "NO": ("New Orleans Saints", 3, 5, 0, 185, 216, "1W"),
    "TB": ("Tampa Bay Buccaneers", 3, 6, 0, 202, 178, "1L"),
    "WAS": ("Washington Commanders", 3, 5, 1, 196, 223, "1W"),
    "BAL": ("Baltimore Ravens", 4, 5, 0, 189, 236, "4L"),
    "DAL": ("Dallas Cowboys", 4, 5, 0, 246, 236, "1W"),
    "LV": ("Las Vegas Raiders", 4, 5, 0, 238, 268, "1L"),
    "CLE": ("Cleveland Browns", 5, 4, 0, 161, 196, "2L"),
    "LAR": ("Los Angeles Rams", 5, 4, 0, 214, 181, "3W"),
    "NE": ("New England Patriots", 5, 4, 0, 211, 207, "1L"),
    "NYG": ("New York Giants", 5, 3, 1, 203, 196, "1L"),
    "SEA": ("Seattle Seahawks", 5, 4, 0, 202, 162, "1W"),
    "CIN": ("Cincinnati Bengals", 6, 2, 0, 240, 175, "4W"),
    "DET": ("Detroit Lions", 6, 2, 0, 222, 189, "4W"),
    "GB": ("Green Bay Packers", 6, 3, 0, 216, 191, "2W"),
    "JAX": ("Jacksonville Jaguars", 6, 2, 0, 229, 121, "2W"),
    "KC": ("Kansas City Chiefs", 6, 2, 0, 202, 143, "1W"),
    "MIN": ("Minnesota Vikings", 6, 2, 0, 146, 116, "2L"),
    "PIT": ("Pittsburgh Steelers", 6, 2, 0, 180, 144, "4W"),
    "BUF": ("Buffalo Bills", 7, 1, 0, 256, 187, "4W"),
    "CHI": ("Chicago Bears", 7, 2, 0, 241, 184, "4W"),
    "DEN": ("Denver Broncos", 7, 2, 0, 198, 186, "5W"),
    "SF": ("San Francisco 49ers", 7, 1, 0, 235, 156, "1W"),
}

# ---------------------------------------------------------------------------
# VERIFIED DATA — Week 10 slate (NFL.com). ("game_id", away, home, date, time,
# tv, note). Byes: CHI, DEN, PHI, TB.
# ---------------------------------------------------------------------------
GAMES_W10 = [
    ("W10-01", "WAS", "NYG", "2026-11-12", "20:15 ET", "Prime Video",
     "TNF FINAL: WAS 24, NYG 21"),
    ("W10-02", "NE", "DET", "2026-11-15", "09:30 ET", "FOX",
     "Munich, Germany (neutral site)"),
    ("W10-03", "KC", "ATL", "2026-11-15", "13:00 ET", "CBS", ""),
    ("W10-04", "HOU", "CLE", "2026-11-15", "13:00 ET", "FOX", ""),
    ("W10-05", "MIN", "GB", "2026-11-15", "13:00 ET", "FOX", ""),
    ("W10-06", "MIA", "IND", "2026-11-15", "13:00 ET", "CBS", ""),
    ("W10-07", "CAR", "NO", "2026-11-15", "13:00 ET", "FOX", ""),
    ("W10-08", "BUF", "NYJ", "2026-11-15", "13:00 ET", "CBS", ""),
    ("W10-09", "JAX", "TEN", "2026-11-15", "13:00 ET", "FOX", ""),
    ("W10-10", "LAR", "AZ", "2026-11-15", "16:05 ET", "CBS", ""),
    ("W10-11", "SEA", "LV", "2026-11-15", "16:05 ET", "CBS", ""),
    ("W10-12", "SF", "DAL", "2026-11-15", "16:25 ET", "FOX", ""),
    ("W10-13", "PIT", "CIN", "2026-11-15", "20:20 ET", "NBC", "SNF"),
    ("W10-14", "LAC", "BAL", "2026-11-16", "20:15 ET", "ABC/ESPN", "MNF"),
]
BYES_W10 = ["CHI", "DEN", "PHI", "TB"]

GAMES_W11 = [
    ("W11-01", "IND", "HOU", "2026-11-19", "20:15 ET", "Prime Video", "TNF"),
    ("W11-02", "MIA", "BUF", "2026-11-22", "13:00 ET", "CBS", ""),
    ("W11-03", "BAL", "CAR", "2026-11-22", "13:00 ET", "FOX", ""),
    ("W11-04", "NO", "CHI", "2026-11-22", "13:00 ET", "FOX", ""),
    ("W11-05", "TEN", "DAL", "2026-11-22", "13:00 ET", "FOX", ""),
    ("W11-06", "TB", "DET", "2026-11-22", "13:00 ET", "FOX", ""),
    ("W11-07", "AZ", "KC", "2026-11-22", "13:00 ET", "CBS", ""),
    ("W11-08", "PIT", "PHI", "2026-11-22", "13:00 ET", "CBS", ""),
    ("W11-09", "NYJ", "LAC", "2026-11-22", "16:05 ET", "FOX", ""),
    ("W11-10", "JAX", "NYG", "2026-11-22", "16:25 ET", "CBS", ""),
    ("W11-11", "LV", "DEN", "2026-11-22", "16:25 ET", "CBS", ""),
    ("W11-12", "MIN", "SF", "2026-11-22", "20:20 ET", "NBC",
     "SNF Mexico City (neutral site)"),
    ("W11-13", "CIN", "WAS", "2026-11-23", "20:15 ET", "ESPN", "MNF"),
]
BYES_W11 = ["ATL", "CLE", "GB", "LAR", "NE", "SEA"]

# ---------------------------------------------------------------------------
# VERIFIED DATA — official Week 10 game-status injury report (NFL.com),
# transcribed row-by-row. (game_id, team, player, pos, injury, status)
# ---------------------------------------------------------------------------
S = "OUT"
D = "DOUBTFUL"
Q = "QUESTIONABLE"
INJURIES = [
    # NE @ DET (Munich)
    ("W10-02", "NE", "TreVeyon Henderson", "RB", "illness", S),
    ("W10-02", "NE", "Ben Brown", "OL", "knee", S),
    ("W10-02", "NE", "Carlton Davis III", "CB", "knee", S),
    ("W10-02", "NE", "Rhamondre Stevenson", "RB", "knee", Q),
    ("W10-02", "NE", "Reggie Gilliam", "FB", "knee", Q),
    ("W10-02", "NE", "A.J. Brown", "WR", "ankle/knee", Q),
    ("W10-02", "NE", "Cameron Latu", "TE", "back", Q),
    ("W10-02", "NE", "Walter Rouse", "OL", "concussion", Q),
    ("W10-02", "NE", "Greg Van Roten", "OL", "hamstring", Q),
    ("W10-02", "NE", "Charles Woods", "CB", "hamstring", Q),
    ("W10-02", "NE", "Kevin Byard III", "S", "chest", Q),
    ("W10-02", "NE", "Brenden Schooler", "S", "hamstring", Q),
    ("W10-02", "DET", "Kerby Joseph", "S", "knee", S),
    ("W10-02", "DET", "Cade Mays", "C", "ankle", S),
    ("W10-02", "DET", "D.J. Reed", "CB", "hip", S),
    ("W10-02", "DET", "Sione Vaki", "RB", "ankle", Q),
    ("W10-02", "DET", "Amon-Ra St. Brown", "WR", "rib", Q),
    # KC @ ATL
    ("W10-03", "KC", "Jaylon Moore", "OL", "ankle", S),
    ("W10-03", "KC", "Omarr Norman-Lott", "DT", "knee", S),
    ("W10-03", "KC", "Peter Woods", "DL", "neck", S),
    ("W10-03", "KC", "Jaydn Ott", "RB", "hamstring", Q),
    ("W10-03", "KC", "Kenneth Walker III", "RB", "groin", Q),
    ("W10-03", "KC", "Mansoor Delane", "CB", "shoulder", Q),
    ("W10-03", "ATL", "Zachariah Branch", "WR", "hamstring", S),
    ("W10-03", "ATL", "Divine Deablo", "LB", "forearm", D),
    ("W10-03", "ATL", "James Pearce Jr.", "DE", "back", Q),
    ("W10-03", "ATL", "Gervon Dexter", "DT", "illness", Q),
    ("W10-03", "ATL", "Josh Woods", "LB", "ankle", Q),
    # HOU @ CLE
    ("W10-04", "HOU", "Marvin Harrison Jr.", "WR", "hamstring", S),
    ("W10-04", "HOU", "Brevin Jordan", "TE", "finger/foot", S),
    ("W10-04", "HOU", "Keylan Rutledge", "OL", "neck/shoulder", S),
    ("W10-04", "HOU", "Danielle Hunter", "DE", "hamstring", S),
    ("W10-04", "HOU", "Azeez Al-Shaair", "LB", "groin", S),
    ("W10-04", "HOU", "David Montgomery", "RB", "groin", Q),
    ("W10-04", "HOU", "Trent Brown", "OT", "illness/wrist", Q),
    ("W10-04", "HOU", "Wyatt Teller", "G", "back/illness", Q),
    ("W10-04", "HOU", "Will Anderson Jr.", "DE", "ankle", Q),
    ("W10-04", "HOU", "Jake Hummel", "LB", "groin", Q),
    ("W10-04", "HOU", "Jaylin Smith", "CB", "hamstring", Q),
    ("W10-04", "CLE", "Michael Burton", "FB", "calf", S),
    ("W10-04", "CLE", "Ronnie Hickman Jr.", "S", "concussion", S),
    ("W10-04", "CLE", "Denzel Boston", "WR", "toe", Q),
    # MIN @ GB
    ("W10-05", "MIN", "Kyler Murray", "QB", "hamstring", S),
    ("W10-05", "MIN", "Jauan Jennings", "WR", "calf", S),
    ("W10-05", "MIN", "T.J. Hockenson", "TE", "wrist/chest", S),
    ("W10-05", "MIN", "Tyrion Ingram-Dawkins", "DL", "ankle", S),
    ("W10-05", "MIN", "Blake Cashman", "LB", "concussion", S),
    ("W10-05", "MIN", "Jordan Addison", "WR", "thumb", Q),
    ("W10-05", "MIN", "Kyle Van Noy", "OLB", "calf", Q),
    ("W10-05", "MIN", "Josh Metellus", "S", "shoulder", Q),
    ("W10-05", "GB", "Josh Jacobs", "RB", "finger", S),
    ("W10-05", "GB", "Josh Whyle", "TE", "concussion", S),
    ("W10-05", "GB", "Sean Rhyan", "OL", "ankle", S),
    ("W10-05", "GB", "Micah Parsons", "EDGE", "knee/illness", S),
    ("W10-05", "GB", "Zaire Franklin", "LB", "shin", D),
    ("W10-05", "GB", "Chris Brooks", "RB", "ankle", Q),
    ("W10-05", "GB", "Skyy Moore", "WR", "ankle", Q),
    ("W10-05", "GB", "Kevin Zeitler", "G", "ankle/triceps", Q),
    ("W10-05", "GB", "Travis Glover", "OL", "knee", Q),
    ("W10-05", "GB", "Lukas Van Ness", "EDGE", "back", Q),
    ("W10-05", "GB", "Javon Bullard", "S", "ankle/knee", Q),
    ("W10-05", "GB", "Xavier McKinney", "S", "foot", Q),
    # MIA @ IND
    ("W10-06", "MIA", "Jared Wayne", "WR", "quad", S),
    ("W10-06", "MIA", "Aaron Brewer", "C", "concussion", S),
    ("W10-06", "MIA", "Chris Bell", "WR", "knee", D),
    ("W10-06", "MIA", "Darrell Baker Jr.", "CB", "knee", Q),
    ("W10-06", "IND", "Mo Alie-Cox", "TE", "groin", S),
    ("W10-06", "IND", "Jalen Travis", "OT", "knee", S),
    ("W10-06", "IND", "Jerry Tillery", "DT", "calf", S),
    ("W10-06", "IND", "Jaylon Carlies", "LB", "neck", S),
    ("W10-06", "IND", "Akeem Davis-Gaither", "LB", "knee", S),
    ("W10-06", "IND", "Luke Rhodes", "LS", "hamstring", S),
    ("W10-06", "IND", "Will Mallory", "TE", "hamstring", Q),
    ("W10-06", "IND", "Arden Key", "DE", "hamstring", Q),
    # CAR @ NO
    ("W10-07", "CAR", "Bobby Okereke", "LB", "foot", S),
    ("W10-07", "CAR", "Jonathon Brooks", "RB", "groin", D),
    ("W10-07", "CAR", "Mike Jackson", "CB", "groin", D),
    ("W10-07", "CAR", "Xavier Legette", "WR", "knee", Q),
    ("W10-07", "CAR", "Brady Christensen", "OL", "hamstring", Q),
    ("W10-07", "CAR", "Jaelan Phillips", "OLB", "hamstring", Q),
    ("W10-07", "CAR", "Will Lee III", "CB", "hamstring", Q),
    ("W10-07", "NO", "CJ Donaldson", "RB", "shoulder", S),
    ("W10-07", "NO", "Taliese Fuaga", "OT", "knee", S),
    ("W10-07", "NO", "Erik McCoy", "C", "biceps", S),
    ("W10-07", "NO", "Christen Miller", "DL", "knee", S),
    ("W10-07", "NO", "Travis Etienne", "RB", "hamstring", Q),
    ("W10-07", "NO", "Martin Emerson", "CB", "shin", Q),
    # BUF @ NYJ
    ("W10-08", "BUF", "Spencer Brown", "OT", "ankle", D),
    ("W10-08", "BUF", "Tyrell Shavers", "WR", "knee", Q),
    ("W10-08", "BUF", "Christian Benford", "CB", "wrist", Q),
    ("W10-08", "BUF", "Sam Franklin", "DB", "shoulder", Q),
    ("W10-08", "BUF", "Jordan Hancock", "DB", "hamstring", Q),
    ("W10-08", "NYJ", "Trevin Wallace", "LB", "groin", S),
    ("W10-08", "NYJ", "Omar Cooper Jr.", "WR", "ankle", Q),
    ("W10-08", "NYJ", "Adonai Mitchell", "WR", "knee", Q),
    ("W10-08", "NYJ", "Garrett Wilson", "WR", "concussion", Q),
    ("W10-08", "NYJ", "Joseph Ossai", "EDGE", "ankle", Q),
    ("W10-08", "NYJ", "Harrison Phillips", "DL", "ankle", Q),
    ("W10-08", "NYJ", "Jarvis Brownlee Jr.", "CB", "illness", Q),
    ("W10-08", "NYJ", "Nahshon Wright", "CB", "back", Q),
    ("W10-08", "NYJ", "VJ Payne", "S", "knee", Q),
    # JAX @ TEN
    ("W10-09", "JAX", "BJ Green II", "DE", "forearm", S),
    ("W10-09", "JAX", "Jordan Davis", "DT", "rest", S),
    ("W10-09", "JAX", "Jessie Bates", "S", "rest", S),
    ("W10-09", "JAX", "Robert Hainsey", "OL", "concussion", Q),
    ("W10-09", "TEN", "Carnell Tate", "WR", "shoulder", S),
    ("W10-09", "TEN", "Peter Skoronski", "G", "hamstring", S),
    ("W10-09", "TEN", "Cody Barton", "LB", "concussion", S),
    ("W10-09", "TEN", "Anthony Hill Jr.", "LB", "neck", S),
    ("W10-09", "TEN", "Tommy Townsend", "P", "left knee/right Achilles", S),
    ("W10-09", "TEN", "Tyjae Spears", "RB", "knee", Q),
    # LAR @ AZ
    ("W10-10", "LAR", "Terrance Ferguson", "TE", "ankle/hamstring", S),
    ("W10-10", "LAR", "Steve Avila", "OL", "hamstring", S),
    ("W10-10", "LAR", "Davis Allen", "TE", "oblique", Q),
    ("W10-10", "LAR", "Myles Garrett", "OLB", "knee", Q),
    ("W10-10", "LAR", "Trent McDuffie", "CB", "back", Q),
    ("W10-10", "LAR", "Kamren Curl", "S", "toe", Q),
    ("W10-10", "LAR", "Joe Cardona", "LS", "ankle", Q),
    ("W10-10", "AZ", "Hjalte Froholdt", "OL", "concussion", S),
    ("W10-10", "AZ", "Jon Gaines II", "OL", "ankle", S),
    ("W10-10", "AZ", "Zach Carter", "DL", "knee", S),
    ("W10-10", "AZ", "Hunter Long", "TE", "knee", Q),
    ("W10-10", "AZ", "Jayden Williams", "OL", "knee", Q),
    ("W10-10", "AZ", "Roy Lopez", "DL", "toe/ankle", Q),
    ("W10-10", "AZ", "Darius Robinson", "DL", "wrist", Q),
    ("W10-10", "AZ", "Max Melton", "CB", "knee/hand", Q),
    ("W10-10", "AZ", "Andrew Wingard", "S", "groin", Q),
    # SEA @ LV
    ("W10-11", "SEA", "Sam Darnold", "QB", "ribs, quadricep", S),
    ("W10-11", "SEA", "Charles Cross", "OT", "ankle", S),
    ("W10-11", "SEA", "Quenton Nelson", "G", "knee", S),
    ("W10-11", "SEA", "Leonard Williams", "DT", "stinger", S),
    ("W10-11", "LV", "Dont'e Thornton Jr.", "WR", "back", Q),
    ("W10-11", "LV", "Thomas Booker", "DT", "ankle", Q),
    # SF @ DAL
    ("W10-12", "SF", "Mike Evans", "WR", "Achilles", S),
    ("W10-12", "SF", "Trent Williams", "OT", "shoulder", Q),
    ("W10-12", "SF", "CJ West", "DT", "knee", Q),
    ("W10-12", "SF", "Dre Greenlaw", "LB", "knee", Q),
    ("W10-12", "SF", "Renardo Green", "CB", "back", Q),
    ("W10-12", "SF", "Nate Hobbs", "CB", "adductor", Q),
    ("W10-12", "SF", "Deommodore Lenoir", "CB", "foot", Q),
    ("W10-12", "SF", "Upton Stout", "CB", "shoulder", Q),
    ("W10-12", "DAL", "Tyler Goodson", "RB", "ankle, knee", S),
    ("W10-12", "DAL", "Jonathan Mingo", "WR", "ankle", S),
    ("W10-12", "DAL", "Jake Ferguson", "TE", "knee, ankle", S),
    ("W10-12", "DAL", "Donovan Ezeiruaku", "LB", "ankle", S),
    ("W10-12", "DAL", "P.J. Locke", "S", "concussion", S),
    ("W10-12", "DAL", "Juanyeh Thomas", "S", "hamstring", D),
    ("W10-12", "DAL", "Jonathan Bullard", "DT", "calf", Q),
    ("W10-12", "DAL", "DaRon Bland", "CB", "ankle", Q),
    ("W10-12", "DAL", "Devin Moore", "CB", "hip", Q),
    ("W10-12", "DAL", "Joey Porter Jr.", "CB", "ankle, foot", Q),
    ("W10-12", "DAL", "Alijah Clark", "S", "illness", Q),
    # PIT @ CIN
    ("W10-13", "PIT", "Derrick Harmon", "DT", "foot", Q),
    ("W10-13", "CIN", "Kyle Dugger", "S", "quadricep", S),
    ("W10-13", "CIN", "Andrei Iosivas", "WR", "thumb", D),
    ("W10-13", "CIN", "Brian Parker II", "G", "knee", D),
    ("W10-13", "CIN", "Jalen Davis", "CB", "hamstring", D),
    # LAC @ BAL — no game-status designations on the official WEEKLY report; the
    # QB room below is IR/season-ending and thus absent from that report (F16).
    ("W10-14", "BAL", "Lamar Jackson", "QB", "broken/dislocated right thumb (surgery)", "IR"),
    ("W10-14", "BAL", "Tyler Huntley", "QB", "toe (season-ending)", "IR"),
    # WAS @ NYG (TNF, final)
    ("W10-01", "WAS", "Colson Yankoff", "TE", "knee", S),
    ("W10-01", "WAS", "Lucas Patrick", "C", "concussion", S),
    ("W10-01", "NYG", "Malik Harrison", "LB", "groin", Q),
]

# ---------------------------------------------------------------------------
# VERIFIED DATA — club-published depth charts, accessed 2026-11-14.
# (team, player) -> (tier, expected replacement, replacement tier, chart url,
#                    note)   tier None => player not found on chart (flagged)
# ---------------------------------------------------------------------------
MIN_C = "https://www.vikings.com/team/depth-chart"
GB_C = "https://www.packers.com/team/depth-chart"
SEA_C = "https://www.seahawks.com/team/depth-chart/"
DET_C = "https://www.detroitlions.com/team/depth-chart"
NE_C = "https://www.patriots.com/team/depth-chart/"
AZ_C = "https://www.azcardinals.com/team/depth-chart"
DAL_C = "https://www.dallascowboys.com/team/depth-chart"
BAL_C = "https://www.baltimoreravens.com/team/depth-chart/"

# IR / season-ending absences do not appear on the weekly game-status report.
# These rows are sourced from the team statement as reported by trusted media and
# the club depth chart (cross-session finding F02 of arena-e8bf2075, confirmed
# independently on 2026-11-14 — see research/sources.md).
ATHLETIC_URL = "https://www.nytimes.com/athletic/7779046/2026/11/13/lamar-jackson-ravens-thumb-injury-timeline/"
NBC_URL = "https://www.nbcsports.com/fantasy/football/player-news/2026-11-13/minter-confirms-jackson-thumb-is-out-6-10-weeks"
EXTRA_SRC = {
    ("BAL", "Lamar Jackson"): ATHLETIC_URL,
    ("BAL", "Tyler Huntley"): NBC_URL,
}

CHART = {
    ("MIN", "Kyler Murray"): (1, "Carson Wentz (QB2)", 2, MIN_C, ""),
    ("MIN", "Jauan Jennings"): (3, "Myles Price", 2, MIN_C, "chart WR3"),
    ("MIN", "T.J. Hockenson"): (1, "Gavin Bartholomew", 2, MIN_C, ""),
    ("MIN", "Tyrion Ingram-Dawkins"): (1, "Elijah Williams", 2, MIN_C, ""),
    ("MIN", "Blake Cashman"): (1, "Ivan Pace Jr.", 2, MIN_C, ""),
    ("MIN", "Jordan Addison"): (2, "Tai Felton", 2, MIN_C, "chart WR2"),
    ("MIN", "Kyle Van Noy"): (2, "Chaz Chambliss", 3, MIN_C, ""),
    ("MIN", "Josh Metellus"): (2, "Jay Ward", 2, MIN_C, ""),
    ("GB", "Josh Jacobs"): (1, "MarShawn Lloyd (RB2)", 2, GB_C, "Pierre Strong Jr. (RB3)"),
    ("GB", "Josh Whyle"): (4, "n/a — chart TE4 behind Kraft/Smith/Redman", None, GB_C, ""),
    ("GB", "Sean Rhyan"): (1, "Jager Burton", 2, GB_C, "chart starting C"),
    ("GB", "Micah Parsons"): (None, "", None, GB_C,
        "IRREGULARITY: listed OUT on NFL.com injury report but absent from Nov 10 club chart"),
    ("GB", "Zaire Franklin"): (1, "Ty'Ron Hopper", 2, GB_C, ""),
    ("GB", "Chris Brooks"): (None, "", None, GB_C, "not on club chart (chart lists Jacobs/Lloyd/Strong/Johnson)"),
    ("GB", "Skyy Moore"): (None, "", None, GB_C, "not on club chart"),
    ("GB", "Kevin Zeitler"): (2, "", None, GB_C, "chart RG2 behind Tomlinson"),
    ("GB", "Travis Glover"): (2, "", None, GB_C, "chart LG2 behind Banks"),
    ("GB", "Lukas Van Ness"): (1, "Brenton Cox Jr.", 2, GB_C, ""),
    ("GB", "Javon Bullard"): (1, "Kamal Hadden", 2, GB_C, "chart NB"),
    ("GB", "Xavier McKinney"): (1, "Kitan Oladapo", 2, GB_C, ""),
    ("SEA", "Sam Darnold"): (1, "Drew Lock (QB2)", 2, SEA_C, "Jalen Milroe (QB3)"),
    ("SEA", "Charles Cross"): (1, "Josh Jones", 2, SEA_C, "chart LT"),
    ("SEA", "Quenton Nelson"): (1, "Anthony Bradford", 2, SEA_C, "chart LG"),
    ("SEA", "Leonard Williams"): (1, "Rylie Mills", 2, SEA_C, "chart DT"),
    ("DET", "Kerby Joseph"): (None, "", None, DET_C,
        "IRREGULARITY: listed OUT on NFL.com injury report but absent from club chart"),
    ("DET", "Cade Mays"): (1, "Juice Scruggs", 2, DET_C, ""),
    ("DET", "D.J. Reed"): (1, "Rock Ya-Sin", 2, DET_C, "Khalil Dorsey (CB3)"),
    ("DET", "Sione Vaki"): (2, "Jacob Saylors", 3, DET_C, ""),
    ("DET", "Amon-Ra St. Brown"): (1, "DeAndre Carter", 2, DET_C, ""),
    ("NE", "TreVeyon Henderson"): (2, "Corey Kiner (RB3)", 3, NE_C, "chart RB2 behind Stevenson"),
    ("NE", "Ben Brown"): (1, "Walter Rouse", 2, NE_C, "chart starting LG"),
    ("NE", "Carlton Davis III"): (1, "Channing Canada", 2, NE_C, ""),
    ("NE", "Rhamondre Stevenson"): (1, "TreVeyon Henderson (OUT)", 2, NE_C, "RB1 questionable"),
    ("NE", "A.J. Brown"): (1, "Efton Chism III", 2, NE_C, ""),
    ("NE", "Kevin Byard III"): (1, "Jaylen Reed", 2, NE_C, ""),
    ("NE", "Charles Woods"): (2, "Karon Prunty", 2, NE_C, "chart CB backup"),
    ("NE", "Walter Rouse"): (2, "", None, NE_C, "chart OL backup (LG/RG)"),
    ("NE", "Cameron Latu"): (3, "", None, NE_C, "chart TE3"),
    ("AZ", "Hjalte Froholdt"): (1, "Kingsley Eguakun", 2, AZ_C, ""),
    ("AZ", "Jon Gaines II"): (2, "", None, AZ_C, "chart RG2 behind Isaiah Adams"),
    ("AZ", "Zach Carter"): (None, "", None, AZ_C, "not on club chart"),
    ("AZ", "Jayden Williams"): (1, "Jedrick Wills", 2, AZ_C, "chart LT"),
    ("AZ", "Roy Lopez"): (1, "Andrew Billings", 2, AZ_C, "chart NT"),
    ("AZ", "Darius Robinson"): (2, "L.J. Collier", 2, AZ_C, "chart DT2"),
    ("AZ", "Max Melton"): (2, "Kei'Trel Clark", 2, AZ_C, "chart CB2"),
    ("AZ", "Andrew Wingard"): (1, "Kitan Crawford", 2, AZ_C, "chart S"),
    ("AZ", "Hunter Long"): (None, "", None, AZ_C, "not on club chart (TE behind McBride/Higgins)"),
    ("DAL", "Tyler Goodson"): (2, "", None, DAL_C, "chart RB2 behind Javonte Williams"),
    ("DAL", "Jonathan Mingo"): (2, "", None, DAL_C, "chart WR backup behind Lamb"),
    ("DAL", "Jake Ferguson"): (1, "Luke Schoonmaker (TE2)", 2, DAL_C,
        "chart co-TE1 with Brevyn Spann-Ford"),
    ("DAL", "Donovan Ezeiruaku"): (1, "James Houston", 2, DAL_C, "chart OLB"),
    ("DAL", "P.J. Locke"): (1, "Markquese Bell (co-S)", 2, DAL_C, "chart co-S"),
    ("DAL", "Juanyeh Thomas"): (2, "", None, DAL_C, "chart S backup"),
    ("DAL", "DaRon Bland"): (1, "Cobie Durant", 2, DAL_C, ""),
    ("DAL", "Joey Porter Jr."): (1, "Shavon Revel Jr.", 2, DAL_C, ""),
    ("DAL", "Alijah Clark"): (2, "", None, DAL_C, "chart S backup"),
    # BAL: club chart fetched 2026-11-14 — QB room completely rebuilt via IR + trade
    ("BAL", "Lamar Jackson"): (1, "Jacoby Brissett (chart QB1, acquired from AZ)", 2, BAL_C,
        "IR 6-10 weeks (thumb surgery) — NOT on weekly report; starter per Ravens HC Jesse Minter statement"),
    ("BAL", "Tyler Huntley"): (2, "Joe Fagnano (chart QB2)", 2, BAL_C,
        "season-ending toe — NOT on weekly report; QB-room cap applied (not priced on top of Jackson)"),
    # Teams whose charts were NOT fetched or unavailable -> tier None everywhere
}

# Chart availability flags per team (for the deficiency page / flagged page)
CHART_STATUS = {
    "MIN": ("club chart fetched (marked '2026 Unofficial Depth Chart')", MIN_C),
    "GB": ("club chart fetched (dated 'Unofficial, Nov. 10, 2026')", GB_C),
    "SEA": ("club chart fetched", SEA_C),
    "DET": ("club chart fetched (marked '2026 Unofficial Depth Chart')", DET_C),
    "NE": ("club chart fetched (published by Patriots.com writers)", NE_C),
    "AZ": ("club chart fetched (labeled 'Official Depth Chart')", AZ_C),
    "DAL": ("club chart fetched (marked 'Unofficial 2026')", DAL_C),
    "HOU": ("UNAVAILABLE — chart published as image on houstontexans.com", "https://www.houstontexans.com/team/depth-chart"),
    "SF": ("UNAVAILABLE — sf49ers.com depth-chart page returned HTTP 500 on 2 tries", "https://www.sf49ers.com/team/depth-chart"),
}

# ---------------------------------------------------------------------------
# VERIFIED-MARKET REFERENCE — books disagree; each game carries its source.
# home spread convention: negative = home favorite.
# (home_spread, total, primary_source_key, market_range_note, flags)
# ---------------------------------------------------------------------------
ESPN = "https://www.espn.com/espn/betting/story/_/id/50414742/2026-nfl-week-10-schedule-odds-point-spreads-totals"
SBR = "https://www.sportsbookreview.com/picks/nfl/week-10-odds-betting-lines-2026/"
CBS = "https://cbssports.com/betting/news/week-10-nfl-betting-odds-lines-totals-spreads"
BETUS = "https://www.betus.com.pa/sportsbook/nfl/nfl-odds-week-10/"
BETMGM = "https://sportsdata.usatoday.com/football/nfl/odds"

# HOME spread convention: negative = HOME favorite. Away favorites encode positive.
MARKET = {
    "W10-01": (-1.5, 43.5, SBR,
               "CBS: NYG -2.5 / 41.0; SBR(bet365): NYG -1.5 / 43.5",
               "spread 1.5-2.5, total 41.0-43.5 disagreement (game final: WAS 24-21)"),
    "W10-02": (-2.5, 49.5, ESPN,
               "ESPN/BetMGM: DET -2.5 / 49.5; betus: DET -3.0 / 49.5; SBR: DET -2.5 / 51.5",
               "total 49.5-51.5 disagreement; neutral site (Munich)"),
    "W10-03": (3.5, 45.5, SBR,
               "SBR: KC -3.5 / 45.5; betus: KC -3.0 / 47.0; ESPN total 47.5 (opened 45.5)",
               "spread 3.0-3.5, total 45.5-47.5 disagreement"),
    "W10-04": (4.5, 39.5, SBR,
               "SBR/CBS: HOU -4.5 / 39.5; betus: HOU -4.5 / 40.5",
               "minor total disagreement"),
    "W10-05": (-3.0, 41.5, ESPN,
               "ESPN: GB -3.0 / 41.5 (opened 45.5); SBR: GB -3.5 / 42.5",
               "spread 3.0-3.5; total opened 45.5 -> 41.5 (Jacobs/Parsons/Murray news)"),
    "W10-06": (-3.5, 38.5, ESPN,
               "ESPN/CBS: IND -3.5 / 38.5; SBR: IND -2.5 / 40.5; ESPN shows opened 47.5",
               "spread 2.5-3.5, total 38.5-40.5; ESPN 'opened 47.5' vs 38.5 now = anomalous 9-pt open-to-now move (flagged)"),
    "W10-07": (1.5, 47.5, SBR,
               "SBR(bet365): CAR -1.5 / 47.5 (home NO +1.5); BetMGM: NO -2.5 / 49.0",
               "FAVORITE DISAGREEMENT: books disagree on who is favored (CAR -1.5 vs NO -2.5), total 47.5-49.0"),
    "W10-08": (8.5, 51.0, ESPN,
               "ESPN: BUF -8.5; betus: BUF -9.0 / 51.0; SBR: BUF -7.5 / 51.5",
               "spread 7.5-9.0 disagreement"),
    "W10-09": (10.5, 46.5, ESPN,
               "ESPN/betus: JAX -10.5 / 46.5; SBR: JAX -9.5 / 47.5",
               "spread 9.5-10.5"),
    "W10-10": (9.5, 39.5, ESPN,
               "ESPN/BetMGM/betus: LAR -9.5 / 39.5; SBR: LAR -7.5 / 44.5",
               "SBR outlier (spread 7.5-9.5, total 39.5-44.5)"),
    "W10-11": (6.5, 40.5, ESPN,
               "ESPN/betus (Nov 13): SEA -6.5 / 40.5; CBS/SBR (Nov 11): SEA -3.5 / 43.5",
               "MAJOR disagreement 3.5-6.5 — ~3pt move after Sam Darnold ruled out Wed"),
    "W10-12": (3.5, 55.5, ESPN,
               "ESPN: SF -3.5 / 55.5 (opened 52.5); betus: SF -4.0 / 55.5; SBR: SF -4.5 / 55.5",
               "spread 3.5-4.5"),
    "W10-13": (-3.5, 50.0, BETUS,
               "betus: CIN -3.5 / 50.0; BetMGM: CIN -3.5 / 49.5; SBR: CIN -3.5 / 47.5",
               "spread agreed 3.5; total 47.5-50.0"),
    "W10-14": (-4.5, 38.5, CBS,
               "CBS/BetMGM: BAL -4.5 / 38.5; SBR: BAL -5.5 / 38.5",
               "spread 4.5-5.5"),
}

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def games_of(team):
    w, l, t = TEAMS[team][1], TEAMS[team][2], TEAMS[team][3]
    return w + l + t


def netpg(team):
    _, w, l, t, pf, pa, _ = TEAMS[team]
    g = w + l + t
    return (pf - pa) / g


def winpct(team):
    _, w, l, t, pf, pa, _ = TEAMS[team]
    g = w + l + t
    return (w + 0.5 * t) / g


def pos_side(pos):
    if pos in OFF_POS:
        return "OFF"
    if pos in ST_POS:
        return "ST"
    return "DEF"


def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / math.sqrt(sxx * syy)


def half(x):
    """round to nearest 0.5"""
    return round(x * 2) / 2


def injury_rows(game_id):
    return [r for r in INJURIES if r[0] == game_id]


def adjustments(game_id, team):
    """returns (off_adj, def_adj, st_adj, rows) where rows are
    (player, pos, status, tier, weight_used, flag, injury)"""
    off = deff = st = 0.0
    rows = []
    for gid, tm, player, pos, inj, status in INJURIES:
        if gid != game_id or tm != team:
            continue
        tier, repl, rtier, url, note = CHART.get((team, player), (None, "", None, "", ""))
        base = BASE_WEIGHT.get(pos, 0.5)
        w = base * TIER_MULT[tier] * STATUS_MULT[status]
        side = pos_side(pos)
        rows.append([player, pos, status, tier, round(w, 3), "", inj, repl, rtier, url])
    # QB-room cap: price only the top-of-room QB absence (one QB plays the spot)
    if QB_ROOM_CAP:
        qbs = [r for r in rows if r[1] == "QB" and r[4] > 0]
        qbs.sort(key=lambda r: (r[3] if r[3] is not None else 9))
        for extra in qbs[1:]:
            extra[5] = ("QB-room cap: not priced on top of the higher-tier QB absence "
                        "(tracked, flagged)") + (" | " + (CHART.get((team, extra[0]), (None,"",None,"",""))[4] or "") if CHART.get((team, extra[0]), (None,"",None,"",""))[4] else "")
            extra[4] = 0.0
    for player, pos, status, tier, w, flag, inj, repl, rtier, url in rows:
        side = pos_side(pos)
        if side == "OFF":
            off += w
        elif side == "DEF":
            deff += w
        else:
            st += w
        note = CHART.get((team, player), (None, "", None, "", ""))[4]
        if tier is None and "tier unverified" not in flag:
            flag = ("tier unverified (no club chart row) — position-group default weight used"
                    + (" | " + note if note else "") + (" | " + flag if flag else ""))
        elif note and note not in flag:
            flag = (flag + " | " if flag else "") + note
    return off, deff, st, rows


def model_game(game_id, away, home, neutral):
    off_a, def_a, st_a, rows_a = adjustments(game_id, away)
    off_h, def_h, st_h, rows_h = adjustments(game_id, home)
    hfa = NEUTRAL_HFA if neutral else HFA
    ra, rh = netpg(away), netpg(home)
    base_margin = REGRESS * (rh - ra) + hfa
    e_home = ((TEAMS[home][4] / games_of(home) + TEAMS[away][5] / games_of(away)) / 2
              + hfa / 2 - off_h + def_a + st_a / 2)
    e_away = ((TEAMS[away][4] / games_of(away) + TEAMS[home][5] / games_of(home)) / 2
              - hfa / 2 - off_a + def_h + st_h / 2)
    margin = e_home - e_away
    total = e_home + e_away
    return {
        "base_margin": base_margin,
        "margin": margin,
        "total": total,
        "e_home": e_home,
        "e_away": e_away,
        "off_h": off_h, "def_h": def_h, "st_h": st_h,
        "off_a": off_a, "def_a": def_a, "st_a": st_a,
        "rows_h": rows_h, "rows_a": rows_a,
    }


# ---------------------------------------------------------------------------
# 1) standings CSV + integrity checks
# ---------------------------------------------------------------------------
pf_sum = sum(v[4] for v in TEAMS.values())
pa_sum = sum(v[5] for v in TEAMS.values())
g_sum = sum(games_of(t) for t in TEAMS)
print("INTEGRITY: sum(PF)=%d sum(PA)=%d match=%s ; total team-games=%d (even=%s)"
      % (pf_sum, pa_sum, pf_sum == pa_sum, g_sum, g_sum % 2 == 0))

with open(os.path.join(DATA, "2026-standings.csv"), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["team_key", "team", "W", "L", "T", "games", "PF", "PA", "net_pts",
                 "PF_pg", "PA_pg", "net_pg", "win_pct", "streak", "source_url"])
    for tk in sorted(TEAMS, key=lambda k: (-winpct(k), -netpg(k))):
        name, w, l, t, pf, pa, strk = TEAMS[tk]
        g = games_of(tk)
        wr.writerow([tk, name, w, l, t, g, pf, pa, pf - pa,
                     round(pf / g, 2), round(pa / g, 2), round(netpg(tk), 2),
                     round(winpct(tk), 3), strk, STANDINGS_URL])

# ---------------------------------------------------------------------------
# 2) games CSVs
# ---------------------------------------------------------------------------

def write_games(path, games, byes, sched_url):
    with open(path, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["game_id", "away", "home", "date", "time_et", "tv", "note",
                     "source_url"])
        for gid, a, h, d, tm, tv, note in games:
            wr.writerow([gid, TEAMS[a][0], TEAMS[h][0], d, tm, tv, note, sched_url])
        for b in byes:
            wr.writerow(["BYE", "", TEAMS[b][0], "", "", "", "Bye week", sched_url])


write_games(os.path.join(DATA, "2026-week10-games.csv"), GAMES_W10, BYES_W10, W10_SCHED_URL)
write_games(os.path.join(DATA, "2026-week11-games.csv"), GAMES_W11, BYES_W11, W11_SCHED_URL)

# ---------------------------------------------------------------------------
# 3) injuries CSV (every official-report row) + deficiency tracker
# ---------------------------------------------------------------------------
with open(os.path.join(DATA, "2026-week10-injuries.csv"), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["game_id", "team", "player", "position", "side", "injury", "status",
                 "depth_tier", "expected_replacement", "replacement_tier",
                 "source_url", "tier_source_url", "flag"])
    for gid, tm, player, pos, inj, status in sorted(INJURIES, key=lambda r: (r[0], r[1], r[5], r[2])):
        tier, repl, rtier, url, note = CHART.get((tm, player), (None, "", None, "", ""))
        flag = note
        if tier is None and not note:
            flag = "tier unverified — club depth chart not integrated for this team"
        src = EXTRA_SRC.get((tm, player), W10_REPORT_URL)
        if (tm, player) in EXTRA_SRC:
            flag = ("NOT on the weekly game-status report (IR/season-ending) — "
                    "sourced from team-statement reporting + club chart" + (" | " + flag if flag else ""))
        wr.writerow([gid, TEAMS[tm][0], player, pos, pos_side(pos), inj, status,
                     tier if tier is not None else "",
                     repl, rtier if rtier is not None else "",
                     src, url, flag])

with open(os.path.join(DATA, "2026-week10-depth-deficiencies.csv"), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["team", "side", "position", "player_out", "player_status",
                 "player_tier", "expected_replacement", "replacement_tier",
                 "deficiency_points", "source_url", "tier_source_url", "flag"])
    for gid, tm, player, pos, inj, status in sorted(INJURIES, key=lambda r: (r[1], r[5], r[2])):
        if status == "QUESTIONABLE":
            continue  # tracker focuses on OUT/DOUBTFUL absences
        tier, repl, rtier, url, note = CHART.get((tm, player), (None, "", None, "", ""))
        base = BASE_WEIGHT.get(pos, 0.5)
        w = base * TIER_MULT[tier] * STATUS_MULT[status]
        flag = note
        if tier is None and not note:
            flag = "tier/replacement unverified — club depth chart not integrated"
        src = EXTRA_SRC.get((tm, player), W10_REPORT_URL)
        if (tm, player) in EXTRA_SRC:
            flag = ("NOT on the weekly game-status report (IR/season-ending) — "
                    "sourced from team-statement reporting + club chart" + (" | " + flag if flag else ""))
        wr.writerow([TEAMS[tm][0], pos_side(pos), pos, player, status,
                     tier if tier is not None else "",
                     repl, rtier if rtier is not None else "",
                     round(w, 3), src, url, flag])

# ---------------------------------------------------------------------------
# 4) correlations computed from verified standings
# ---------------------------------------------------------------------------
pfg = [TEAMS[t][4] / games_of(t) for t in TEAMS]
pag = [TEAMS[t][5] / games_of(t) for t in TEAMS]
netg = [netpg(t) for t in TEAMS]
wp = [winpct(t) for t in TEAMS]
R = {
    ("PF_pg", "PA_pg"): pearson(pfg, pag),
    ("PF_pg", "win_pct"): pearson(pfg, wp),
    ("PA_pg", "win_pct"): pearson(pag, wp),
    ("net_pg", "win_pct"): pearson(netg, wp),
    ("PF_pg", "net_pg"): pearson(pfg, netg),
    ("PA_pg", "net_pg"): pearson(pag, netg),
}
# Pythagorean exponent fit on PF/PA vs win%
best_x, best_err = None, 1e9
x = 1.0
while x <= 20.0001:
    err = 0.0
    for t in TEAMS:
        _, w, l, tt, pf, pa, _ = TEAMS[t]
        g = w + l + tt
        pred = pf ** x / (pf ** x + pa ** x)
        err += (pred - winpct(t)) ** 2
    if err < best_err:
        best_x, best_err = x, err
    x += 0.1

with open(os.path.join(DATA, "correlation-matrix.csv"), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["metric_a", "metric_b", "pearson_r", "n", "basis", "source_url", "flag"])
    for (a, b), r in R.items():
        wr.writerow([a, b, round(r, 4), 32,
                     "2026 NFL team-level aggregates (through TNF Wk10)", STANDINGS_URL, ""])
    wr.writerow(["pythagorean_exponent", "win_pct fit", round(best_x, 1), 32,
                 "best-fit exponent minimizing MSE of PF^x/(PF^x+PA^x) vs win%%",
                 STANDINGS_URL, ""])
    wr.writerow(["parlay_leg_outcomes_same_game", "", "", "",
                 "requires game-level results", "",
                 "UNVERIFIED — data not yet ingested (see requirements Q6)"])
    wr.writerow(["player_props_same_game", "", "", "",
                 "requires player-level stats", "",
                 "UNVERIFIED — data not yet ingested (see requirements Q7)"])
    wr.writerow(["injury_signal_vs_line_move", "", "", "",
                 "requires market line history", "",
                 "UNVERIFIED — line history feed not integrated (see requirements Q5)"])

print("CORRELATIONS:",
      {f"{a}~{b}": round(r, 4) for (a, b), r in R.items()})
print("PYTHAGOREAN best exponent x=%.1f (MSE=%.4f)" % (best_x, best_err / 32))

# ---------------------------------------------------------------------------
# 5) originated lines vs market
# ---------------------------------------------------------------------------
line_rows = []
print("\nORIGINATED LINES — Week 10 (model output, v0.1)")
for gid, away, home, d, tm, tv, note in GAMES_W10:
    if gid == "W10-01":
        continue  # already played (result recorded separately)
    neutral = "neutral" in note.lower()
    m = model_game(gid, away, home, neutral)
    msp = half(m["margin"])
    mtot = half(m["total"])
    mspr, mt, mkt_src, rng, mflag = MARKET[gid]
    # market implied home margin = -mspr ; edge = model margin - market margin
    edge_spread = round(msp + mspr, 2)
    edge_total = round(mtot - mt, 2)
    line_rows.append({
        "gid": gid, "away": away, "home": home, "msp": msp, "mtot": mtot,
        "m": m, "mspr": mspr, "mt": mt, "mkt_src": mkt_src,
        "rng": rng, "mflag": mflag, "es": edge_spread, "et": edge_total,
        "neutral": neutral,
    })
    print(f"{gid} {TEAMS[away][0]} @ {TEAMS[home][0]}: model margin(home)={msp:+.1f} "
          f"total={mtot:.1f} | market home_spread={mspr:+.1f} total={mt:.1f} | "
          f"edge_spread={edge_spread:+.1f} edge_total={edge_total:+.1f} "
          f"| adj off/def/st home={m['off_h']:.2f}/{m['def_h']:.2f}/{m['st_h']:.2f} "
          f"away={m['off_a']:.2f}/{m['def_a']:.2f}/{m['st_a']:.2f}")

with open(os.path.join(DATA, "2026-week10-lines.csv"), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["game_id", "away", "home", "model_home_margin", "model_total",
                 "market_home_spread", "market_total",
                 "edge_spread_pts(model_margin-minus-market_margin)",
                 "edge_total_pts(model-minus-market)", "inj_adj_home_off",
                 "inj_adj_home_def", "inj_adj_away_off", "inj_adj_away_def",
                 "market_source_url", "market_range_other_books", "flag"])
    for r in line_rows:
        m = r["m"]
        wr.writerow([r["gid"], TEAMS[r["away"]][0], TEAMS[r["home"]][0],
                     r["msp"], r["mtot"], r["mspr"], r["mt"], r["es"], r["et"],
                     round(m["off_h"], 3), round(m["def_h"], 3),
                     round(m["off_a"], 3), round(m["def_a"], 3),
                     r["mkt_src"], r["rng"], r["mflag"]])

# deficiency scoreboard (OUT/DOUBTFUL only)
defs = {}
for gid, tm, player, pos, inj, status in INJURIES:
    if status == "QUESTIONABLE":
        continue
    tier, repl, rtier, url, note = CHART.get((tm, player), (None, "", None, "", ""))
    w = BASE_WEIGHT.get(pos, 0.5) * TIER_MULT[tier] * STATUS_MULT[status]
    key = (tm, pos_side(pos))
    defs[key] = defs.get(key, 0.0) + w

print("\nDEFICIENCY SCORES (OUT/DOUBTFUL weight sums, design units):")
for (tm, side), v in sorted(defs.items(), key=lambda kv: -kv[1])[:12]:
    print(f"  {TEAMS[tm][0]:28s} {side:4s} {v:.2f}")

print("\nWrote CSVs to data/. Done.")
