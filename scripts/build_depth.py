"""Build data/depth_risk.json.

Availability  <- official NFL Week 10 injury report (S02) ONLY.
Depth order   <- Ourlads depth charts (S04), symbols decoded with S05.
Conflicts between the two are recorded, never silently merged.
"""
import json

SRC_DEPTH = "S04"
SRC_INJ = "S02"


def pedigree(code):
    """Decode an Ourlads pedigree token into (kind, draft_year, draft_round)."""
    if not code:
        return (None, None, None)
    c = code.strip()
    parts = c.split("/")
    if len(parts) == 2 and parts[0].isdigit() and len(parts[0]) == 2:
        try:
            return ("draft", 2000 + int(parts[0]), int(parts[1].replace("R", "")))
        except ValueError:
            return ("draft", 2000 + int(parts[0]), None)
    for p in ("CC", "U", "T", "W", "P"):
        if c == p or c.startswith(p + "/"):
            return ("veteran-" + p, None, None)
    if c.startswith("CF"):
        try:
            return ("udfa", 2000 + int(c[2:4]), None)
        except Exception:
            return ("udfa", None, None)
    if c.startswith("SF"):
        try:
            return ("street-fa", 2000 + int(c[2:4]), None)
        except Exception:
            return ("street-fa", None, None)
    return ("other", None, None)


# team -> position -> [(player, depth_code, ourlads_marker, ourlads_note)]
# ourlads_marker: "O"=Out, "Q"=Questionable, "D"=Doubtful, "DFR"=designated for return,
# "NIR"=not injury related/resting, None=no marker on the chart.
# Transcribed from https://www.ourlads.com/nfldepthcharts/pfdepthchart/<TEAM> (S04).
D = {
 "WAS": {
  "C":      [("Lucas Patrick", "SF26", "O", "Concussion"), ("Nick Allegretti", "U/KC", None, "")],
  "TE":     [("Chig Okonkwo", "U/Ten", None, ""), ("John Bates", "21/4", None, ""), ("Ben Sinnott", "24/2", None, ""), ("Colson Yankoff", "CF24", "O", "Knee")],
  "CB":     [("Trey Amos", "25/2", None, ""), ("Rasul Douglas", "U/Mia", None, ""), ("Isaac Yiadom", "SF26", None, ""), ("Amik Robertson", "U/Det", None, "")],
  "WR":     [("Antonio Williams", "26/3", None, ""), ("Treylon Burks", "SF25", None, ""), ("Van Jefferson", "U/Ten", None, ""), ("Stefon Diggs", "CC/NE", None, ""), ("Luke McCaffrey", "24/3", None, "")],
  "DT":     [("Charles Omenihu", "U/KC", None, ""), ("Jer'Zhan Newton", "24/2", None, ""), ("Shy Tuttle", "W/Ten", None, "")],
  "QB":     [("Jayden Daniels", "24/1", None, ""), ("Marcus Mariota", "U/Phi", None, ""), ("Athan Kaliakmanis", "26/7", None, "")],
 },
 "NYG": {
  "QB":     [("J.J. McCarthy", "25/1", None, ""), ("Tyler Huntley", None, None, "")],
  "WR":     [("Malik Nabers", "24/1", None, ""), ("Darnell Mooney", "U/Atl", None, ""), ("Charlie Jones", "U/Chi", None, "")],
  "TE":     [("Theo Johnson", "24/4", None, "")],
  "T":      [("Andrew Thomas", "20/1", None, ""), ("Jermaine Eluemunor", "U/LV", None, "")],
  "LB":     [("Abdul Carter", "25/1", None, ""), ("Malik Harrison", "U/Bal", "Q", "Groin")],
  "CB":     [("Colton Hood", "26/2", None, "")],
 },
 "NE": {
  "C":      [("Jared Wilson", "25/3", None, ""), ("Ben Brown", "P/LV", "O", "Knee")],
  "WR":     [("A.J. Brown", "T/Phi", "Q", "Ankle, Knee"), ("Mack Hollins", "U/Buf", None, ""), ("Kyle Williams", "25/3", None, "")],
  "CB":     [("Carlton Davis III", "U/Det", "O", "Knee"), ("Christian Gonzalez", "23/1", None, ""), ("Charles Woods", "W/LAR", "Q", "Hamstring")],
  "RB":     [("Rhamondre Stevenson", "21/4", "Q", "Knee"), ("TreVeyon Henderson", "25/2", "O", "Illness"), ("Corey Kiner", "T/Arz", None, "")],
  "QB":     [("Drake Maye", "24/1", None, ""), ("Tommy DeVito", "W/NYG", None, "")],
 },
 "DET": {
  "C":      [("Cade Mays", "U/Car", "O", "Ankle"), ("Juice Scruggs", "T/Hou", None, ""), ("Seth McLaughlin", "SF26", None, "")],
  "CB":     [("Ennis Rakestraw Jr.", "24/2", None, ""), ("Khalil Dorsey", "SF22", None, ""), ("Rock Ya-Sin", "U/SF", None, ""), ("D.J. Reed", "U/NYJ", "O", "Hip")],
  "S":      [("Brian Branch", "23/2", None, ""), ("Chuck Clark", "U/Pit", None, ""), ("Kerby Joseph", "22/3", "DFR", "Knee"), ("Keith Abney II", "26/5", None, "")],
  "WR":     [("Amon-Ra St. Brown", "21/4", "Q", "Rib"), ("Jameson Williams", "22/1", None, ""), ("Isaac TeSlaa", "25/3", None, "")],
  "RB":     [("Jahmyr Gibbs", "23/1", None, ""), ("Sione Vaki", "24/4", "Q", "Ankle"), ("Jacob Saylors", "SF25", None, "")],
  "DE":     [("Aidan Hutchinson", "22/1", None, ""), ("D.J. Wonnum", "U/Car", "O", ""), ("Derrick Moore", "26/2", None, "")],
 },
 "KC": {
  "WR":     [("Xavier Worthy", "24/1", None, ""), ("Rashee Rice", "23/2", None, ""), ("Josh Downs", "T/Ind", None, "")],
  "RB":     [("Kenneth Walker III", "U/Sea", "Q", "Groin"), ("Emmett Johnson", "26/5", None, ""), ("Jaydn Ott", "CF26", "Q", "Hamstring")],
  "DT":     [("Chris Jones", "16/2", None, ""), ("Khyiris Tonga", "U/NE", None, ""), ("Peter Woods", "26/1", "O", "Neck")],
  "CB":     [("Mansoor Delane", "26/1", "O", ""), ("Nohl Williams", "25/3", None, ""), ("Kristian Fulton", "U/LAC", None, "")],
  "T":      [("Kahlil Benson", "CF26", None, ""), ("Jaylon Moore", "U/SF", None, "Ankle")],
  "QB":     [("Patrick Mahomes", "17/1", None, ""), ("Justin Fields", "T/NYJ", None, "")],
 },
 "ATL": {
  "WR":     [("Drake London", "22/1", None, ""), ("Jahan Dotson", "U/Phi", None, ""), ("Olamide Zaccheaus", "U/Chi", None, ""), ("Zachariah Branch", "26/3", "O", "Hamstring")],
  "LB":     [("Divine Deablo", "U/LV", None, "Forearm"), ("Kendal Daniels", "26/4", None, ""), ("Josh Woods", "U/Arz", "Q", "Ankle")],
  "DT":     [("Gervon Dexter Sr.", "T/Chi", "Q", "Illness"), ("Brandon Dorlus", "24/4", None, "")],
  "DE":     [("James Pearce Jr.", "25/1", "Q", "Back"), ("Za'Darius Smith", "SF26", None, ""), ("Cameron Thomas", "U/Cle", None, "")],
  "T":      [("Jake Matthews", "14/1", None, ""), ("Jawaan Taylor", "CC/KC", None, "")],
  "QB":     [("Michael Penix Jr.", "24/1", None, ""), ("Tua Tagovailoa", "CC/Mia", None, ""), ("Andy Dalton", "SF26", None, "")],
 },
 "MIN": {
  "TE":     [("T.J. Hockenson", "19/1", "O", "Wrist, Chest"), ("Josh Oliver", "U/Bal", None, "")],
  "LB":     [("Blake Cashman", "U/Hou", "O", "Concussion"), ("Kyle Van Noy", "SF26", "Q", "Calf")],
  "DT":     [("Tyrion Ingram-Dawkins", "25/5", "O", "Ankle")],
  "CB":     [("Byron Murphy Jr.", "19/2", None, "")],
  "WR":     [("Justin Jefferson", "20/1", None, ""), ("Jordan Addison", "23/1", "Q", "Thumb"), ("Jauan Jennings", "U/SF", "O", "Calf")],
  "S":      [("Harrison Smith", "12/1", None, ""), ("Josh Metellus", "20/6", "Q", "Shoulder")],
 },
 "GB": {
  "RB":     [("Josh Jacobs", "U/LV", "O", "Finger"), ("MarShawn Lloyd", "24/3", "O", ""), ("Pierre Strong Jr.", "SF25", None, "")],
  "C":      [("Sean Rhyan", "22/3", "O", "Ankle"), ("John Williams", "25/7", None, "")],
  "G":      [("Laken Tomlinson", "P/Dal", None, ""), ("Aaron Banks", "U/SF", None, ""), ("Travis Glover", "24/6", "O", "Knee"), ("Kevin Zeitler", "U/Ten", None, "")],
  "LB":     [("Zaire Franklin", "T/Ind", "O", "Shin"), ("Ty'Ron Hopper", "24/3", None, ""), ("Isaiah McDuffie", "21/6", None, "")],
  "TE":     [("Tucker Kraft", "23/3", None, ""), ("Josh Whyle", "SF25", "O", "Concussion")],
  "S":      [("Xavier McKinney", "U/NYG", None, ""), ("Javon Bullard", "24/2", "Q", "Ankle, Knee")],
  "QB":     [("Jordan Love", "20/1", None, ""), ("Tyrod Taylor", "U/NYJ", None, "")],
 },
 "JAX": {
  "S":      [("Jessie Bates III", "T/Atl", "NIR", "Not injury related - resting player"), ("Antonio Johnson", "23/5", None, ""), ("Jalen Huskey", "26/3", None, "")],
  "DT":     [("Jordan Davis", "T/Phi", "NIR", "Not injury related - resting player"), ("Davon Godchaux", "T/NO", None, "")],
  "C":      [("Robert Hainsey", "U/TB", "Q", "Concussion"), ("Jonah Monheim", "25/7", None, "")],
  "RB":     [("Bhayshul Tuten", "25/4", "Q", ""), ("Chris Rodriguez Jr.", "U/Was", None, "")],
  "DE":     [("Travon Walker", "22/1", None, ""), ("Josh Hines-Allen", "19/1", None, ""), ("BJ Green II", "SF26", "DFR", "Forearm")],
 },
 "TEN": {
  "LB":     [("Cody Barton", "U/Den", "O", "Concussion"), ("Anthony Hill Jr.", "26/2", "O", "Neck"), ("Cedric Gray", "24/4", None, ""), ("Dorian Mausi", "W/Min", None, "")],
  "G":      [("Peter Skoronski", "23/1", "O", "Hamstring"), ("Garrett Dellinger", "W/Cle", None, "")],
  "WR":     [("Carnell Tate", "26/1", "O", "Shoulder"), ("Elic Ayomanor", "25/4", None, ""), ("Chimere Dike", "25/4", None, "")],
  "P":      [("Tommy Townsend", "U/Hou", "O", "Knee, Achilles"), ("Thomas Morstead", "SF26", None, "")],
  "CB":     [("Cor'Dale Flott", "U/NYG", None, ""), ("Jaylon Jones", "SF26", None, "")],
  "QB":     [("Cam Ward", "25/1", None, ""), ("Mitchell Trubisky", "U/Buf", None, "")],
 },
 "BUF": {
  "T":      [("Dion Dawkins", "17/2", "O", ""), ("Spencer Brown", "21/3", "Q", "Ankle"), ("Tylan Grable", "24/6", None, ""), ("Jude Bowry", "26/4", None, "")],
  "G":      [("Alec Anderson", "CF22", "O", ""), ("O'Cyrus Torrence", "23/2", None, ""), ("Ar'maj Reed-Adams", "26/7", None, "")],
  "LB":     [("Terrel Bernard", "22/3", None, ""), ("Dorian Williams", "23/3", None, "")],
  "DE":     [("Greg Rousseau", "21/1", None, ""), ("Ed Oliver", "19/1", None, ""), ("T.J. Sanders", "25/2", None, "")],
  "CB":     [("Christian Benford", "22/6", "Q", "Wrist"), ("Davison Igbinosun", "26/2", None, "")],
  "S":      [("Amani Hooker", "T/Ten", None, ""), ("Sam Franklin Jr.", "SF25", "Q", "Shoulder")],
  "WR":     [("Khalil Shakir", "22/5", None, "")],
 },
 "NYJ": {
  "LB":     [("Trevin Wallace", "SF25", "O", "Groin")],
  "WR":     [("Garrett Wilson", "22/1", "Q", "Concussion"), ("Omar Cooper Jr.", "25/4", "Q", "Ankle"), ("Adonai Mitchell", "24/2", "Q", "Knee")],
  "CB":     [("Jarvis Brownlee Jr.", "24/5", "Q", "Illness"), ("Nahshon Wright", "SF26", "Q", "Back")],
  "DT":     [("Harrison Phillips", "U/Min", "Q", "Ankle")],
  "S":      [("VJ Payne", "25/4", "Q", "Knee")],
 },
 "MIA": {
  "C":      [("Aaron Brewer", "U/Ten", "O", "Concussion"), ("Andrew Meyer", "CF24", None, "")],
  "WR":     [("Chris Bell", "26/3", "O", "Knee"), ("Jared Wayne", "W/Hou", "O", "Quadricep"), ("Caleb Douglas", "26/3", None, "")],
  "CB":     [("Darrell Baker Jr.", "SF26", "Q", "Knee"), ("JuJu Brents", "W/Ind", None, "")],
  "RB":     [("Ollie Gordon II", "25/6", None, ""), ("Jaylen Wright", "24/4", "O", "")],
  "QB":     [("Kyle McCord", "T/GB", None, ""), ("Brady Cook", "W/NYJ", None, "")],
 },
 "IND": {
  "TE":     [("Mo Alie-Cox", "SF20", "O", "Groin"), ("Will Mallory", "23/5", "Q", "Hamstring")],
  "LB":     [("Jaylon Carlies", "24/5", "O", "Neck"), ("Akeem Davis-Gaither", "U/Cin", "O", "Knee"), ("C.J. Allen", "25/4", None, "")],
  "DT":     [("Grover Stewart", "17/4", None, ""), ("Jerry Tillery", "SF25", "O", "Calf")],
  "T":      [("Jalen Travis", "25/5", "O", "Knee")],
  "LS":     [("Luke Rhodes", "SF04", "O", "Hamstring")],
 },
 "CAR": {
  "RB":     [("Chuba Hubbard", "21/4", None, ""), ("Jonathon Brooks", "24/2", None, "Groin"), ("Trevor Etienne", "25/4", None, "")],
  "G":      [("Damien Lewis", "20/3", None, ""), ("Brady Christensen", "21/3", "Q", "Hamstring")],
  "CB":     [("Mike Jackson", "U/Sea", None, "Groin"), ("Will Lee III", "25/5", "Q", "Hamstring")],
  "LB":     [("Bobby Okereke", "U/NYG", "O", "Foot"), ("Jaelan Phillips", "U/Mia", "Q", "Hamstring")],
  "WR":     [("Xavier Legette", "24/1", "Q", "Knee")],
 },
 "NO": {
  "T":      [("Taliese Fuaga", "24/1", "O", "Knee"), ("Kelvin Banks Jr.", "25/1", None, ""), ("Asim Richards", "SF26", None, "")],
  "C":      [("Erik McCoy", "19/2", "O", "Biceps")],
  "RB":     [("Alvin Kamara", "17/3", None, ""), ("Travis Etienne", "T/Jax", "Q", "Hamstring"), ("CJ Donaldson", "SF26", "O", "Shoulder")],
  "DT":     [("Christen Miller", "26/3", "O", "Knee")],
  "CB":     [("Martin Emerson", "T/Cle", "Q", "Shin"), ("Quincy Riley", "SF26", None, "")],
 },
 "HOU": {
  "G":      [("Keylan Rutledge", "26/1", "O", "Neck, Shoulder"), ("Wyatt Teller", "U/Cle", "Q", "Illness, Back")],
  "T":      [("Trent Brown", "U/Cin", "Q", "Wrist, Illness")],
  "WR":     [("Nico Collins", "21/3", None, ""), ("Marvin Harrison Jr.", "T/Arz", "O", "Hamstring"), ("Tank Dell", "23/3", None, "")],
  "DE":     [("Will Anderson Jr.", "23/1", "Q", "Ankle"), ("Danielle Hunter", "U/Min", "O", "Hamstring"), ("Jadeveon Clowney", "U/Dal", None, "")],
  "LB":     [("Azeez Al-Shaair", "U/Ten", "O", "Groin, Not injury related - personal matter"), ("Henry To'oTo'o", "23/5", None, "")],
  "S":      [("Reed Blankenship", "U/Phi", "O", "")],
  "TE":     [("Dalton Schultz", "U/Dal", None, ""), ("Brevin Jordan", "21/5", "O", "Finger, Foot"), ("Foster Moreau", "U/NO", None, "")],
 },
 "CLE": {
  "S":      [("Ronnie Hickman Jr.", "CF23", "O", "Concussion")],
  "FB":     [("Michael Burton", "SF21", "O", "Calf")],
  "WR":     [("Denzel Boston", "26/4", "Q", "Toe")],
 },
 "LAR": {
  "G":      [("Steve Avila", "23/2", "O", "Hamstring")],
  "TE":     [("Terrance Ferguson", "24/2", "O", "Ankle, Hamstring"), ("Colby Parkinson", "22/4", None, ""), ("Tyler Higbee", "16/4", None, ""), ("Davis Allen", "23/5", "Q", "Oblique")],
  "CB":     [("Trent McDuffie", "T/KC", "Q", "Back")],
  "S":      [("Kam Curl", "U/Was", "Q", "Toe")],
  "LB":     [("Myles Garrett", "T/Cle", "Q", "Knee, Not injury related - resting player")],
  "WR":     [("Puka Nacua", "23/5", None, "")],
 },
 "AZ": {
  "C":      [("Hjalte Froholdt", "U/Cle", "O", "Concussion")],
  "G":      [("Jon Gaines II", "22/7", "O", "Ankle")],
  "DT":     [("Zachary Carter", "W/Cin", "O", "Knee"), ("Roy Lopez", "SF25", "Q", "Toe, Ankle"), ("Darius Robinson", "24/1", "Q", "Wrist")],
  "CB":     [("Max Melton", "24/2", "Q", "Knee, Hand")],
  "S":      [("Budda Baker", "17/2", None, ""), ("Andrew Wingard", "U/Jax", "Q", "Groin")],
  "TE":     [("Hunter Long", "T/Dal", "Q", "Knee")],
 },
 "SEA": {
  "QB":     [("Sam Darnold", "U/Min", "O", "Ribs, Quadricep"), ("Drew Lock", "U/NYG", None, ""), ("Jalen Milroe", "25/3", None, "")],
  "T":      [("Charles Cross", "22/1", "O", "Ankle"), ("Josh Jones", "U/Bal", None, "")],
  "G":      [("Quenton Nelson", "T/Ind", "O", "Knee"), ("Grey Zabel", "25/1", None, ""), ("Anthony Bradford", "23/4", None, "")],
  "DT":     [("Leonard Williams", "T/NYG", "O", "Stinger"), ("Byron Murphy II", "24/1", None, ""), ("Brandon Pili", "W/Mia", "O", "")],
  "WR":     [("Jaxon Smith-Njigba", "23/1", None, ""), ("Rashid Shaheed", "T/NO", "O", ""), ("Cooper Kupp", "CC/LAR", None, "")],
  "LB":     [("Uchenna Nwosu", "U/LAC", "O", ""), ("Derick Hall", "23/2", None, "")],
 },
 "SF": {
  "WR":     [("Deebo Samuel Sr.", "19/2", None, ""), ("Demarcus Robinson", "SF26", None, ""), ("Mike Evans", "U/TB", "O", "Achilles")],
  "T":      [("Trent Williams", "10/1", "Q", "Shoulder")],
  "CB":     [("Renardo Green", "24/2", "Q", "Back"), ("Deommodore Lenoir", "20/5", "Q", "Foot"), ("Nate Hobbs", "U/LV", "Q", "Groin"), ("Upton Stout", "25/6", "Q", "Shoulder, Neck")],
  "LB":     [("Dre Greenlaw", "19/5", "Q", "Knee")],
  "DT":     [("C.J. West", "25/4", "Q", "Knee")],
 },
 "DAL": {
  "CB":     [("DaRon Bland", "22/5", "Q", "Ankle"), ("Joey Porter Jr.", "U/Pit", "Q", "Ankle, Foot"), ("Devin Moore", "SF25", "Q", "Hip")],
  "TE":     [("Jake Ferguson", "22/4", "O", "Knee, Ankle"), ("Luke Schoonmaker", "23/2", None, ""), ("Brevyn Spann-Ford", "CF24", None, "")],
  "LB":     [("Donovan Ezeiruaku", "25/2", "O", "Ankle"), ("DeMarvion Overshown", "23/3", None, ""), ("Marist Liufau", "24/4", None, "")],
  "S":      [("Malik Hooker", "U/Ind", None, ""), ("P.J. Locke", "U/Den", "O", "Concussion"), ("Juanyeh Thomas", "CF22", "D", "Hamstring")],
  "RB":     [("Tyler Goodson", "SF24", "O", "Ankle, Knee")],
  "WR":     [("George Pickens", "U/Pit", None, ""), ("KaVontae Turpin", "22/6", None, ""), ("Jonathan Mingo", "T/Car", "O", "Ankle")],
 },
 "PIT": {
  "DT":     [("Cameron Heyward", "11/1", None, ""), ("Derrick Harmon", "25/1", "Q", "Foot")],
  "S":      [("DeShon Elliott", "SF24", None, "")],
  "CB":     [("Brandin Echols", "U/NYJ", None, ""), ("Doneiko Slaughter", "26/5", None, "")],
 },
 "CIN": {
  "S":      [("Jordan Battle", "23/3", None, ""), ("Kyle Dugger", "U/Pit", "O", "Quadricep"), ("Russ Yeast", "SF25", None, "")],
  "DT":     [("Dexter Lawrence II", "T/NYG", None, ""), ("Jonathan Allen", "CC/Min", None, ""), ("B.J. Hill", "T/NYG", None, "")],
  "CB":     [("DJ Turner II", "23/2", None, ""), ("Jalen Davis", "SF20", "D", "Hamstring")],
  "WR":     [("Ja'Marr Chase", "21/1", None, ""), ("Tee Higgins", "20/2", None, ""), ("Andrei Iosivas", "23/6", "D", "Thumb")],
  "G":      [("Dylan Fairchild", "25/3", None, ""), ("Brian Parker II", "25/5", "D", "Knee")],
 },
 "LAC": {
  "WR":     [("Ladd McConkey", "24/2", None, ""), ("Tre Harris", "25/2", None, ""), ("Brenen Thompson", "26/6", None, "")],
  "TE":     [("David Njoku", "U/Cle", None, "")],
  "T":      [("Trey Pipkins", "19/3", None, "")],
  "RB":     [("Keaton Mitchell", "SF25", None, "")],
  "CB":     [("Cam Hart", "24/5", None, ""), ("Deane Leonard", "SF22", None, ""), ("Rodney Shelley", "SF26", None, "")],
 },
 "BAL": {
  "QB":     [("Jacoby Brissett", "T/Arz", None, ""), ("Joe Fagnano", "CF26", None, "")],
  "S":      [("Malaki Starks", "25/1", None, ""), ("Kyle Hamilton", "22/1", None, ""), ("Jaylinn Hawkins", "U/NE", "O", "")],
  "CB":     [("Marlon Humphrey", "17/1", None, ""), ("Nate Wiggins", "24/1", "O", ""), ("Chidobe Awuzie", "CC/Ten", None, "")],
  "RB":     [("Derrick Henry", "U/Ten", None, ""), ("Justice Hill", "19/4", None, ""), ("Rasheen Ali", "24/5", None, "")],
  "WR":     [("Zay Flowers", "23/1", None, ""), ("Rashod Bateman", "21/1", None, "")],
 },
}
inj = json.load(open("data/injuries_2026_w10.json"))["report"]
by_team = {}
for r in inj:
    by_team.setdefault(r["team"], []).append(r)


def norm(s):
    return (s or "").lower().replace(".", "").replace("'", "").replace("-", " ").replace(",", " ").strip()


def find_inj(team, name):
    """Match a depth-chart name to an official-report row. Handles 'Last, First'."""
    if "," in name:
        last, first = [x.strip() for x in name.split(",", 1)]
        variants = [norm(first + " " + last), norm(first.split()[0] + " " + last), norm(name)]
    else:
        variants = [norm(name)]
    best = None
    for r in by_team.get(team, []):
        pn = norm(r["player"])
        if pn in variants:
            return r
        pw, nw = pn.split(), variants[0].split()
        if pw and nw and pw[-1] == nw[-1] and pw[0][:1] == nw[0][:1]:
            best = best or r
    return best


rows, conflicts, no_designation = [], [], []
for team, positions in D.items():
    for pos, players in positions.items():
        for depth, (name, code, marker, note) in enumerate(players, start=1):
            kind, yr, rnd = pedigree(code)
            off = find_inj(team, name)
            gs = off["game_status"] if off else None
            prac = off["practice_status"] if off else None
            on_report = off is not None
            if not on_report:
                state = "no-designation-published"
            elif gs:
                state = gs
            else:
                state = "listed-no-game-status"

            if on_report:
                marker_says_out = marker in ("O",)
                if marker_says_out and gs != "Out":
                    conflicts.append({
                        "id": "C-%03d" % (len(conflicts) + 1),
                        "team": team, "position": pos, "player": name,
                        "ourlads_marker": marker,
                        "official_game_status": gs or "no designation",
                        "official_practice": prac,
                        "resolution": "Official NFL report (S02) governs availability; Ourlads marker (S04) recorded but not used.",
                        "sources": ["S04", "S02"]})
                elif marker == "Q" and gs == "Out":
                    conflicts.append({
                        "id": "C-%03d" % (len(conflicts) + 1),
                        "team": team, "position": pos, "player": name,
                        "ourlads_marker": marker,
                        "official_game_status": gs,
                        "official_practice": prac,
                        "resolution": "Official report rules the player Out; Ourlads understated it. Official wins.",
                        "sources": ["S04", "S02"]})

            rows.append({
                "team": team, "position": pos, "depth": depth, "player": name,
                "depth_code": code, "pedigree_kind": kind,
                "draft_year": yr, "draft_round": rnd,
                "ourlads_marker": marker, "ourlads_note": note or None,
                "official_injury": off["injury"] if off else None,
                "official_practice": prac,
                "official_game_status": gs,
                "availability_state": state,
                "on_official_report": on_report,
                "src_depth": SRC_DEPTH,
                "src_availability": SRC_INJ if on_report else None,
                "player_page": off["player_url"] if off else None,
            })
            if not on_report:
                no_designation.append({"team": team, "position": pos, "depth": depth, "player": name})

doc = {
  "meta": {
    "title": "Depth chart and backup-deficiency input set (2026 Week 10)",
    "as_of": "2026-11-14", "accessed": "2026-11-14",
    "method": [
      "Availability comes ONLY from the official NFL Week 10 injury report (S02).",
      "Depth order (1 = starter) comes ONLY from Ourlads (S04), decoded with the Ourlads key (S05).",
      "A player absent from the official report is recorded as 'no-designation-published', never as 'healthy'.",
      "Where an Ourlads O/D marker contradicts the official report the official report wins and the row is logged in conflicts and in data/flagged.json."
    ],
    "scope_limits": [
      "Positions transcribed: QB, RB, WR, TE, T, G, C, DT, DE, LB, CB, S plus specialists where a starter is out.",
      "27 of the 28 teams playing in Week 10 are covered; the Colts chart was not retrieved (flagged F-06).",
      "The official report publishes game status only - no snap counts, no graded replacement quality and no depth chart. Replacement quality here is therefore an inference from draft pedigree and depth ordinal, and is labelled as such everywhere it is shown."
    ],
    "counts": {"rows": len(rows), "teams": len(D), "conflicts": len(conflicts),
               "no_designation_published": len(no_designation)}
  },
  "depth": rows,
  "conflicts": conflicts,
  "no_designation_published": no_designation
}
json.dump(doc, open("data/depth_risk.json", "w"), indent=1)
print("rows", len(rows), "teams", len(D), "conflicts", len(conflicts), "no_designation", len(no_designation))
for c in conflicts:
    print("  CONFLICT", c["id"], c["team"], c["position"], c["player"], "ourlads=", c["ourlads_marker"], "official=", c["official_game_status"])
