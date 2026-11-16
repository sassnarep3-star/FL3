#!/usr/bin/env python3
"""
FL3 — official re-capture, 2026-11-16.

WHAT THIS DOES
--------------
Writes two capture files from transcriptions taken directly off two official NFL.com pages
during a single read, and records for each capture: the URL, the UTC clock time of the read,
the number of rows, the per-row source link, and a SHA-256 of the *normalised transcription*
(not of the raw HTTP body — see PROVENANCE below).

  data/captures/week10_injuries_2026-11-16.csv   full injury report, every row the page lists
  data/captures/week10_results_2026-11-16.csv    settled scores + kickoff state for the 14 games

PROVENANCE — read this before quoting any hash
----------------------------------------------
The agent's fetch tool returns extracted markdown, not raw HTML bytes, so a hash of the raw
response is not available to this script. The hash recorded here is SHA-256 over the
canonicalised transcription (club, player, position, injury, practice, game status, sorted by
club then page order). That makes the capture tamper-evident *relative to what was transcribed*
and lets a future re-read be compared row by row. It is NOT a hash of NFL.com's bytes and must
not be described as one. A future session with raw-body access should supersede it.

WHY IT MATTERS
--------------
The checked-in site snapshot was captured 2026-11-14. Twelve of the fourteen Week 10 games
had settled by 2026-11-16T01:30Z. Publishing "originated lines" without results, and without a
clock on the injury read, is the single largest decision-usefulness gap in the repository.
These captures close it for Week 10 only, and are dated so they cannot be mistaken for a feed.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "captures")

INJURY_URL = "https://www.nfl.com/injuries/league/2026/reg10"
SCHEDULE_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"

# Clock time of the read that produced INJURY_ROWS. Frozen constant, not datetime.now(),
# so that regenerating this file is byte-stable and the timestamp cannot drift silently.
INJURY_CAPTURED_UTC = "2026-11-16T01:31Z"
RESULTS_CAPTURED_UTC = "2026-11-16T01:30Z"

# ----------------------------------------------------------------------------------
# INJURY_ROWS — transcribed 1:1 from INJURY_URL, page order, 28 clubs.
# Format: (club, player, position, injury, practice_status, game_status)
# Empty string means the page's cell is blank. Nothing is inferred or filled in.
# -------------------------------------------------------------------------------------
INJURY_ROWS = [
 ("WAS","John Bates","TE","","Full Participation in Practice",""),
 ("WAS","Treylon Burks","WR","","Did Not Participate In Practice",""),
 ("WAS","Jayden Daniels","QB","","Full Participation in Practice",""),
 ("WAS","Matt Gulbin","C","","Full Participation in Practice",""),
 ("WAS","Chig Okonkwo","TE","","Full Participation in Practice",""),
 ("WAS","Lucas Patrick","C","Concussion","Did Not Participate In Practice","Out"),
 ("WAS","Amik Robertson","CB","","Limited Participation in Practice",""),
 ("WAS","Shy Tuttle","DT","","Full Participation in Practice",""),
 ("WAS","Colson Yankoff","TE","Knee","Did Not Participate In Practice","Out"),

 ("NYG","Abdul Carter","LB","","Full Participation in Practice",""),
 ("NYG","Jermaine Eluemunor","T","","Full Participation in Practice",""),
 ("NYG","Malik Harrison","LB","Groin","Limited Participation in Practice","Questionable"),
 ("NYG","Colton Hood","CB","","Full Participation in Practice",""),
 ("NYG","Theo Johnson","TE","","Full Participation in Practice",""),
 ("NYG","Charlie Jones","WR","","Full Participation in Practice",""),
 ("NYG","J.J. McCarthy","QB","","Full Participation in Practice",""),
 ("NYG","Darnell Mooney","WR","","Full Participation in Practice",""),
 ("NYG","Malik Nabers","WR","","Full Participation in Practice",""),
 ("NYG","Cam Skattebo","RB","","Full Participation in Practice",""),
 ("NYG","Andrew Thomas","T","","Full Participation in Practice",""),

 ("NE","Ben Brown","C","Knee","Did Not Participate In Practice","Out"),
 ("NE","A.J. Brown","WR","Ankle, Knee","Limited Participation in Practice","Questionable"),
 ("NE","Kevin Byard","S","Chest","Full Participation in Practice","Questionable"),
 ("NE","Carlton Davis III","CB","Knee","Did Not Participate In Practice","Out"),
 ("NE","Reggie Gilliam","FB","Knee","Limited Participation in Practice","Questionable"),
 ("NE","TreVeyon Henderson","RB","Illness","Did Not Participate In Practice","Out"),
 ("NE","Hunter Henry","TE","","Limited Participation in Practice",""),
 ("NE","Cameron Latu","TE","Back","Limited Participation in Practice","Questionable"),
 ("NE","Drake Maye","QB","","Full Participation in Practice",""),
 ("NE","Morgan Moses","T","","Full Participation in Practice",""),
 ("NE","Walter Rouse","T","Concussion","Limited Participation in Practice","Questionable"),
 ("NE","Brenden Schooler","S","Hamstring","Limited Participation in Practice","Questionable"),
 ("NE","Rhamondre Stevenson","RB","Knee","Limited Participation in Practice","Questionable"),
 ("NE","Greg Van Roten","G","Hamstring","Full Participation in Practice","Questionable"),
 ("NE","Charles Woods","CB","Hamstring","Full Participation in Practice","Questionable"),

 ("DET","Brian Branch","S","","Full Participation in Practice",""),
 ("DET","Jared Goff","QB","","Full Participation in Practice",""),
 ("DET","Kerby Joseph","S","Knee","Did Not Participate In Practice","Out"),
 ("DET","Cade Mays","C","Ankle","Did Not Participate In Practice","Out"),
 ("DET","D.J. Reed","CB","Hip","Did Not Participate In Practice","Out"),
 ("DET","Jacob Saylors","RB","","Full Participation in Practice",""),
 ("DET","Amon-Ra St. Brown","WR","Rib","Limited Participation in Practice","Questionable"),
 ("DET","Sione Vaki","RB","Ankle","Limited Participation in Practice","Questionable"),
 ("DET","DJ Wonnum","DE","","Full Participation in Practice",""),

 ("KC","Jeffrey Bassa","LB","","Full Participation in Practice",""),
 ("KC","Mansoor Delane","CB","Shoulder","Full Participation in Practice","Questionable"),
 ("KC","Justin Fields","QB","","Full Participation in Practice",""),
 ("KC","Jaden Hicks","S","","Full Participation in Practice",""),
 ("KC","Travis Kelce","TE","","Full Participation in Practice",""),
 ("KC","Patrick Mahomes","QB","","Full Participation in Practice",""),
 ("KC","Jaylon Moore","T","Ankle","Did Not Participate In Practice","Out"),
 ("KC","Omarr Norman-Lott","DT","Knee","Limited Participation in Practice","Out"),
 ("KC","Jaydn Ott","RB","Hamstring","Limited Participation in Practice","Questionable"),
 ("KC","Rashee Rice","WR","","Full Participation in Practice",""),
 ("KC","Kenneth Walker III","RB","Groin","Did Not Participate In Practice","Questionable"),
 ("KC","Peter Woods","DT","Neck","Did Not Participate In Practice","Out"),
 ("KC","Xavier Worthy","WR","","Full Participation in Practice",""),

 ("ATL","Zachariah Branch","WR","Hamstring","Did Not Participate In Practice","Out"),
 ("ATL","Kendal Daniels","LB","","Full Participation in Practice",""),
 ("ATL","Divine Deablo","LB","Forearm","Did Not Participate In Practice","Doubtful"),
 ("ATL","Gervon Dexter Sr.","DT","Illness","Limited Participation in Practice","Questionable"),
 ("ATL","Jake Matthews","T","","Limited Participation in Practice",""),
 ("ATL","Liam McCullough","LS","","Did Not Participate In Practice",""),
 ("ATL","James Pearce Jr.","DE","Back","Limited Participation in Practice","Questionable"),
 ("ATL","Za'Darius Smith","DE","","Full Participation in Practice",""),
 ("ATL","Jawaan Taylor","T","","Limited Participation in Practice",""),
 ("ATL","Cameron Thomas","DE","","Full Participation in Practice",""),
 ("ATL","Josh Woods","LB","Ankle","Full Participation in Practice","Questionable"),

 ("MIN","Jordan Addison","WR","Thumb","Limited Participation in Practice","Questionable"),
 ("MIN","Blake Cashman","LB","Concussion","Limited Participation in Practice","Out"),
 ("MIN","Christian Darrisaw","T","","Did Not Participate In Practice",""),
 ("MIN","T.J. Hockenson","TE","Wrist, Chest","Did Not Participate In Practice","Out"),
 ("MIN","Tyrion Ingram-Dawkins","DT","Ankle","Did Not Participate In Practice","Out"),
 ("MIN","Theo Jackson","S","","Full Participation in Practice",""),
 ("MIN","Jauan Jennings","WR","Calf","Did Not Participate In Practice","Out"),
 ("MIN","Josh Metellus","S","Shoulder","Limited Participation in Practice","Questionable"),
 ("MIN","Kyler Murray","QB","Hamstring","Did Not Participate In Practice","Out"),
 ("MIN","Harrison Smith","S","","Limited Participation in Practice",""),
 ("MIN","Kyle Van Noy","LB","Calf","Limited Participation in Practice","Questionable"),
 ("MIN","Jay Ward","S","","Full Participation in Practice",""),
 ("MIN","Carson Wentz","QB","","Full Participation in Practice",""),

 ("GB","Aaron Banks","G","","Limited Participation in Practice",""),
 ("GB","Chris Brooks","RB","Ankle","Limited Participation in Practice","Questionable"),
 ("GB","Javon Bullard","S","Ankle, Knee","Limited Participation in Practice","Questionable"),
 ("GB","Zaire Franklin","LB","Shin","Did Not Participate In Practice","Doubtful"),
 ("GB","Travis Glover","G","Knee","Limited Participation in Practice","Questionable"),
 ("GB","Ty'Ron Hopper","LB","","Full Participation in Practice",""),
 ("GB","Josh Jacobs","RB","Finger","Did Not Participate In Practice","Out"),
 ("GB","Xavier McKinney","S","Foot","Limited Participation in Practice","Questionable"),
 ("GB","Bo Melton","WR","","Full Participation in Practice",""),
 ("GB","Skyy Moore","WR","Ankle","Limited Participation in Practice","Questionable"),
 ("GB","Micah Parsons","LB","Knee, Illness","Limited Participation in Practice","Out"),
 ("GB","Sean Rhyan","C","Ankle","Did Not Participate In Practice","Out"),
 ("GB","Trey Smack","K","","Full Participation in Practice",""),
 ("GB","Lukas Van Ness","LB","Back","Limited Participation in Practice","Questionable"),
 ("GB","Josh Whyle","TE","Concussion","Did Not Participate In Practice","Out"),
 ("GB","Savion Williams","WR","","Limited Participation in Practice",""),
 ("GB","Kevin Zeitler","G","Ankle, Triceps","Did Not Participate In Practice","Questionable"),

 ("JAX","Jessie Bates","S","Not injury related - resting player","Limited Participation in Practice","Out"),
 ("JAX","Ezra Cleveland","G","","Full Participation in Practice",""),
 ("JAX","Branson Combs","LB","","Full Participation in Practice",""),
 ("JAX","Jordan Davis","DT","Not injury related - resting player","Limited Participation in Practice","Out"),
 ("JAX","BJ Green II","DE","Forearm","Full Participation in Practice","Out"),
 ("JAX","Robert Hainsey","C","Concussion","Limited Participation in Practice","Questionable"),
 ("JAX","Antonio Johnson","S","","Limited Participation in Practice",""),
 ("JAX","Jakobi Meyers","WR","","Limited Participation in Practice",""),
 ("JAX","Chris Rodriguez Jr.","RB","","Limited Participation in Practice",""),
 ("JAX","Bhayshul Tuten","RB","","Limited Participation in Practice",""),
 ("JAX","Travon Walker","DE","","Limited Participation in Practice",""),

 ("TEN","Cody Barton","LB","Concussion","Did Not Participate In Practice","Out"),
 ("TEN","John Franklin-Myers","DE","","Full Participation in Practice",""),
 ("TEN","Marcus Harris","CB","","Full Participation in Practice",""),
 ("TEN","Anthony Hill Jr.","LB","Neck","Did Not Participate In Practice","Out"),
 ("TEN","Jaylon Jones","CB","","Full Participation in Practice",""),
 ("TEN","JC Latham","T","","Full Participation in Practice",""),
 ("TEN","Tony Pollard","RB","","Full Participation in Practice",""),
 ("TEN","Peter Skoronski","G","Hamstring","Did Not Participate In Practice","Out"),
 ("TEN","Tyjae Spears","RB","Knee","Full Participation in Practice","Questionable"),
 ("TEN","Carnell Tate","WR","Shoulder","Did Not Participate In Practice","Out"),
 ("TEN","Tommy Townsend","P","Knee, Achilles","Did Not Participate In Practice","Out"),
 ("TEN","Kevin Winston Jr.","S","","Full Participation in Practice",""),

 ("BUF","Alec Anderson","G","","Full Participation in Practice",""),
 ("BUF","Christian Benford","CB","Wrist","Full Participation in Practice","Questionable"),
 ("BUF","Terrel Bernard","LB","","Did Not Participate In Practice",""),
 ("BUF","Spencer Brown","T","Ankle","Did Not Participate In Practice","Doubtful"),
 ("BUF","Dion Dawkins","T","","Full Participation in Practice",""),
 ("BUF","Sam Franklin Jr.","S","Shoulder","Limited Participation in Practice","Questionable"),
 ("BUF","Greg Gaines","DT","","Full Participation in Practice",""),
 ("BUF","Jordan Hancock","CB","Hamstring","Full Participation in Practice","Questionable"),
 ("BUF","Dalton Kincaid","TE","","Full Participation in Practice",""),
 ("BUF","Connor McGovern","C","","Full Participation in Practice",""),
 ("BUF","Ed Oliver","DE","","Did Not Participate In Practice",""),
 ("BUF","Ar'maj Reed-Adams","G","","Full Participation in Practice",""),
 ("BUF","T.J. Sanders","DE","","Full Participation in Practice",""),
 ("BUF","Tyrell Shavers","WR","Knee","Full Participation in Practice","Questionable"),

 ("NYJ","Jarvis Brownlee Jr.","CB","Illness","Limited Participation in Practice","Questionable"),
 ("NYJ","Omar Cooper Jr.","WR","Ankle","Full Participation in Practice","Questionable"),
 ("NYJ","Adonai Mitchell","WR","Knee","Full Participation in Practice","Questionable"),
 ("NYJ","Joseph Ossai","DE","Ankle","Full Participation in Practice","Questionable"),
 ("NYJ","VJ Payne","S","Knee","Full Participation in Practice","Questionable"),
 ("NYJ","Harrison Phillips","DT","Ankle","Full Participation in Practice","Questionable"),
 ("NYJ","Trevin Wallace","LB","Groin","Did Not Participate In Practice","Out"),
 ("NYJ","Garrett Wilson","WR","Concussion","Full Participation in Practice","Questionable"),
 ("NYJ","Nahshon Wright","CB","Back","Full Participation in Practice","Questionable"),

 ("MIA","Tucker Addington","LS","","Limited Participation in Practice",""),
 ("MIA","Kaytron Allen","RB","","Full Participation in Practice",""),
 ("MIA","Darrell Baker Jr.","CB","Knee","Full Participation in Practice","Questionable"),
 ("MIA","Chris Bell","WR","Knee","Did Not Participate In Practice","Doubtful"),
 ("MIA","Aaron Brewer","C","Concussion","Did Not Participate In Practice","Out"),
 ("MIA","Malik Herring","DE","","Full Participation in Practice",""),
 ("MIA","Will Kacmarek","TE","","Full Participation in Practice",""),
 ("MIA","Michael Taaffe","S","","Full Participation in Practice",""),
 ("MIA","Dante Trader Jr.","S","","Full Participation in Practice",""),
 ("MIA","Jared Wayne","WR","Quadricep","Did Not Participate In Practice","Out"),
 ("MIA","Jaylen Wright","RB","","Full Participation in Practice",""),

 ("IND","Mo Alie-Cox","TE","Groin","Did Not Participate In Practice","Out"),
 ("IND","CJ Allen","LB","","Full Participation in Practice",""),
 ("IND","Jaylon Carlies","LB","Neck","Did Not Participate In Practice","Out"),
 ("IND","Akeem Davis-Gaither","LB","Knee","Did Not Participate In Practice","Out"),
 ("IND","A.J. Haulcy","S","","Full Participation in Practice",""),
 ("IND","Arden Key","DE","","Full Participation in Practice",""),
 ("IND","Will Mallory","TE","Hamstring","Limited Participation in Practice","Questionable"),
 ("IND","Luke Rhodes","LS","Hamstring","Did Not Participate In Practice","Out"),
 ("IND","Grover Stewart","DT","","Full Participation in Practice",""),
 ("IND","Jonathan Taylor","RB","","Full Participation in Practice",""),
 ("IND","Jerry Tillery","DT","Calf","Did Not Participate In Practice","Out"),
 ("IND","Jalen Travis","T","Knee","Did Not Participate In Practice","Out"),
 ("IND","Justin Walley","CB","","Full Participation in Practice",""),
 ("IND","Charvarius Ward","CB","","Full Participation in Practice",""),

 ("CAR","Jonathon Brooks","RB","Groin","Limited Participation in Practice","Doubtful"),
 ("CAR","Brady Christensen","G","Hamstring","Full Participation in Practice","Questionable"),
 ("CAR","Trevor Etienne","RB","","Full Participation in Practice",""),
 ("CAR","Chuba Hubbard","RB","","Full Participation in Practice",""),
 ("CAR","Lee Hunter","DT","","Full Participation in Practice",""),
 ("CAR","Mike Jackson","CB","Groin","Limited Participation in Practice","Doubtful"),
 ("CAR","Will Lee III","CB","Hamstring","Limited Participation in Practice","Questionable"),
 ("CAR","Xavier Legette","WR","Knee","Full Participation in Practice","Questionable"),
 ("CAR","Damien Lewis","G","","Full Participation in Practice",""),
 ("CAR","Bobby Okereke","LB","Foot","Did Not Participate In Practice","Out"),
 ("CAR","Jaelan Phillips","LB","Hamstring","Full Participation in Practice","Questionable"),
 ("CAR","Torricelli Simpkins III","G","","Full Participation in Practice",""),

 ("NO","Kelvin Banks Jr.","T","","Full Participation in Practice",""),
 ("NO","CJ Donaldson","RB","Shoulder","Did Not Participate In Practice","Out"),
 ("NO","David Edwards","G","","Full Participation in Practice",""),
 ("NO","Martin Emerson","CB","Shin","Limited Participation in Practice","Questionable"),
 ("NO","Travis Etienne","RB","Hamstring","Full Participation in Practice","Questionable"),
 ("NO","Noah Fant","TE","","Full Participation in Practice",""),
 ("NO","Taliese Fuaga","T","Knee","Did Not Participate In Practice","Out"),
 ("NO","Alvin Kamara","RB","","Full Participation in Practice",""),
 ("NO","Erik McCoy","C","Biceps","Did Not Participate In Practice","Out"),
 ("NO","Christen Miller","DT","Knee","Did Not Participate In Practice","Out"),
 ("NO","Asim Richards","T","","Full Participation in Practice",""),
 ("NO","Quincy Riley","CB","","Full Participation in Practice",""),

 ("HOU","Azeez Al-Shaair","LB","Groin, Not injury related - personal matter","Did Not Participate In Practice","Out"),
 ("HOU","Will Anderson Jr.","DE","Ankle","Did Not Participate In Practice","Questionable"),
 ("HOU","Reed Blankenship","S","","Full Participation in Practice",""),
 ("HOU","Trent Brown","T","Wrist, Illness","Did Not Participate In Practice","Questionable"),
 ("HOU","Tank Dell","WR","","Full Participation in Practice",""),
 ("HOU","Blake Fisher","T","","Full Participation in Practice",""),
 ("HOU","Marvin Harrison Jr.","WR","Hamstring","Did Not Participate In Practice","Out"),
 ("HOU","Jacob Hummel","LB","Groin","Full Participation in Practice","Questionable"),
 ("HOU","Danielle Hunter","DE","Hamstring","Did Not Participate In Practice","Out"),
 ("HOU","Brevin Jordan","TE","Finger, Foot","Did Not Participate In Practice","Out"),
 ("HOU","Woody Marks","RB","","Full Participation in Practice",""),
 ("HOU","David Montgomery","RB","Groin","Full Participation in Practice","Questionable"),
 ("HOU","Keylan Rutledge","G","Neck, Shoulder","Did Not Participate In Practice","Out"),
 ("HOU","Jaylin Smith","CB","Hamstring","Full Participation in Practice","Questionable"),
 ("HOU","Wyatt Teller","G","Illness, Back","Limited Participation in Practice","Questionable"),
 ("HOU","Tommy Togiai","DT","","Full Participation in Practice",""),

 ("CLE","Austin Barber","T","","Full Participation in Practice",""),
 ("CLE","Denzel Boston","WR","Toe","Limited Participation in Practice","Questionable"),
 ("CLE","Michael Burton","FB","Calf","Did Not Participate In Practice","Out"),
 ("CLE","Maliek Collins","DT","","Full Participation in Practice",""),
 ("CLE","Harold Fannin Jr.","TE","","Full Participation in Practice",""),
 ("CLE","Ronnie Hickman Jr.","S","Concussion","Did Not Participate In Practice","Out"),
 ("CLE","Tytus Howard","T","","Full Participation in Practice",""),
 ("CLE","Elgton Jenkins","C","","Full Participation in Practice",""),
 ("CLE","Donovan McMillon","S","","Limited Participation in Practice",""),
 ("CLE","Carson Schwesinger","LB","","Full Participation in Practice",""),
 ("CLE","Denzel Ward","CB","","Limited Participation in Practice",""),
 ("CLE","Quincy Williams","LB","","Full Participation in Practice",""),

 ("LA","Davis Allen","TE","Oblique","Limited Participation in Practice","Questionable"),
 ("LA","Steve Avila","G","Hamstring","Did Not Participate In Practice","Out"),
 ("LA","Joe Cardona","LS","Ankle","Limited Participation in Practice","Questionable"),
 ("LA","Kam Curl","S","Toe","Limited Participation in Practice","Questionable"),
 ("LA","Aaron Donald","DT","","Did Not Participate In Practice",""),
 ("LA","Terrance Ferguson","TE","Ankle, Hamstring","Did Not Participate In Practice","Out"),
 ("LA","Braden Fiske","DT","","Did Not Participate In Practice",""),
 ("LA","Myles Garrett","LB","Knee, Not injury related - resting player","Did Not Participate In Practice","Questionable"),
 ("LA","Tyler Higbee","TE","","Limited Participation in Practice",""),
 ("LA","Trent McDuffie","CB","Back","Limited Participation in Practice","Questionable"),
 ("LA","Puka Nacua","WR","","Did Not Participate In Practice",""),
 ("LA","Colby Parkinson","TE","","Full Participation in Practice",""),
 ("LA","Matthew Stafford","QB","","Full Participation in Practice",""),
 ("LA","Byron Young","LB","","Did Not Participate In Practice",""),

 ("AZ","Budda Baker","S","","Full Participation in Practice",""),
 ("AZ","Zachary Carter","DT","Knee","Limited Participation in Practice","Out"),
 ("AZ","Hjalte Froholdt","C","Concussion","Did Not Participate In Practice","Out"),
 ("AZ","Jon Gaines II","G","Ankle","Did Not Participate In Practice","Out"),
 ("AZ","Bam Knight","RB","","Full Participation in Practice",""),
 ("AZ","Hunter Long","TE","Knee","Limited Participation in Practice","Questionable"),
 ("AZ","Roy Lopez","DT","Toe, Ankle","Limited Participation in Practice","Questionable"),
 ("AZ","Max Melton","CB","Knee, Hand","Limited Participation in Practice","Questionable"),
 ("AZ","Darius Robinson","DT","Wrist","Limited Participation in Practice","Questionable"),
 ("AZ","Isaac Seumalo","G","","Full Participation in Practice",""),
 ("AZ","Dante Stills","DT","","Full Participation in Practice",""),
 ("AZ","Josh Sweat","LB","","Full Participation in Practice",""),
 ("AZ","Jayden Williams","T","Knee","Limited Participation in Practice","Questionable"),
 ("AZ","Mack Wilson","LB","","Full Participation in Practice",""),
 ("AZ","Andrew Wingard","S","Groin","Did Not Participate In Practice","Questionable"),

 ("SEA","AJ Barner","TE","","Full Participation in Practice",""),
 ("SEA","Anthony Bradford","G","","Full Participation in Practice",""),
 ("SEA","Charles Cross","T","Ankle","Did Not Participate In Practice","Out"),
 ("SEA","Sam Darnold","QB","Ribs, Quadricep","Did Not Participate In Practice","Out"),
 ("SEA","Derick Hall","LB","","Did Not Participate In Practice",""),
 ("SEA","Drew Lock","QB","","Limited Participation in Practice",""),
 ("SEA","Quenton Nelson","G","Knee","Did Not Participate In Practice","Out"),
 ("SEA","Uchenna Nwosu","LB","","Full Participation in Practice",""),
 ("SEA","Patrick O'Connell","LB","","Full Participation in Practice",""),
 ("SEA","Connor O'Toole","LB","","Full Participation in Practice",""),
 ("SEA","Brandon Pili","DT","","Full Participation in Practice",""),
 ("SEA","Jarran Reed","DT","","Full Participation in Practice",""),
 ("SEA","Rashid Shaheed","WR","","Full Participation in Practice",""),
 ("SEA","Jaxon Smith-Njigba","WR","","Full Participation in Practice",""),
 ("SEA","Leonard Williams","DT","Stinger","Did Not Participate In Practice","Out"),

 ("LV","Thomas Booker","DT","Ankle","Full Participation in Practice","Questionable"),
 ("LV","Foley Fatukasi","DT","","Full Participation in Practice",""),
 ("LV","Ian Thomas","TE","","Full Participation in Practice",""),
 ("LV","Dont'e Thornton Jr.","WR","Back","Did Not Participate In Practice","Questionable"),
 ("LV","Trey Zuhn III","C","","Full Participation in Practice",""),

 ("SF","Mike Evans","WR","Achilles","Did Not Participate In Practice","Out"),
 ("SF","Renardo Green","CB","Back","Limited Participation in Practice","Questionable"),
 ("SF","Dre Greenlaw","LB","Knee","Limited Participation in Practice","Questionable"),
 ("SF","Nate Hobbs","CB","Groin","Full Participation in Practice","Questionable"),
 ("SF","Deommodore Lenoir","CB","Foot","Limited Participation in Practice","Questionable"),
 ("SF","Christian McCaffrey","RB","","Full Participation in Practice",""),
 ("SF","Siran Neal","S","","Full Participation in Practice",""),
 ("SF","Demarcus Robinson","WR","","Full Participation in Practice",""),
 ("SF","Deebo Samuel Sr.","WR","","Full Participation in Practice",""),
 ("SF","Upton Stout","CB","Shoulder, Neck","Limited Participation in Practice","Questionable"),
 ("SF","C.J. West","DT","Knee","Full Participation in Practice","Questionable"),
 ("SF","Trent Williams","T","Shoulder","Did Not Participate In Practice","Questionable"),

 ("DAL","DaRon Bland","CB","Ankle","Limited Participation in Practice","Questionable"),
 ("DAL","Jonathan Bullard","DT","Calf","Full Participation in Practice","Questionable"),
 ("DAL","Alijah Clark","S","Illness","Did Not Participate In Practice","Questionable"),
 ("DAL","Donovan Ezeiruaku","LB","Ankle","Did Not Participate In Practice","Out"),
 ("DAL","Jake Ferguson","TE","Knee, Ankle","Did Not Participate In Practice","Out"),
 ("DAL","Tyler Goodson","RB","Ankle, Knee","Did Not Participate In Practice","Out"),
 ("DAL","Malik Hooker","S","","Did Not Participate In Practice",""),
 ("DAL","Marist Liufau","LB","","Full Participation in Practice",""),
 ("DAL","P.J. Locke","S","Concussion","Did Not Participate In Practice","Out"),
 ("DAL","Von Miller","LB","","Did Not Participate In Practice",""),
 ("DAL","Jonathan Mingo","WR","Ankle","Did Not Participate In Practice","Out"),
 ("DAL","Devin Moore","CB","Hip","Full Participation in Practice","Questionable"),
 ("DAL","DeMarvion Overshown","LB","","Full Participation in Practice",""),
 ("DAL","George Pickens","WR","","Full Participation in Practice",""),
 ("DAL","Joey Porter Jr.","CB","Ankle, Foot","Limited Participation in Practice","Questionable"),
 ("DAL","Luke Schoonmaker","TE","","Full Participation in Practice",""),
 ("DAL","Brevyn Spann-Ford","TE","","Full Participation in Practice",""),
 ("DAL","Juanyeh Thomas","S","Hamstring","Did Not Participate In Practice","Doubtful"),
 ("DAL","KaVontae Turpin","WR","","Full Participation in Practice",""),

 ("PIT","Brandin Echols","CB","","Full Participation in Practice",""),
 ("PIT","DeShon Elliott","S","","Full Participation in Practice",""),
 ("PIT","Derrick Harmon","DT","Foot","Full Participation in Practice","Questionable"),
 ("PIT","Cameron Heyward","DT","","Full Participation in Practice",""),
 ("PIT","Ben Skowronek","WR","","Full Participation in Practice",""),
 ("PIT","Doneiko Slaughter","CB","","Full Participation in Practice",""),
 ("PIT","Darnell Washington","TE","","Full Participation in Practice",""),
 ("PIT","T.J. Watt","LB","","Full Participation in Practice",""),

 ("CIN","Jonathan Allen","DT","","Limited Participation in Practice",""),
 ("CIN","Jalen Davis","CB","Hamstring","Full Participation in Practice","Doubtful"),
 ("CIN","Kyle Dugger","S","Quadricep","Did Not Participate In Practice","Out"),
 ("CIN","Dylan Fairchild","G","","Full Participation in Practice",""),
 ("CIN","B.J. Hill","DT","","Did Not Participate In Practice",""),
 ("CIN","Andrei Iosivas","WR","Thumb","Full Participation in Practice","Doubtful"),
 ("CIN","Dexter Lawrence","DT","","Did Not Participate In Practice",""),
 ("CIN","Brian Parker II","G","Knee","Full Participation in Practice","Doubtful"),
 ("CIN","DJ Turner II","CB","","Full Participation in Practice",""),

 ("LAC","Kayode Awosika","G","Fibula","Full Participation in Practice","Questionable"),
 ("LAC","Bud Dupree","DE","","Full Participation in Practice",""),
 ("LAC","Justin Eboigbe","DE","Ankle","Limited Participation in Practice","Questionable"),
 ("LAC","Alex Harkey","G","","Full Participation in Practice",""),
 ("LAC","Tre Harris","WR","","Full Participation in Practice",""),
 ("LAC","Cam Hart","CB","","Full Participation in Practice",""),
 ("LAC","Daiyan Henley","LB","","Full Participation in Practice",""),
 ("LAC","Deane Leonard","CB","","Full Participation in Practice",""),
 ("LAC","Khalil Mack","LB","","Full Participation in Practice",""),
 ("LAC","Ladd McConkey","WR","Back","Did Not Participate In Practice","Questionable"),
 ("LAC","Keaton Mitchell","RB","","Full Participation in Practice",""),
 ("LAC","David Njoku","TE","Fibula","Full Participation in Practice","Questionable"),
 ("LAC","Denzel Perryman","LB","Pectoral","Full Participation in Practice","Questionable"),
 ("LAC","Trey Pipkins","T","Not injury related - personal matter, Knee","Limited Participation in Practice","Questionable"),
 ("LAC","Rodney Shelley","CB","","Full Participation in Practice",""),
 ("LAC","Branson Taylor","G","Ankle","Did Not Participate In Practice","Out"),
 ("LAC","Brenen Thompson","WR","Hamstring","Did Not Participate In Practice","Doubtful"),
 ("LAC","Isas Waxter","CB","Ankle","Did Not Participate In Practice","Out"),
 ("LAC","Kendall Williamson","S","Calf","Did Not Participate In Practice","Out"),

 ("BAL","Rasheen Ali","RB","","Full Participation in Practice",""),
 ("BAL","Rashod Bateman","WR","","Full Participation in Practice",""),
 ("BAL","Calais Campbell","DT","","Did Not Participate In Practice",""),
 ("BAL","Kyle Hamilton","S","","Full Participation in Practice",""),
 ("BAL","Jaylinn Hawkins","S","Knee","Limited Participation in Practice","Out"),
 ("BAL","Matthew Hibner","TE","","Full Participation in Practice",""),
 ("BAL","Olaivavega Ioane","G","","Full Participation in Practice",""),
 ("BAL","Adam Randall","RB","Neck, Hamstring","Full Participation in Practice","Questionable"),
 ("BAL","Ronnie Stanley","T","","Did Not Participate In Practice",""),
 ("BAL","Nate Wiggins","CB","","Full Participation in Practice",""),
]

# ----------------------------------------------------------------------------------
# RESULTS — settled scores read off SCHEDULE_URL, plus the two games not yet final.
# Each row carries the nfl.com game page that is the per-row official source.
# -------------------------------------------------------------------------------------
GAME_PAGE = {
 "W10-01": "https://www.nfl.com/games/commanders-at-giants-2026-reg-10",
 "W10-02": "https://www.nfl.com/games/patriots-at-lions-2026-reg-10",
 "W10-03": "https://www.nfl.com/games/chiefs-at-falcons-2026-reg-10",
 "W10-04": "https://www.nfl.com/games/texans-at-browns-2026-reg-10",
 "W10-05": "https://www.nfl.com/games/vikings-at-packers-2026-reg-10",
 "W10-06": "https://www.nfl.com/games/dolphins-at-colts-2026-reg-10",
 "W10-07": "https://www.nfl.com/games/panthers-at-saints-2026-reg-10",
 "W10-08": "https://www.nfl.com/games/bills-at-jets-2026-reg-10",
 "W10-09": "https://www.nfl.com/games/jaguars-at-titans-2026-reg-10",
 "W10-10": "https://www.nfl.com/games/rams-at-cardinals-2026-reg-10",
 "W10-11": "https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10",
 "W10-12": "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10",
 "W10-13": "https://www.nfl.com/games/steelers-at-bengals-2026-reg-10",
 "W10-14": "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10",
}

# game_id, away, home, away_pts, home_pts, state_as_published, page_order
RESULTS = [
 ("W10-01","WAS","NYG",24,21,"FINAL, Thursday, November 12th","TNF"),
 ("W10-02","NE","DET",10,35,"FINAL, Sunday, November 15th (Munich)","International Game"),
 ("W10-03","KC","ATL",35,13,"FINAL, Sunday, November 15th","1:00 PM"),
 ("W10-04","HOU","CLE",24,27,"FINAL, Sunday, November 15th","1:00 PM"),
 ("W10-05","MIN","GB",30,10,"FINAL, Sunday, November 15th","1:00 PM"),
 ("W10-06","MIA","IND",22,24,"FINAL, Sunday, November 15th","1:00 PM"),
 ("W10-07","CAR","NO",20,17,"FINAL, Sunday, November 15th","1:00 PM"),
 ("W10-08","BUF","NYJ",31,12,"FINAL, Sunday, November 15th","1:00 PM"),
 ("W10-09","JAX","TEN",40,23,"FINAL, Sunday, November 15th","1:00 PM"),
 ("W10-10","LA","AZ",34,6,"FINAL, Sunday, November 15th","4:05 PM"),
 ("W10-11","SEA","LV",21,13,"FINAL, Sunday, November 15th","4:05 PM"),
 ("W10-12","SF","DAL",46,40,"FINAL, Sunday, November 15th","4:25 PM"),
 ("W10-13","PIT","CIN",None,None,"KICKOFF 8:20 PM ET 2026-11-15 = 2026-11-16T01:20Z; in progress at capture, no final score","SNF"),
 ("W10-14","LAC","BAL",None,None,"KICKOFF 8:15 PM ET 2026-11-16 = 2026-11-17T01:15Z; not yet played at capture","MNF"),
]


def normalised_injury_blob() -> bytes:
    """Canonical form of the transcription: club, then page order, all six fields."""
    lines = ["club\tplayer\tposition\tinjury\tpractice\tgame_status"]
    for club, player, pos, inj, prac, game in INJURY_ROWS:
        lines.append("\t".join([club, player, pos, inj, prac, game]))
    return ("\n".join(lines) + "\n").encode("utf-8")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)

    blob = normalised_injury_blob()
    digest = hashlib.sha256(blob).hexdigest()

    inj_path = os.path.join(OUT, "week10_injuries_2026-11-16.csv")
    with open(inj_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["club", "player", "position", "injury", "practice_status", "game_status",
                    "capture_utc", "source_url", "row_hash_scope"])
        for club, player, pos, inj, prac, game in INJURY_ROWS:
            w.writerow([club, player, pos, inj, prac, game,
                        INJURY_CAPTURED_UTC, INJURY_URL, digest[:16]])

    res_path = os.path.join(OUT, "week10_results_2026-11-16.csv")
    with open(res_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["game_id", "away", "home", "away_pts", "home_pts", "state_as_published",
                    "capture_utc", "game_page", "schedule_url"])
        for gid, away, home, ap, hp, state, _slot in RESULTS:
            w.writerow([gid, away, home, "" if ap is None else ap,
                        "" if hp is None else hp, state,
                        RESULTS_CAPTURED_UTC, GAME_PAGE[gid], SCHEDULE_URL])

    manifest = {
        "generated_by": "scripts/capture_official.py",
        "provenance_note": (
            "Hash is SHA-256 of the normalised transcription produced by this script, NOT of "
            "NFL.com's raw HTTP bytes. See module docstring."
        ),
        "captures": [
            {
                "file": "data/captures/week10_injuries_2026-11-16.csv",
                "url": INJURY_URL,
                "captured_utc": INJURY_CAPTURED_UTC,
                "rows": len(INJURY_ROWS),
                "clubs": len({r[0] for r in INJURY_ROWS}),
                "with_game_designation": sum(1 for r in INJURY_ROWS if r[5]),
                "sha256_normalised": digest,
            },
            {
                "file": "data/captures/week10_results_2026-11-16.csv",
                "url": SCHEDULE_URL,
                "captured_utc": RESULTS_CAPTURED_UTC,
                "rows": len(RESULTS),
                "final": sum(1 for r in RESULTS if r[3] is not None),
                "sha256_normalised": hashlib.sha256(
                    json.dumps(RESULTS, sort_keys=True).encode()).hexdigest(),
            },
        ],
    }
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
        fh.write("\n")

    print(f"injuries : {len(INJURY_ROWS)} rows, {manifest['captures'][0]['clubs']} clubs, "
          f"{manifest['captures'][0]['with_game_designation']} with a game designation")
    print(f"results  : {len(RESULTS)} rows, {manifest['captures'][1]['final']} final")
    print(f"sha256   : {digest}")


if __name__ == "__main__":
    main()
