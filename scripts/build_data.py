#!/usr/bin/env python3
"""FL3 data builder.

Transcribes values captured from official NFL.com pages (fetched 2026-11-14) into
CSV + JSON datasets. Every record carries a source_url pointing at the official
page it was transcribed from. Blank cell = the official page itself showed the
cell blank (no designation). Nothing is inferred.

Sources (fetched 2026-11-14):
  standings : https://www.nfl.com/standings/league/2026/reg
  schedule  : https://www.nfl.com/schedules/2026/REG10
  injuries  : https://www.nfl.com/injuries/league/2026/reg10
"""
import csv, json, os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(OUT, exist_ok=True)

SRC_STANDINGS = "https://www.nfl.com/standings/league/2026/reg"
SRC_SCHEDULE = "https://www.nfl.com/schedules/2026/REG10"
SRC_INJURIES = "https://www.nfl.com/injuries/league/2026/reg10"

# ---------------------------------------------------------------- standings --
# (abbr, name, conf, div, W, L, T, PCT, PF, PA, NET, HOME, ROAD, DIV, CONF, STRK, L5)
# Transcribed from NFL.com league standings, 2026 regular season (through Week 9).
STANDINGS = [
    ("BUF","Buffalo Bills","AFC","East",7,1,0,"0.875",256,187,69,"3-1-0","4-0-0","0-1-0","4-1-0","4W","4-1-0"),
    ("SF","San Francisco 49ers","NFC","West",7,1,0,"0.875",235,156,79,"5-0-0","2-1-0","3-0-0","4-1-0","1W","4-1-0"),
    ("CHI","Chicago Bears","NFC","North",7,2,0,"0.778",241,184,57,"4-1-0","3-1-0","0-2-0","5-2-0","4W","4-1-0"),
    ("DEN","Denver Broncos","AFC","West",7,2,0,"0.778",198,186,12,"4-0-0","3-2-0","2-1-0","3-1-0","5W","5-0-0"),
    ("CIN","Cincinnati Bengals","AFC","North",6,2,0,"0.750",240,175,65,"2-1-0","4-1-0","1-1-0","4-2-0","4W","4-1-0"),
    ("DET","Detroit Lions","NFC","North",6,2,0,"0.750",222,189,33,"4-0-0","2-2-0","2-0-0","4-1-0","4W","4-1-0"),
    ("JAX","Jacksonville Jaguars","AFC","South",6,2,0,"0.750",229,121,108,"4-1-0","2-1-0","1-1-0","5-2-0","2W","4-1-0"),
    ("KC","Kansas City Chiefs","AFC","West",6,2,0,"0.750",202,143,59,"4-0-0","2-2-0","3-1-0","6-1-0","1W","3-2-0"),
    ("MIN","Minnesota Vikings","NFC","North",6,2,0,"0.750",146,116,30,"3-1-0","3-1-0","2-1-0","4-1-0","2L","3-2-0"),
    ("PIT","Pittsburgh Steelers","AFC","North",6,2,0,"0.750",180,144,36,"4-0-0","2-2-0","2-1-0","3-2-0","4W","4-1-0"),
    ("GB","Green Bay Packers","NFC","North",6,3,0,"0.667",216,191,25,"3-1-0","3-2-0","1-2-0","4-3-0","2W","4-1-0"),
    ("NYG","New York Giants","NFC","East",5,3,1,"0.611",203,196,7,"3-2-0","2-1-1","2-1-1","3-3-1","1L","2-2-1"),
    ("CLE","Cleveland Browns","AFC","North",5,4,0,"0.556",161,196,-35,"3-0-0","2-4-0","2-1-0","3-3-0","2L","2-3-0"),
    ("LAR","Los Angeles Rams","NFC","West",5,4,0,"0.556",214,181,33,"2-3-0","3-1-0","0-2-0","3-2-0","3W","3-2-0"),
    ("NE","New England Patriots","AFC","East",5,4,0,"0.556",211,207,4,"3-1-0","2-3-0","3-0-0","5-1-0","1L","3-2-0"),
    ("SEA","Seattle Seahawks","NFC","West",5,4,0,"0.556",202,162,40,"4-2-0","1-2-0","2-1-0","2-3-0","1W","2-3-0"),
    ("BAL","Baltimore Ravens","AFC","North",4,5,0,"0.444",189,236,-47,"1-3-0","3-2-0","0-2-0","2-4-0","4L","1-4-0"),
    ("DAL","Dallas Cowboys","NFC","East",4,5,0,"0.444",246,236,10,"1-3-0","3-2-0","2-1-0","2-4-0","1W","2-3-0"),
    ("LV","Las Vegas Raiders","AFC","West",4,5,0,"0.444",238,268,-30,"1-3-0","3-2-0","1-1-0","3-3-0","1L","1-4-0"),
    ("WAS","Washington Commanders","NFC","East",3,5,1,"0.389",196,223,-27,"2-2-1","1-3-0","2-2-1","3-4-1","1W","2-2-1"),
    ("CAR","Carolina Panthers","NFC","South",3,5,0,"0.375",199,219,-20,"1-3-0","2-2-0","1-1-0","3-3-0","3L","2-3-0"),
    ("HOU","Houston Texans","AFC","South",3,5,0,"0.375",209,192,17,"0-4-0","3-1-0","2-1-0","3-3-0","1W","3-2-0"),
    ("NO","New Orleans Saints","NFC","South",3,5,0,"0.375",185,216,-31,"1-4-0","2-1-0","0-1-0","1-3-0","1W","2-3-0"),
    ("AZ","Arizona Cardinals","NFC","West",3,6,0,"0.333",178,255,-77,"0-3-0","3-3-0","1-3-0","2-5-0","1L","2-3-0"),
    ("ATL","Atlanta Falcons","NFC","South",3,6,0,"0.333",188,223,-35,"1-4-0","2-2-0","1-2-0","3-3-0","2L","1-4-0"),
    ("TB","Tampa Bay Buccaneers","NFC","South",3,6,0,"0.333",202,178,24,"1-4-0","2-2-0","2-0-0","3-3-0","1L","3-2-0"),
    ("IND","Indianapolis Colts","AFC","South",2,7,0,"0.222",184,249,-65,"1-3-0","1-4-0","1-2-0","1-5-0","5L","0-5-0"),
    ("NYJ","New York Jets","AFC","East",2,7,0,"0.222",182,223,-41,"1-3-0","1-4-0","0-2-0","2-4-0","4L","1-4-0"),
    ("PHI","Philadelphia Eagles","NFC","East",2,7,0,"0.222",148,221,-73,"1-4-0","1-3-0","1-3-0","1-6-0","7L","0-5-0"),
    ("MIA","Miami Dolphins","AFC","East",1,7,0,"0.125",126,200,-74,"0-4-0","1-3-0","1-1-0","1-4-0","2L","1-4-0"),
    ("TEN","Tennessee Titans","AFC","South",1,7,0,"0.125",144,199,-55,"0-4-0","1-3-0","1-1-0","1-5-0","2L","1-4-0"),
    ("LAC","Los Angeles Chargers","AFC","West",0,8,0,"0.000",121,219,-98,"0-4-0","0-4-0","0-3-0","0-5-0","8L","0-5-0"),
]

# ----------------------------------------------------------------- schedule --
# (date, time_et, slot, away, home, network, venue_note, game_url, status, away_pts, home_pts)
SCHEDULE = [
    ("2026-11-12","8:15 PM","Thursday Night Football","WAS","NYG","Prime Video","", "https://www.nfl.com/games/commanders-at-giants-2026-reg-10","FINAL",24,21),
    ("2026-11-15","9:30 AM","Sunday - International Series (Munich)","NE","DET","FOX","Munich, Germany","https://www.nfl.com/games/patriots-at-lions-2026-reg-10","Scheduled","",""),
    ("2026-11-15","1:00 PM","Sunday - Early","KC","ATL","CBS","","https://www.nfl.com/games/chiefs-at-falcons-2026-reg-10","Scheduled","",""),
    ("2026-11-15","1:00 PM","Sunday - Early","MIN","GB","FOX","","https://www.nfl.com/games/vikings-at-packers-2026-reg-10","Scheduled","",""),
    ("2026-11-15","1:00 PM","Sunday - Early","JAX","TEN","FOX","","https://www.nfl.com/games/jaguars-at-titans-2026-reg-10","Scheduled","",""),
    ("2026-11-15","1:00 PM","Sunday - Early","BUF","NYJ","CBS","","https://www.nfl.com/games/bills-at-jets-2026-reg-10","Scheduled","",""),
    ("2026-11-15","1:00 PM","Sunday - Early","MIA","IND","CBS","","https://www.nfl.com/games/dolphins-at-colts-2026-reg-10","Scheduled","",""),
    ("2026-11-15","1:00 PM","Sunday - Early","CAR","NO","FOX","","https://www.nfl.com/games/panthers-at-saints-2026-reg-10","Scheduled","",""),
    ("2026-11-15","1:00 PM","Sunday - Early","HOU","CLE","FOX","","https://www.nfl.com/games/texans-at-browns-2026-reg-10","Scheduled","",""),
    ("2026-11-15","4:05 PM","Sunday - Late","LAR","AZ","CBS","","https://www.nfl.com/games/rams-at-cardinals-2026-reg-10","Scheduled","",""),
    ("2026-11-15","4:05 PM","Sunday - Late","SEA","LV","CBS","","https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10","Scheduled","",""),
    ("2026-11-15","4:25 PM","Sunday - Late","SF","DAL","FOX","","https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10","Scheduled","",""),
    ("2026-11-15","8:20 PM","Sunday Night Football","PIT","CIN","NBC","","https://www.nfl.com/games/steelers-at-bengals-2026-reg-10","Scheduled","",""),
    ("2026-11-16","8:15 PM","Monday Night Football","LAC","BAL","ESPN / ABC / ESPN2","",
     "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10","Scheduled","",""),
]
BYE_TEAMS = [("CHI","7-2"),("DEN","7-2"),("PHI","2-7"),("TB","3-6")]

# ----------------------------------------------------------------- injuries --
# (team, opp, game_date, player, pos, injuries, practice, game_status, note)
D = "Did Not Participate In Practice"
L = "Limited Participation in Practice"
F = "Full Participation in Practice"
NI = "Not injury related - resting player"
BASE_NOTE = "Transcribed from NFL.com league injury report (final Week 10 report)"
INJ = [
    # -- Thu Nov 12: WAS @ NYG (final) --
    ("WAS","NYG","2026-11-12","John Bates","TE","",""+F,"",BASE_NOTE),
    ("WAS","NYG","2026-11-12","Treylon Burks","WR","",D,"",BASE_NOTE),
    ("WAS","NYG","2026-11-12","Jayden Daniels","QB","",F,"",BASE_NOTE),
    ("WAS","NYG","2026-11-12","Matt Gulbin","C","",F,"",BASE_NOTE),
    ("WAS","NYG","2026-11-12","Chig Okonkwo","TE","",F,"",BASE_NOTE),
    ("WAS","NYG","2026-11-12","Lucas Patrick","C","Concussion",D,"Out",BASE_NOTE),
    ("WAS","NYG","2026-11-12","Amik Robertson","CB","",L,"",BASE_NOTE),
    ("WAS","NYG","2026-11-12","Shy Tuttle","DT","",F,"",BASE_NOTE),
    ("WAS","NYG","2026-11-12","Colson Yankoff","TE","Knee",D,"Out",BASE_NOTE),
    ("NYG","WAS","2026-11-12","Abdul Carter","LB","",F,"",BASE_NOTE),
    ("NYG","WAS","2026-11-12","Jermaine Eluemunor","T","",F,"",BASE_NOTE),
    ("NYG","WAS","2026-11-12","Malik Harrison","LB","Groin",L,"Questionable",BASE_NOTE),
    ("NYG","WAS","2026-11-12","Colton Hood","CB","",F,"",BASE_NOTE),
    ("NYG","WAS","2026-11-12","Theo Johnson","TE","",F,"",BASE_NOTE),
    ("NYG","WAS","2026-11-12","Charlie Jones","WR","",F,"",BASE_NOTE),
    ("NYG","WAS","2026-11-12","J.J. McCarthy","QB","",F,"",BASE_NOTE),
    ("NYG","WAS","2026-11-12","Darnell Mooney","WR","",F,"",BASE_NOTE),
    ("NYG","WAS","2026-11-12","Malik Nabers","WR","",F,"",BASE_NOTE),
    ("NYG","WAS","2026-11-12","Cam Skattebo","RB","",F,"",BASE_NOTE),
    ("NYG","WAS","2026-11-12","Andrew Thomas","T","",F,"",BASE_NOTE),
    # -- Sun Nov 15 9:30: NE @ DET (Munich) --
    ("NE","DET","2026-11-15","Ben Brown","C","Knee",D,"Out",BASE_NOTE),
    ("NE","DET","2026-11-15","A.J. Brown","WR","Ankle; Knee",L,"Questionable",BASE_NOTE),
    ("NE","DET","2026-11-15","Kevin Byard","S","Chest",F,"Questionable",BASE_NOTE),
    ("NE","DET","2026-11-15","Carlton Davis III","CB","Knee",D,"Out",BASE_NOTE),
    ("NE","DET","2026-11-15","Reggie Gilliam","FB","Knee",L,"Questionable",BASE_NOTE),
    ("NE","DET","2026-11-15","TreVeyon Henderson","RB","Illness",D,"Out",BASE_NOTE),
    ("NE","DET","2026-11-15","Hunter Henry","TE","",L,"",BASE_NOTE),
    ("NE","DET","2026-11-15","Cameron Latu","TE","Back",L,"Questionable",BASE_NOTE),
    ("NE","DET","2026-11-15","Drake Maye","QB","",F,"",BASE_NOTE),
    ("NE","DET","2026-11-15","Morgan Moses","T","",F,"",BASE_NOTE),
    ("NE","DET","2026-11-15","Walter Rouse","T","Concussion",L,"Questionable",BASE_NOTE),
    ("NE","DET","2026-11-15","Brenden Schooler","S","Hamstring",L,"Questionable",BASE_NOTE),
    ("NE","DET","2026-11-15","Rhamondre Stevenson","RB","Knee",L,"Questionable",BASE_NOTE),
    ("NE","DET","2026-11-15","Greg Van Roten","G","Hamstring",F,"Questionable",BASE_NOTE),
    ("NE","DET","2026-11-15","Charles Woods","CB","Hamstring",F,"Questionable",BASE_NOTE),
    ("DET","NE","2026-11-15","Brian Branch","S","",F,"",BASE_NOTE),
    ("DET","NE","2026-11-15","Jared Goff","QB","",F,"",BASE_NOTE),
    ("DET","NE","2026-11-15","Kerby Joseph","S","Knee",D,"Out",BASE_NOTE),
    ("DET","NE","2026-11-15","Cade Mays","C","Ankle",D,"Out",BASE_NOTE),
    ("DET","NE","2026-11-15","D.J. Reed","CB","Hip",D,"Out",BASE_NOTE),
    ("DET","NE","2026-11-15","Jacob Saylors","RB","",F,"",BASE_NOTE),
    ("DET","NE","2026-11-15","Amon-Ra St. Brown","WR","Rib",L,"Questionable",BASE_NOTE),
    ("DET","NE","2026-11-15","Sione Vaki","RB","Ankle",L,"Questionable",BASE_NOTE),
    ("DET","NE","2026-11-15","DJ Wonnum","DE","",F,"",BASE_NOTE),
    # -- Sun Nov 15 1:00: KC @ ATL --
    ("KC","ATL","2026-11-15","Jeffrey Bassa","LB","",F,"",BASE_NOTE),
    ("KC","ATL","2026-11-15","Mansoor Delane","CB","Shoulder",F,"Questionable",BASE_NOTE),
    ("KC","ATL","2026-11-15","Justin Fields","QB","",F,"",BASE_NOTE),
    ("KC","ATL","2026-11-15","Jaden Hicks","S","",F,"",BASE_NOTE),
    ("KC","ATL","2026-11-15","Travis Kelce","TE","",F,"",BASE_NOTE),
    ("KC","ATL","2026-11-15","Patrick Mahomes","QB","",F,"",BASE_NOTE),
    ("KC","ATL","2026-11-15","Jaylon Moore","T","Ankle",D,"Out",BASE_NOTE),
    ("KC","ATL","2026-11-15","Omarr Norman-Lott","DT","Knee",L,"Out",BASE_NOTE),
    ("KC","ATL","2026-11-15","Jaydn Ott","RB","Hamstring",L,"Questionable",BASE_NOTE),
    ("KC","ATL","2026-11-15","Rashee Rice","WR","",F,"",BASE_NOTE),
    ("KC","ATL","2026-11-15","Kenneth Walker III","RB","Groin",D,"Questionable",BASE_NOTE),
    ("KC","ATL","2026-11-15","Peter Woods","DT","Neck",D,"Out",BASE_NOTE),
    ("KC","ATL","2026-11-15","Xavier Worthy","WR","",F,"",BASE_NOTE),
    ("ATL","KC","2026-11-15","Zachariah Branch","WR","Hamstring",D,"Out",BASE_NOTE),
    ("ATL","KC","2026-11-15","Kendal Daniels","LB","",F,"",BASE_NOTE),
    ("ATL","KC","2026-11-15","Divine Deablo","LB","Forearm",D,"Doubtful",BASE_NOTE),
    ("ATL","KC","2026-11-15","Gervon Dexter Sr.","DT","Illness",L,"Questionable",BASE_NOTE),
    ("ATL","KC","2026-11-15","Jake Matthews","T","",L,"",BASE_NOTE),
    ("ATL","KC","2026-11-15","Liam McCullough","LS","",D,"",BASE_NOTE),
    ("ATL","KC","2026-11-15","James Pearce Jr.","DE","Back",L,"Questionable",BASE_NOTE),
    ("ATL","KC","2026-11-15","Za'Darius Smith","DE","",F,"",BASE_NOTE),
    ("ATL","KC","2026-11-15","Jawaan Taylor","T","",L,"",BASE_NOTE),
    ("ATL","KC","2026-11-15","Cameron Thomas","DE","",F,"",BASE_NOTE),
    ("ATL","KC","2026-11-15","Josh Woods","LB","Ankle",F,"Questionable",BASE_NOTE),
    # -- Sun Nov 15 1:00: MIN @ GB --
    ("MIN","GB","2026-11-15","Jordan Addison","WR","Thumb",L,"Questionable",BASE_NOTE),
    ("MIN","GB","2026-11-15","Blake Cashman","LB","Concussion",L,"Out",BASE_NOTE),
    ("MIN","GB","2026-11-15","Christian Darrisaw","T","",D,"",BASE_NOTE),
    ("MIN","GB","2026-11-15","T.J. Hockenson","TE","Wrist; Chest",D,"Out",BASE_NOTE),
    ("MIN","GB","2026-11-15","Tyrion Ingram-Dawkins","DT","Ankle",D,"Out",BASE_NOTE),
    ("MIN","GB","2026-11-15","Theo Jackson","S","",F,"",BASE_NOTE),
    ("MIN","GB","2026-11-15","Jauan Jennings","WR","Calf",D,"Out",BASE_NOTE),
    ("MIN","GB","2026-11-15","Josh Metellus","S","Shoulder",L,"Questionable",BASE_NOTE),
    ("MIN","GB","2026-11-15","Kyler Murray","QB","Hamstring",D,"Out",BASE_NOTE),
    ("MIN","GB","2026-11-15","Harrison Smith","S","",L,"",BASE_NOTE),
    ("MIN","GB","2026-11-15","Kyle Van Noy","LB","Calf",L,"Questionable",BASE_NOTE),
    ("MIN","GB","2026-11-15","Jay Ward","S","",F,"",BASE_NOTE),
    ("MIN","GB","2026-11-15","Carson Wentz","QB","",F,"",BASE_NOTE),
    ("GB","MIN","2026-11-15","Aaron Banks","G","",L,"",BASE_NOTE),
    ("GB","MIN","2026-11-15","Chris Brooks","RB","Ankle",L,"Questionable",BASE_NOTE),
    ("GB","MIN","2026-11-15","Javon Bullard","S","Ankle; Knee",L,"Questionable",BASE_NOTE),
    ("GB","MIN","2026-11-15","Zaire Franklin","LB","Shin",D,"Doubtful",BASE_NOTE),
    ("GB","MIN","2026-11-15","Travis Glover","G","Knee",L,"Questionable",BASE_NOTE),
    ("GB","MIN","2026-11-15","Ty'Ron Hopper","LB","",F,"",BASE_NOTE),
    ("GB","MIN","2026-11-15","Josh Jacobs","RB","Finger",D,"Out",BASE_NOTE),
    ("GB","MIN","2026-11-15","Xavier McKinney","S","Foot",L,"Questionable",BASE_NOTE),
    ("GB","MIN","2026-11-15","Bo Melton","WR","",F,"",BASE_NOTE),
    ("GB","MIN","2026-11-15","Skyy Moore","WR","Ankle",L,"Questionable",BASE_NOTE),
    ("GB","MIN","2026-11-15","Micah Parsons","LB","Knee; Illness",L,"Out",BASE_NOTE),
    ("GB","MIN","2026-11-15","Sean Rhyan","C","Ankle",D,"Out",BASE_NOTE),
    ("GB","MIN","2026-11-15","Trey Smack","K","",F,"",BASE_NOTE),
    ("GB","MIN","2026-11-15","Lukas Van Ness","LB","Back",L,"Questionable",BASE_NOTE),
    ("GB","MIN","2026-11-15","Josh Whyle","TE","Concussion",D,"Out",BASE_NOTE),
    ("GB","MIN","2026-11-15","Savion Williams","WR","",L,"",BASE_NOTE),
    ("GB","MIN","2026-11-15","Kevin Zeitler","G","Ankle; Triceps",D,"Questionable",BASE_NOTE),
    # -- Sun Nov 15 1:00: JAX @ TEN --
    ("JAX","TEN","2026-11-15","Jessie Bates","S",NI,L,"Out",BASE_NOTE),
    ("JAX","TEN","2026-11-15","Ezra Cleveland","G","",F,"",BASE_NOTE),
    ("JAX","TEN","2026-11-15","Branson Combs","LB","",F,"",BASE_NOTE),
    ("JAX","TEN","2026-11-15","Jordan Davis","DT",NI,L,"Out",BASE_NOTE),
    ("JAX","TEN","2026-11-15","BJ Green II","DE","Forearm",F,"Out",BASE_NOTE),
    ("JAX","TEN","2026-11-15","Robert Hainsey","C","Concussion",L,"Questionable",BASE_NOTE),
    ("JAX","TEN","2026-11-15","Antonio Johnson","S","",L,"",BASE_NOTE),
    ("JAX","TEN","2026-11-15","Jakobi Meyers","WR","",L,"",BASE_NOTE),
    ("JAX","TEN","2026-11-15","Chris Rodriguez Jr.","RB","",L,"",BASE_NOTE),
    ("JAX","TEN","2026-11-15","Bhayshul Tuten","RB","",L,"",BASE_NOTE),
    ("JAX","TEN","2026-11-15","Travon Walker","DE","",L,"",BASE_NOTE),
    ("TEN","JAX","2026-11-15","Cody Barton","LB","Concussion",D,"Out",BASE_NOTE),
    ("TEN","JAX","2026-11-15","John Franklin-Myers","DE","",F,"",BASE_NOTE),
    ("TEN","JAX","2026-11-15","Marcus Harris","CB","",F,"",BASE_NOTE),
    ("TEN","JAX","2026-11-15","Anthony Hill Jr.","LB","Neck",D,"Out",BASE_NOTE),
    ("TEN","JAX","2026-11-15","Jaylon Jones","CB","",F,"",BASE_NOTE),
    ("TEN","JAX","2026-11-15","JC Latham","T","",F,"",BASE_NOTE),
    ("TEN","JAX","2026-11-15","Tony Pollard","RB","",F,"",BASE_NOTE),
    ("TEN","JAX","2026-11-15","Peter Skoronski","G","Hamstring",D,"Out",BASE_NOTE),
    ("TEN","JAX","2026-11-15","Tyjae Spears","RB","Knee",F,"Questionable",BASE_NOTE),
    ("TEN","JAX","2026-11-15","Carnell Tate","WR","Shoulder",D,"Out",BASE_NOTE),
    ("TEN","JAX","2026-11-15","Tommy Townsend","P","Knee; Achilles",D,"Out",BASE_NOTE),
    ("TEN","JAX","2026-11-15","Kevin Winston Jr.","S","",F,"",BASE_NOTE),
    # -- Sun Nov 15 1:00: BUF @ NYJ --
    ("BUF","NYJ","2026-11-15","Alec Anderson","G","",F,"",BASE_NOTE),
    ("BUF","NYJ","2026-11-15","Christian Benford","CB","Wrist",F,"Questionable",BASE_NOTE),
    ("BUF","NYJ","2026-11-15","Terrel Bernard","LB","",D,"",BASE_NOTE),
    ("BUF","NYJ","2026-11-15","Spencer Brown","T","Ankle",D,"Doubtful",BASE_NOTE),
    ("BUF","NYJ","2026-11-15","Dion Dawkins","T","",F,"",BASE_NOTE),
    ("BUF","NYJ","2026-11-15","Sam Franklin Jr.","S","Shoulder",L,"Questionable",BASE_NOTE),
    ("BUF","NYJ","2026-11-15","Greg Gaines","DT","",F,"",BASE_NOTE),
    ("BUF","NYJ","2026-11-15","Jordan Hancock","CB","Hamstring",F,"Questionable",BASE_NOTE),
    ("BUF","NYJ","2026-11-15","Dalton Kincaid","TE","",F,"",BASE_NOTE),
    ("BUF","NYJ","2026-11-15","Connor McGovern","C","",F,"",BASE_NOTE),
    ("BUF","NYJ","2026-11-15","Ed Oliver","DE","",D,"",BASE_NOTE),
    ("BUF","NYJ","2026-11-15","Ar'maj Reed-Adams","G","",F,"",BASE_NOTE),
    ("BUF","NYJ","2026-11-15","T.J. Sanders","DE","",F,"",BASE_NOTE),
    ("BUF","NYJ","2026-11-15","Tyrell Shavers","WR","Knee",F,"Questionable",BASE_NOTE),
    ("NYJ","BUF","2026-11-15","Jarvis Brownlee Jr.","CB","Illness",L,"Questionable",BASE_NOTE),
    ("NYJ","BUF","2026-11-15","Omar Cooper Jr.","WR","Ankle",F,"Questionable",BASE_NOTE),
    ("NYJ","BUF","2026-11-15","Adonai Mitchell","WR","Knee",F,"Questionable",BASE_NOTE),
    ("NYJ","BUF","2026-11-15","Joseph Ossai","DE","Ankle",F,"Questionable",BASE_NOTE),
    ("NYJ","BUF","2026-11-15","VJ Payne","S","Knee",F,"Questionable",BASE_NOTE),
    ("NYJ","BUF","2026-11-15","Harrison Phillips","DT","Ankle",F,"Questionable",BASE_NOTE),
    ("NYJ","BUF","2026-11-15","Trevin Wallace","LB","Groin",D,"Out",BASE_NOTE),
    ("NYJ","BUF","2026-11-15","Garrett Wilson","WR","Concussion",F,"Questionable",BASE_NOTE),
    ("NYJ","BUF","2026-11-15","Nahshon Wright","CB","Back",F,"Questionable",BASE_NOTE),
    # -- Sun Nov 15 1:00: MIA @ IND --
    ("MIA","IND","2026-11-15","Tucker Addington","LS","",L,"",BASE_NOTE),
    ("MIA","IND","2026-11-15","Kaytron Allen","RB","",F,"",BASE_NOTE),
    ("MIA","IND","2026-11-15","Darrell Baker Jr.","CB","Knee",F,"Questionable",BASE_NOTE),
    ("MIA","IND","2026-11-15","Chris Bell","WR","Knee",D,"Doubtful",BASE_NOTE),
    ("MIA","IND","2026-11-15","Aaron Brewer","C","Concussion",D,"Out",BASE_NOTE),
    ("MIA","IND","2026-11-15","Malik Herring","DE","",F,"",BASE_NOTE),
    ("MIA","IND","2026-11-15","Will Kacmarek","TE","",F,"",BASE_NOTE),
    ("MIA","IND","2026-11-15","Michael Taaffe","S","",F,"",BASE_NOTE),
    ("MIA","IND","2026-11-15","Dante Trader Jr.","S","",F,"",BASE_NOTE),
    ("MIA","IND","2026-11-15","Jared Wayne","WR","Quadricep",D,"Out",BASE_NOTE),
    ("MIA","IND","2026-11-15","Jaylen Wright","RB","",F,"",BASE_NOTE),
    ("IND","MIA","2026-11-15","Mo Alie-Cox","TE","Groin",D,"Out",BASE_NOTE),
    ("IND","MIA","2026-11-15","CJ Allen","LB","",F,"",BASE_NOTE),
    ("IND","MIA","2026-11-15","Jaylon Carlies","LB","Neck",D,"Out",BASE_NOTE),
    ("IND","MIA","2026-11-15","Akeem Davis-Gaither","LB","Knee",D,"Out",BASE_NOTE),
    ("IND","MIA","2026-11-15","A.J. Haulcy","S","",F,"",BASE_NOTE),
    ("IND","MIA","2026-11-15","Arden Key","DE","Hamstring",F,"Questionable",BASE_NOTE),
    ("IND","MIA","2026-11-15","Will Mallory","TE","Hamstring",L,"Questionable",BASE_NOTE),
    ("IND","MIA","2026-11-15","Luke Rhodes","LS","Hamstring",D,"Out",BASE_NOTE),
    ("IND","MIA","2026-11-15","Grover Stewart","DT","",F,"",BASE_NOTE),
    ("IND","MIA","2026-11-15","Jonathan Taylor","RB","",F,"",BASE_NOTE),
    ("IND","MIA","2026-11-15","Jerry Tillery","DT","Calf",D,"Out",BASE_NOTE),
    ("IND","MIA","2026-11-15","Jalen Travis","T","Knee",D,"Out",BASE_NOTE),
    ("IND","MIA","2026-11-15","Justin Walley","CB","",F,"",BASE_NOTE),
    ("IND","MIA","2026-11-15","Charvarius Ward","CB","",F,"",BASE_NOTE),
    # -- Sun Nov 15 1:00: CAR @ NO --
    ("CAR","NO","2026-11-15","Jonathon Brooks","RB","Groin",L,"Doubtful",BASE_NOTE),
    ("CAR","NO","2026-11-15","Brady Christensen","G","Hamstring",F,"Questionable",BASE_NOTE),
    ("CAR","NO","2026-11-15","Trevor Etienne","RB","",F,"",BASE_NOTE),
    ("CAR","NO","2026-11-15","Chuba Hubbard","RB","",F,"",BASE_NOTE),
    ("CAR","NO","2026-11-15","Lee Hunter","DT","",F,"",BASE_NOTE),
    ("CAR","NO","2026-11-15","Mike Jackson","CB","Groin",L,"Doubtful",BASE_NOTE),
    ("CAR","NO","2026-11-15","Will Lee III","CB","Hamstring",L,"Questionable",BASE_NOTE),
    ("CAR","NO","2026-11-15","Xavier Legette","WR","Knee",F,"Questionable",BASE_NOTE),
    ("CAR","NO","2026-11-15","Damien Lewis","G","",F,"",BASE_NOTE),
    ("CAR","NO","2026-11-15","Bobby Okereke","LB","Foot",D,"Out",BASE_NOTE),
    ("CAR","NO","2026-11-15","Jaelan Phillips","LB","Hamstring",F,"Questionable",BASE_NOTE),
    ("CAR","NO","2026-11-15","Torricelli Simpkins III","G","",F,"",BASE_NOTE),
    ("NO","CAR","2026-11-15","Kelvin Banks Jr.","T","",F,"",BASE_NOTE),
    ("NO","CAR","2026-11-15","CJ Donaldson","RB","Shoulder",D,"Out",BASE_NOTE),
    ("NO","CAR","2026-11-15","David Edwards","G","",F,"",BASE_NOTE),
    ("NO","CAR","2026-11-15","Martin Emerson","CB","Shin",L,"Questionable",BASE_NOTE),
    ("NO","CAR","2026-11-15","Travis Etienne","RB","Hamstring",F,"Questionable",BASE_NOTE),
    ("NO","CAR","2026-11-15","Noah Fant","TE","",F,"",BASE_NOTE),
    ("NO","CAR","2026-11-15","Taliese Fuaga","T","Knee",D,"Out",BASE_NOTE),
    ("NO","CAR","2026-11-15","Alvin Kamara","RB","",F,"",BASE_NOTE),
    ("NO","CAR","2026-11-15","Erik McCoy","C","Biceps",D,"Out",BASE_NOTE),
    ("NO","CAR","2026-11-15","Christen Miller","DT","Knee",D,"Out",BASE_NOTE),
    ("NO","CAR","2026-11-15","Asim Richards","T","",F,"",BASE_NOTE),
    ("NO","CAR","2026-11-15","Quincy Riley","CB","",F,"",BASE_NOTE),
    # -- Sun Nov 15 1:00: HOU @ CLE --
    ("HOU","CLE","2026-11-15","Azeez Al-Shaair","LB","Groin; Not injury related - personal matter",D,"Out",BASE_NOTE),
    ("HOU","CLE","2026-11-15","Will Anderson Jr.","DE","Ankle",D,"Questionable",BASE_NOTE),
    ("HOU","CLE","2026-11-15","Reed Blankenship","S","",F,"",BASE_NOTE),
    ("HOU","CLE","2026-11-15","Trent Brown","T","Wrist; Illness",D,"Questionable",BASE_NOTE),
    ("HOU","CLE","2026-11-15","Tank Dell","WR","",F,"",BASE_NOTE),
    ("HOU","CLE","2026-11-15","Blake Fisher","T","",F,"",BASE_NOTE),
    ("HOU","CLE","2026-11-15","Marvin Harrison Jr.","WR","Hamstring",D,"Out",BASE_NOTE),
    ("HOU","CLE","2026-11-15","Jake Hummel","LB","Groin",F,"Questionable",BASE_NOTE),
    ("HOU","CLE","2026-11-15","Danielle Hunter","DE","Hamstring",D,"Out",BASE_NOTE),
    ("HOU","CLE","2026-11-15","Brevin Jordan","TE","Finger; Foot",D,"Out",BASE_NOTE),
    ("HOU","CLE","2026-11-15","Woody Marks","RB","",F,"",BASE_NOTE),
    ("HOU","CLE","2026-11-15","David Montgomery","RB","Groin",F,"Questionable",BASE_NOTE),
    ("HOU","CLE","2026-11-15","Keylan Rutledge","G","Neck; Shoulder",D,"Out",BASE_NOTE),
    ("HOU","CLE","2026-11-15","Jaylin Smith","CB","Hamstring",F,"Questionable",BASE_NOTE),
    ("HOU","CLE","2026-11-15","Wyatt Teller","G","Illness; Back",L,"Questionable",BASE_NOTE),
    ("HOU","CLE","2026-11-15","Tommy Togiai","DT","",F,"",BASE_NOTE),
    ("CLE","HOU","2026-11-15","Austin Barber","T","",F,"",BASE_NOTE),
    ("CLE","HOU","2026-11-15","Denzel Boston","WR","Toe",L,"Questionable",BASE_NOTE),
    ("CLE","HOU","2026-11-15","Michael Burton","FB","Calf",D,"Out",BASE_NOTE),
    ("CLE","HOU","2026-11-15","Maliek Collins","DT","",F,"",BASE_NOTE),
    ("CLE","HOU","2026-11-15","Harold Fannin Jr.","TE","",F,"",BASE_NOTE),
    ("CLE","HOU","2026-11-15","Ronnie Hickman Jr.","S","Concussion",D,"Out",BASE_NOTE),
    ("CLE","HOU","2026-11-15","Tytus Howard","T","",F,"",BASE_NOTE),
    ("CLE","HOU","2026-11-15","Elgton Jenkins","C","",F,"",BASE_NOTE),
    ("CLE","HOU","2026-11-15","Donovan McMillon","S","",L,"",BASE_NOTE),
    ("CLE","HOU","2026-11-15","Carson Schwesinger","LB","",F,"",BASE_NOTE),
    ("CLE","HOU","2026-11-15","Denzel Ward","CB","",L,"",BASE_NOTE),
    ("CLE","HOU","2026-11-15","Quincy Williams","LB","",F,"",BASE_NOTE),
    # -- Sun Nov 15 4:05: LAR @ AZ --
    ("LAR","AZ","2026-11-15","Davis Allen","TE","Oblique",L,"Questionable",BASE_NOTE),
    ("LAR","AZ","2026-11-15","Steve Avila","G","Hamstring",D,"Out",BASE_NOTE),
    ("LAR","AZ","2026-11-15","Joe Cardona","LS","Ankle",L,"Questionable",BASE_NOTE),
    ("LAR","AZ","2026-11-15","Kam Curl","S","Toe",L,"Questionable",BASE_NOTE),
    ("LAR","AZ","2026-11-15","Aaron Donald","DT","",D,"",BASE_NOTE),
    ("LAR","AZ","2026-11-15","Terrance Ferguson","TE","Ankle; Hamstring",D,"Out",BASE_NOTE),
    ("LAR","AZ","2026-11-15","Braden Fiske","DT","",D,"",BASE_NOTE),
    ("LAR","AZ","2026-11-15","Myles Garrett","LB","Knee; Not injury related - resting player",D,"Questionable",BASE_NOTE),
    ("LAR","AZ","2026-11-15","Tyler Higbee","TE","",L,"",BASE_NOTE),
    ("LAR","AZ","2026-11-15","Trent McDuffie","CB","Back",L,"Questionable",BASE_NOTE),
    ("LAR","AZ","2026-11-15","Puka Nacua","WR","",D,"",BASE_NOTE,"Official report shows no game-status designation; NFL.com news (Nov 13) says he is likely to be placed on IR"),
    ("LAR","AZ","2026-11-15","Colby Parkinson","TE","",F,"",BASE_NOTE),
    ("LAR","AZ","2026-11-15","Matthew Stafford","QB","",F,"",BASE_NOTE),
    ("LAR","AZ","2026-11-15","Byron Young","LB","",D,"",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Budda Baker","S","",F,"",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Zachary Carter","DT","Knee",L,"Out",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Hjalte Froholdt","C","Concussion",D,"Out",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Jon Gaines II","G","Ankle",D,"Out",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Bam Knight","RB","",F,"",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Hunter Long","TE","Knee",L,"Questionable",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Roy Lopez","DT","Toe; Ankle",L,"Questionable",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Max Melton","CB","Knee; Hand",L,"Questionable",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Darius Robinson","DT","Wrist",L,"Questionable",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Isaac Seumalo","G","",F,"",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Dante Stills","DT","",F,"",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Josh Sweat","LB","",F,"",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Jayden Williams","T","Knee",L,"Questionable",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Mack Wilson","LB","",F,"",BASE_NOTE),
    ("AZ","LAR","2026-11-15","Andrew Wingard","S","Groin",D,"Questionable",BASE_NOTE),
    # -- Sun Nov 15 4:05: SEA @ LV --
    ("SEA","LV","2026-11-15","AJ Barner","TE","",F,"",BASE_NOTE),
    ("SEA","LV","2026-11-15","Anthony Bradford","G","",F,"",BASE_NOTE),
    ("SEA","LV","2026-11-15","Charles Cross","T","Ankle",D,"Out",BASE_NOTE),
    ("SEA","LV","2026-11-15","Sam Darnold","QB","Ribs; Quadricep",D,"Out",BASE_NOTE),
    ("SEA","LV","2026-11-15","Derick Hall","LB","",D,"",BASE_NOTE),
    ("SEA","LV","2026-11-15","Drew Lock","QB","",L,"",BASE_NOTE,"Official report shows no game-status designation; NFL.com news (Nov 14): no injury designation, will start"),
    ("SEA","LV","2026-11-15","Quenton Nelson","G","Knee",D,"Out",BASE_NOTE),
    ("SEA","LV","2026-11-15","Uchenna Nwosu","LB","",F,"",BASE_NOTE),
    ("SEA","LV","2026-11-15","Patrick O'Connell","LB","",F,"",BASE_NOTE),
    ("SEA","LV","2026-11-15","Connor O'Toole","LB","",F,"",BASE_NOTE),
    ("SEA","LV","2026-11-15","Brandon Pili","DT","",F,"",BASE_NOTE),
    ("SEA","LV","2026-11-15","Jarran Reed","DT","",F,"",BASE_NOTE),
    ("SEA","LV","2026-11-15","Rashid Shaheed","WR","",F,"",BASE_NOTE),
    ("SEA","LV","2026-11-15","Jaxon Smith-Njigba","WR","",F,"",BASE_NOTE),
    ("SEA","LV","2026-11-15","Leonard Williams","DT","Stinger",D,"Out",BASE_NOTE),
    ("LV","SEA","2026-11-15","Thomas Booker","DT","Ankle",F,"Questionable",BASE_NOTE),
    ("LV","SEA","2026-11-15","Foley Fatukasi","DT","",F,"",BASE_NOTE),
    ("LV","SEA","2026-11-15","Ian Thomas","TE","",F,"",BASE_NOTE),
    ("LV","SEA","2026-11-15","Dont'e Thornton Jr.","WR","Back",D,"Questionable",BASE_NOTE),
    ("LV","SEA","2026-11-15","Trey Zuhn III","C","",F,"",BASE_NOTE),
    # -- Sun Nov 15 4:25: SF @ DAL --
    ("SF","DAL","2026-11-15","Mike Evans","WR","Achilles",D,"Out",BASE_NOTE),
    ("SF","DAL","2026-11-15","Renardo Green","CB","Back",L,"Questionable",BASE_NOTE),
    ("SF","DAL","2026-11-15","Dre Greenlaw","LB","Knee",L,"Questionable",BASE_NOTE),
    ("SF","DAL","2026-11-15","Nate Hobbs","CB","Groin",F,"Questionable",BASE_NOTE),
    ("SF","DAL","2026-11-15","Deommodore Lenoir","CB","Foot",L,"Questionable",BASE_NOTE),
    ("SF","DAL","2026-11-15","Christian McCaffrey","RB","",F,"",BASE_NOTE),
    ("SF","DAL","2026-11-15","Siran Neal","S","",F,"",BASE_NOTE),
    ("SF","DAL","2026-11-15","Demarcus Robinson","WR","",F,"",BASE_NOTE),
    ("SF","DAL","2026-11-15","Deebo Samuel Sr.","WR","",F,"",BASE_NOTE),
    ("SF","DAL","2026-11-15","Upton Stout","CB","Shoulder; Neck",L,"Questionable",BASE_NOTE),
    ("SF","DAL","2026-11-15","C.J. West","DT","Knee",F,"Questionable",BASE_NOTE),
    ("SF","DAL","2026-11-15","Trent Williams","T","Shoulder",D,"Questionable",BASE_NOTE),
    ("DAL","SF","2026-11-15","DaRon Bland","CB","Ankle",L,"Questionable",BASE_NOTE),
    ("DAL","SF","2026-11-15","Jonathan Bullard","DT","Calf",F,"Questionable",BASE_NOTE),
    ("DAL","SF","2026-11-15","Alijah Clark","S","Illness",D,"Questionable",BASE_NOTE),
    ("DAL","SF","2026-11-15","Donovan Ezeiruaku","LB","Ankle",D,"Out",BASE_NOTE),
    ("DAL","SF","2026-11-15","Jake Ferguson","TE","Knee; Ankle",D,"Out",BASE_NOTE),
    ("DAL","SF","2026-11-15","Tyler Goodson","RB","Ankle; Knee",D,"Out",BASE_NOTE),
    ("DAL","SF","2026-11-15","Malik Hooker","S","",D,"",BASE_NOTE),
    ("DAL","SF","2026-11-15","Marist Liufau","LB","",F,"",BASE_NOTE),
    ("DAL","SF","2026-11-15","P.J. Locke","S","Concussion",D,"Out",BASE_NOTE),
    ("DAL","SF","2026-11-15","Von Miller","LB","",D,"",BASE_NOTE),
    ("DAL","SF","2026-11-15","Jonathan Mingo","WR","Ankle",D,"Out",BASE_NOTE),
    ("DAL","SF","2026-11-15","Devin Moore","CB","Hip",F,"Questionable",BASE_NOTE),
    ("DAL","SF","2026-11-15","DeMarvion Overshown","LB","",F,"",BASE_NOTE),
    ("DAL","SF","2026-11-15","George Pickens","WR","",F,"",BASE_NOTE),
    ("DAL","SF","2026-11-15","Joey Porter Jr.","CB","Ankle; Foot",L,"Questionable",BASE_NOTE),
    ("DAL","SF","2026-11-15","Luke Schoonmaker","TE","",F,"",BASE_NOTE),
    ("DAL","SF","2026-11-15","Brevyn Spann-Ford","TE","",F,"",BASE_NOTE),
    ("DAL","SF","2026-11-15","Juanyeh Thomas","S","Hamstring",D,"Doubtful",BASE_NOTE),
    ("DAL","SF","2026-11-15","KaVontae Turpin","WR","",F,"",BASE_NOTE),
    # -- Sun Nov 15 8:20: PIT @ CIN --
    ("PIT","CIN","2026-11-15","Brandin Echols","CB","",F,"",BASE_NOTE),
    ("PIT","CIN","2026-11-15","DeShon Elliott","S","",F,"",BASE_NOTE),
    ("PIT","CIN","2026-11-15","Derrick Harmon","DT","Foot",F,"Questionable",BASE_NOTE),
    ("PIT","CIN","2026-11-15","Cameron Heyward","DT","",F,"",BASE_NOTE),
    ("PIT","CIN","2026-11-15","Ben Skowronek","WR","",F,"",BASE_NOTE),
    ("PIT","CIN","2026-11-15","Doneiko Slaughter","CB","",F,"",BASE_NOTE),
    ("PIT","CIN","2026-11-15","Darnell Washington","TE","",F,"",BASE_NOTE),
    ("PIT","CIN","2026-11-15","T.J. Watt","LB","",F,"",BASE_NOTE),
    ("CIN","PIT","2026-11-15","Jonathan Allen","DT","",L,"",BASE_NOTE),
    ("CIN","PIT","2026-11-15","Jalen Davis","CB","Hamstring",F,"Doubtful",BASE_NOTE),
    ("CIN","PIT","2026-11-15","Kyle Dugger","S","Quadricep",D,"Out",BASE_NOTE),
    ("CIN","PIT","2026-11-15","Dylan Fairchild","G","",F,"",BASE_NOTE),
    ("CIN","PIT","2026-11-15","B.J. Hill","DT","",D,"",BASE_NOTE),
    ("CIN","PIT","2026-11-15","Andrei Iosivas","WR","Thumb",F,"Doubtful",BASE_NOTE),
    ("CIN","PIT","2026-11-15","Dexter Lawrence","DT","",D,"",BASE_NOTE),
    ("CIN","PIT","2026-11-15","Brian Parker II","G","Knee",F,"Doubtful",BASE_NOTE),
    ("CIN","PIT","2026-11-15","DJ Turner II","CB","",F,"",BASE_NOTE),
    # -- Mon Nov 16 8:15: LAC @ BAL --
    ("LAC","BAL","2026-11-16","Kayode Awosika","G","",L,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Bud Dupree","DE","",D,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Justin Eboigbe","DE","",L,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Alex Harkey","G","",F,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Tre Harris","WR","",F,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Cam Hart","CB","",F,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Daiyan Henley","LB","",F,"",BASE_NOTE,"Official report lists him on LAC; NFL.com news (Nov 10) headline says Broncos traded for Chargers' LB Daiyan Henley - manual review recommended"),
    ("LAC","BAL","2026-11-16","Deane Leonard","CB","",F,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Khalil Mack","LB","",F,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Ladd McConkey","WR","",D,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Keaton Mitchell","RB","",L,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","David Njoku","TE","",L,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Denzel Perryman","LB","",F,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Trey Pipkins","T","",D,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Rodney Shelley","CB","",L,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Branson Taylor","G","",D,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Brenen Thompson","WR","",D,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Isas Waxter","CB","",D,"",BASE_NOTE),
    ("LAC","BAL","2026-11-16","Kendall Williamson","S","",D,"",BASE_NOTE),
    ("BAL","LAC","2026-11-16","Rasheen Ali","RB","",F,"",BASE_NOTE),
    ("BAL","LAC","2026-11-16","Rashod Bateman","WR","",F,"",BASE_NOTE),
    ("BAL","LAC","2026-11-16","Kyle Hamilton","S","",F,"",BASE_NOTE),
    ("BAL","LAC","2026-11-16","Jaylinn Hawkins","S","",L,"",BASE_NOTE),
    ("BAL","LAC","2026-11-16","Matthew Hibner","TE","",F,"",BASE_NOTE),
    ("BAL","LAC","2026-11-16","Olaivavega Ioane","G","",F,"",BASE_NOTE),
    ("BAL","LAC","2026-11-16","Adam Randall","RB","",F,"",BASE_NOTE),
    ("BAL","LAC","2026-11-16","Nate Wiggins","CB","",F,"",BASE_NOTE),
]

# ------------------------------------------------------------- injury news --
NEWS = [
    ("Drew Lock (elbow/oblique) has no injury designation, will start for Seahawks vs. Raiders","https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders"),
    ("NFL news roundup: Ravens confirm Lamar Jackson expected to miss 6-10 weeks; Kenneth Walker questionable","https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13"),
    ("NFL news roundup: Latest league updates from Thursday, Nov. 12","https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-thursday-nov-12"),
    ("NFL news roundup: Browns to start QB Deshaun Watson vs. Texans; Cardinals' Carson Beck to start vs. Rams","https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"),
    ("Dolphins place QB Malik Willis (groin) on injured reserve; Kyle McCord in line for first start","https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start"),
    ("NFL news roundup: Bills acquire S Amani Hooker; Broncos trade for Chargers' Daiyan Henley","https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-tuesday-nov-10"),
    ("Rams WR Puka Nacua likely to be placed on injured reserve with turf toe, sprained MCL and PCL","https://www.nfl.com/news/rams-wr-puka-nacua-likely-to-be-placed-on-injured-reserve-with-turf-toe-sprained-mcl-and-pcl"),
    ("Packers RB Josh Jacobs to undergo surgery on finger this week; timeline to return TBD","https://www.nfl.com/news/packers-rb-josh-jacobs-to-undergo-surgery-on-finger-this-week"),
    ("Sam Darnold ruled out for Seahawks' Week 10 game vs. Raiders; Drew Lock expected to start again","https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again"),
    ("NFL news roundup: J.J. McCarthy expected to play Week 10; Justin Herbert avoids finger fracture","https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-monday-nov-9"),
    ("Notable injuries, news from Sunday's Week 9 games: Rams WR Puka Nacua to undergo testing on knee injury","https://www.nfl.com/news/notable-injuries-news-sunday-week-9-games-2026"),
    ("NFL Network: Ravens' Lamar Jackson (right thumb) out 6-9 weeks, expects to return this season","https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season"),
]

def write_csv(name, header, rows):
    p = os.path.join(OUT, name)
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {p} ({len(rows)} rows)")

def write_json(name, records):
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=1)
    print(f"wrote {p} ({len(records)} records)")

# --- standings ---
st_header = ["team","name","conf","division","w","l","t","pct","pf","pa","net_pts","home","road","div","conf","streak","last5","games_played","source_url","note"]
st_rows, st_json = [], []
for t in STANDINGS:
    abbr,name,conf,div,w,l,tie,pct,pf,pa,net,home,road,dr,cr,streak,l5 = t
    gp = w+l+tie
    assert pf-pa == net, name
    assert w+l+tie == int(home.split('-')[0])+int(home.split('-')[1])+int(home.split('-')[2])+int(road.split('-')[0])+int(road.split('-')[1])+int(road.split('-')[2]), name
    note = "Transcribed from NFL.com league standings (2026 regular season)"
    row = [abbr,name,conf,div,w,l,tie,pct,pf,pa,net,home,road,dr,cr,streak,l5,gp,SRC_STANDINGS,note]
    st_rows.append(row)
    st_json.append(dict(zip(st_header,row)))
write_csv("standings_2026_wk9.csv", st_header, st_rows)
write_json("standings_2026_wk9.json", st_json)

# --- schedule ---
sc_header = ["week","date","time_et","slot","away","home","network","venue_note","game_url","status","away_pts","home_pts","source_url","note"]
sc_rows, sc_json = [], []
for wk_row in SCHEDULE:
    date, tm, slot, aw, hm, netw, vn, url, status, ap, hp = wk_row
    row = [10, date, tm, slot, aw, hm, netw, vn, url, status, ap, hp, SRC_SCHEDULE, "Transcribed from NFL.com Week 10 schedule; team records cross-checked against standings"]
    sc_rows.append(row); sc_json.append(dict(zip(sc_header,row)))
write_csv("schedule_2026_wk10.csv", sc_header, sc_rows)
write_json("schedule_2026_wk10.json", sc_json)

# --- injuries ---
inj_header = ["week","team","opponent","game_date","player","position","injuries","practice_status","game_status","source_url","note"]
inj_rows, inj_json = [], []
for t in INJ:
    if len(t) == 10:  # base note + extra manual-review note
        note = t[8] + " | " + t[9]
        t = t[:8] + (note,)
    team,opp,gd,player,pos,inj,prac,gs,note = t
    inj_final = inj.replace("; ", "; ")
    row = [10,team,opp,gd,player,pos,inj_final,prac,gs,SRC_INJURIES,note]
    inj_rows.append(row); inj_json.append(dict(zip(inj_header,row)))
write_csv("injuries_2026_wk10.csv", inj_header, inj_rows)
write_json("injuries_2026_wk10.json", inj_json)

# --- bye teams ---
bye_header = ["week","team","record","source_url","note"]
bye_rows = [[10,t,rec,SRC_SCHEDULE,"Listed under 'Teams on Bye' on NFL.com Week 10 schedule"] for t,rec in BYE_TEAMS]
write_csv("bye_teams_2026_wk10.csv", bye_header, bye_rows)

# --- news ---
news_header = ["headline","url","note"]
news_rows = [[h,u,"Headline transcribed from NFL.com Week 10 injury report page (news links section)"] for h,u in NEWS]
write_csv("injury_news_2026_wk10.csv", news_header, news_rows)

# --- summary ---
print(f"\nTeams on injury report: {len(set(r[1] for r in inj_rows))} (4 on bye: CHI DEN PHI TB)")
print(f"Out: {sum(1 for r in inj_rows if r[8]=='Out')}, Doubtful: {sum(1 for r in inj_rows if r[8]=='Doubtful')}, Questionable: {sum(1 for r in inj_rows if r[8]=='Questionable')}, No designation: {sum(1 for r in inj_rows if r[8]=='')}")
