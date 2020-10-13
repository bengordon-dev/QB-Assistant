import discord
from discord.utils import get
import time

# Google Sheets API stuff. See https://www.youtube.com/watch?v=vISRn5qFrkM for details.
# This could also probably be done in Excel but whatever sheets rocks n rules
# Sheet needs to be an NAQT online scoresheet https://www.naqt.com/downloads/scoresheet-electronic.xlsx 
# uploaded to Google Drive and saved as a Google Sheet.
import gspread
from gspread.exceptions import SpreadsheetNotFound
from oauth2client.service_account import ServiceAccountCredentials
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
sheets_client = gspread.authorize(creds)


client = discord.Client()

state = { # Several important state variables I decided to keep in the same place.
    "reset": True,
    "ready": False,
    "tossup": 1,
    "tossup player": "",
    "bonus team": "",
    "awaiting sheet": False,
    "sheet": "", # Needs to be initialized with the link sheet command. Eventually a sheets_client.open(message.content).sheet1 object 
    "max players": 6, # sheet tings
    "red score": 0,
    "red tossups": {},
    "red bonuses": [],
    "blue score": 0,
    "blue tossups": {},
    "blue bonuses": [],
}

def is_admin(user): # Returns true if the user has the Captain or Moderator role. Controls who gets to control the bot.
    roles = [x.id for x in user.roles]
    if (731169067901124678 in roles) or (735240204222464021 in roles):
        return True
    else:
        return False

def team(user): # A string, depends on what roles the user has. Very important
    roles = [x.id for x in user.roles]

    if (731169562879328316 in roles) and (731169675697717328 in roles):
        return "both"
    elif 731169562879328316 in roles:
        return "red"
    elif 731169675697717328 in roles:
        return "blue"
    else:
        return "neither"

def other_team(team):
    if team == "blue":
        return "red"
    if team == "red":
        return "blue"
    return "write better code lol"

def team_color(user): # useful shorthand. Possibilities include blue, red, gray, or purple.
    if team(user) == "both":
        return discord.Color(0xff00ff)
    elif team(user) == "red":
        return discord.Color(0xff0000)
    elif team(user) == "blue":
        return discord.Color(0x0000ff)
    else:
        return discord.Color(0x999999)

async def reset(channel, unmute_people=True, add_embed=True): # Equivalent to the reset button on a physical buzzer box. Resets state variables to allow someone else to buzz, unmutes everyone.
    if not state["reset"]:
        state["reset"] = True
        
        if add_embed:
            embed = discord.Embed(
                title = "Reset buzzer box",
                description = "Buzz away!",
                color = discord.Color(0x00ff00)
            )
            await channel.send(embed=embed)
    if unmute_people:
        for user in client.get_channel(731169225745498152).members: 
            await user.edit(mute=False)
    state["bonus team"] = ""
    state["tossup player"] = ""


async def buzz(message): # The one command any player can run. Whoever buzzes first gets to answer!
    if state["reset"]:
        desc = ""
        if team(message.author) == "both":
            desc = f"{message.author} appears to be on both teams! Award the bonus to whoever should get it."
        elif team(message.author) == "neither":
            desc = "Nice buzz!"
        else:
            desc = f"If they are right, the {team(message.author)} team gets the bonus!"

        embed = discord.Embed(
            title = (f'{message.author.display_name} buzzed first!'),
            description = desc,
            color = team_color(message.author)
        )
        state["reset"] = False
        state["tossup player"] = message.author
        await message.channel.send(embed=embed)

async def bonus_init(message, winTeam): # Allows one team to confer during a bonus by muting everybody else.
    muteTeam = ""
    if winTeam == "red":
        muteTeam = "blue"
    if winTeam == "blue":
        muteTeam = "red"

    if muteTeam: #if a valid team was entered, pretty much
        state["bonus team"] = winTeam
        for user in client.get_channel(731169225745498152).members:
            if team(user) == muteTeam:
                await user.edit(mute=True)


async def begin(message): # Equivalent to flipping the "run/pause" switch on a buzzer box. Lets people buzz in for the first tossup
    embed = discord.Embed(
        title = ("The match has begun!"),
        description = "Buzz whenever you know the answer!",
        color = discord.Color(0x00ff00)
    )
    state["ready"] = True

    await initialize_memory(message)
        

    await message.channel.send(embed=embed)

async def initialize_memory(message):
    for x in range(0, 24):
        state["red bonuses"].append([])
        state["blue bonuses"].append([])

    state["red tossups"] = {}
    state["blue tossups"] = {}
    #initialize internal scorekeeping
    for user in client.get_channel(731169225745498152).members: 
        if team(user) == 'red':
            state["red tossups"][user.id] = [""]*24
        elif team(user) == 'blue':
            state["blue tossups"][user.id] = [""]*24
        else:
            await message.channel.send(f"Please assign **{user.display_name}** a valid team!")

async def update_memory(message):
    for user in client.get_channel(731169225745498152).members: 
        if (team(user) == 'red'):
            if (user.id not in state["red tossups"].keys()):
                state["red tossups"][user.id] = [""]*24
                await message.channel.send(f"Player **{user.display_name}** added to the **red** team")
        elif (team(user) == 'blue'):
            if (user.id not in state["blue tossups"].keys()):
                state["blue tossups"][user.id] = [""]*24
                await message.channel.send(f"Player **{user.display_name}** added to the **blue** team")
        else:
            await message.channel.send(f"Please assign **{user.display_name}** a valid team!")

async def new_match(message): # Runs reset, brings the tossup variable back to 1 and unlinks the sheet.
    await reset(message.channel)
    state["tossup"] = 1
    state["sheet"] = ""
    await initialize_memory(message)
    await message.channel.send(f'Game reset!')

async def next_tossup(message): #self-explanatory.
    await reset(message.channel)
    state["tossup"] += 1
    await message.channel.send(f'Tossup **{state["tossup"]}**')


# Google Sheets stuff. 2 separate functions for user friendly reasons.
async def link_sheet_p1(message):
    await message.channel.send("What is the name of your spreadsheet?")
    state["awaiting sheet"] = True

# The sheet needs to be shared with the email of your API application. If it is shared you should just be able to type in its name - make sure the sheet's name is unique!
async def link_sheet_p2(message):
    state["awaiting sheet"] = False
    try:
        state["sheet"] = sheets_client.open(message.content).sheet1 # The NAQT electronic scoresheet file has only one sheet in it.
        await message.channel.send(f'Successfully linked sheet **{message.content}**')
    except SpreadsheetNotFound:
        state["sheet"] = ""
        await message.channel.send(f'Invalid spreadsheet name')

async def insert_player(user, message, alert_already_existing=False):
    cells = []
    if team(user) == "red":
        cells = list(range(2, 2+state["max players"]))
    elif team(user) == "blue":
        cells = list(range(8+state["max players"], 8+(2 * state["max players"])))
    for col in cells:
        if state["sheet"].cell(7, col).value == user.display_name: # user already in that team
            if alert_already_existing:
                await message.channel.send(f"**{user.display_name}** cannot exist in the **{team(user)}** team more than once!")
            break
        if not state["sheet"].cell(7, col).value: # blank 
            state["sheet"].update_cell(7, col, user.display_name)
            await message.channel.send(f"Added **{user.display_name}** in column **{col}**")
            break
        if col == cells[-1] and state["sheet"].cell(7, col).value:
            await message.channel.send(f"The **{team(user)}** team already has 6 players! **{user.display_name}** was unable to be added to the sheet.")

    if not cells:
        await message.channel.send(f"Please assign {user.display_name} a valid team!")

async def load_sheet(message):
    if state["sheet"]:
        for user in client.get_channel(731169225745498152).members: 
            await insert_player(user, message, alert_already_existing=True)
    else:
        await message.channel.send("Please link a sheet!")

async def update_sheet(message): 
    if state["sheet"]:
        for user in client.get_channel(731169225745498152).members: 
            await insert_player(user, message, alert_already_existing=False)
    else:
        await message.channel.send("Please link a sheet!")

def get_column(player): # Gets the column in the linked sheet corresponding to a display name.
    #print(team(player))
    if state["sheet"] != "":
        possible_cols = []
        if team(player) == "red":
            possible_cols = range(2, 2+state["max players"])
        else:
            if team(player) == "blue":
                possible_cols = range(8+state["max players"], 8+(2 * state["max players"]))
        #print(possible_cols)
        """else:
            possible_cols = (range(2, 8)) + (range(14, 20))"""
        for col in possible_cols:
            if state["sheet"].cell(7, col).value == player.display_name:
                return col
        return "no column found"
    else:
        return "no linked sheet"

async def tossup_score(message):
    if state["tossup player"]:
        if message.content.lower().split()[1] in ["neg", "incorrect", "-5", "none", "zero", "0", "ten", "10", "power", "15"]:
            if (state["tossup player"]).id in (state["red tossups"]).keys() or (state["tossup player"]).id in (state["blue tossups"]).keys():
                score = 0
                embed_title = ""
                embed_color = discord.Color(0x999999)
                embed_desc = ""
                if message.content.lower().split()[1] in ["neg", "incorrect", "-5"]:
                    score = -5
                    embed_title = "Incorrect interrupt!"
                    embed_desc = f"The **{team(state['tossup player'])}** team loses 5 points! They cannot buzz for the remainder of this tossup."
                if message.content.lower().split()[1] in ["none", "zero", "0"]:
                    embed_title = "Incorrect!"
                    embed_desc = f"As the buzz occured after the end of the question, the **{team(state['tossup player'])}** team loses no points. They cannot buzz for the remainder of this tossup."
                if message.content.lower().split()[1] in ["ten", "10"]:
                    score = 10
                    embed_title = "Correct!"
                    embed_desc = f"The **{team(state['tossup player'])}** team gets 10 points and a chance to answer 3 bonus questions."
                    embed_color = team_color(state["tossup player"])
                if message.content.lower().split()[1] in ["power", "15"]:
                    score = 15
                    embed_title = "Power!"
                    embed_desc = f"Nice buzz! The **{team(state['tossup player'])}** team gets 15 points and a chance to answer 3 bonus questions."
                    embed_color = team_color(state["tossup player"])

                state[team(state["tossup player"]) + " tossups"][(state["tossup player"]).id][state["tossup"] - 1] = score
                state[team(state["tossup player"]) + " score"] += score

                if state["sheet"]:
                    state["sheet"].update_cell(state["tossup"]+7, get_column(state["tossup player"]), score)

                embed = discord.Embed(
                    title = embed_title,
                    description = embed_desc,
                    color = embed_color
                )
                await message.channel.send(embed=embed)

                if message.content.lower().split()[1] in ["neg", "incorrect", "-5", "none", "zero", "0"]: #reset if the answer was wrong
                    await reset(message.channel, unmute_people=False, add_embed=False)
                if message.content.lower().split()[1] in ["ten", "10", "power", "15"]: #move to the bonus if the answer was wrong
                    await bonus_init(message, team(state['tossup player']))
            else:
                await message.channel.send("Player not found in memory.")
        else:
            await message.channel.send("Possible score values include neg, incorrect, -5, none, zero, 0, ten, 10, power, and 15")
    else:
        await message.channel.send("To score a tossup, a player must have buzzed in after the last reset.")
  
                
               


async def bonus_score(message): # Ran by the moderator with "bonus score [y/n][y/n][y/n]" after a bonus has been answered. 
    if state["bonus team"]:
        data = message.content.lower().split()[2]

        col_offset = 8
        if state["bonus team"] == "blue":
            col_offset = 20
        
        score = 0
        
        for bonus_question in range(0, 3):
            if data[bonus_question] in ["y", "1"]:
                if state["sheet"]:
                    state["sheet"].update_cell(state["tossup"]+7, col_offset+bonus_question, 10)
                score += 10
                state[state["bonus team"] + " bonuses"][state["tossup"] - 1].append(True)
            else:
                if state["sheet"]:
                    state["sheet"].update_cell(state["tossup"]+7, col_offset+bonus_question, 0)
                state[state["bonus team"] + " bonuses"][state["tossup"] - 1].append(False)
        embed_desc = ""
        embed_color = discord.Color(0x999999)

        state[state["bonus team"] + " score"] += score
        if score == 0:
            embed_desc = "Better luck next time!"
        elif score == 10:
            embed_desc = "At least you got one!"
            if data[2] in ["y", "1"]: #only the last one correct
                embed_desc = "At least you got the last one!"
            if data[0] in ["y", "1"]: #only the first one correct
                embed_desc = "You got the first one but not the rest!"
            embed_color = discord.Color(0x66bb66)
        elif score == 20:
            embed_desc = "A respectable effort."
            if data[2] in ["n", "0"]: #only the last one wrong
                embed_desc = "Aww man, you almost got all three!"
            embed_color = discord.Color(0x33dd33)
        elif score == 30:
            embed_desc = "Nailed it! Good job."
            embed_color = discord.Color(0x00ff00)

        embed = discord.Embed(
            title = f"{score} points on the bonus!",
            description = embed_desc,
            color = embed_color
        )
        await message.channel.send(embed=embed)
    else:
        await message.channel.send("Make sure a sheet has linked and a team has been assigned the bonus!")

async def score_check(message):
    red_score = state["red score"]
    blue_score = state["blue score"]
    print(state["red tossups"])
    print(state["red bonuses"])
    print(state["blue tossups"])
    print(state["blue bonuses"])
    if state["sheet"]:
        red_score = int(state["sheet"].cell(45, 2).value)
        blue_score = int(state["sheet"].cell(45, 8+state["max players"]).value)
        
    embed_color = discord.Color(0x999999)
    embed_desc = f"After {state['tossup'] - 1} tossups, the game is all tied up!"

    if red_score > blue_score:
        embed_color = discord.Color(0xff0000)
        embed_desc = f"After {state['tossup'] - 1} tossups, the red team is ahead!"
    if blue_score > red_score:
        embed_color = discord.Color(0x0000ff)
        embed_desc = f"After {state['tossup'] - 1} tossups, the blue team is ahead!"

    embed = discord.Embed(
        title = f"Red team {red_score}, Blue team {blue_score}!",
        description = embed_desc,
        color = embed_color
    )
    await message.channel.send(embed=embed)

async def bounceback(message): # lets the team NOT answering a bonus take a swing 
    for user in client.get_channel(731169225745498152).members:
        if team(user) == state["bonus team"]:
            await user.edit(mute=True)
        else:
            await user.edit(mute=False)
    await message.channel.send("Bounce!")

async def return_from_bounce(message): # returns to the state before the bounce - lets the team answering a bonus confer
    for user in client.get_channel(731169225745498152).members:
        if team(user) == state["bonus team"]:
            await user.edit(mute=False)
        elif is_admin(user) and team(user) != "neither":
            await user.edit(mute=False)
        else:
            await user.edit(mute=True)
    await message.channel.send("Back to normal.")

async def set_tossup(message):
    if len(message.content.split()) == 3:
        try: 
            state["tossup"] = int(message.content.lower().split()[2])
            await message.channel.send(f"Tossup **{state['tossup']}**")
        except ValueError:
            await message.channel.send("Tossup value must be set to a number")
    else:
        await message.channel.send("Proper format is `set tossup <tossup number>`")

async def take_attendance(message):
    file = open(f"./attendance/attendance {time.asctime()}.txt", "w")
    for user in client.get_channel(731169225745498152).members:
        file.write(user.display_name + '\n')
    file.close()
async def demask_players(message):
    for member in message.guild.members:
        if team(member) in ["red", "blue", "both"]:
            await member.remove_roles(get(message.guild.roles, id=731169562879328316), get(message.guild.roles, id=731169675697717328))
            #member.remove_roles(message.guild.roles.get("731169562879328316"), message.guild.roles.get("731169675697717328"))

@client.event
async def on_ready():
    print('Logged on as {0}!'.format(client.user))
    
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.channel.id == 731169045520449677:
        if state["ready"]:
            if message.content.lower() in ["buzz", "b"]:
                await buzz(message)
        if is_admin(message.author):
            if message.content.lower() in ["reset", "r"]:
                await reset(message.channel)
            if message.content.lower().startswith("bonus"):
                if message.content.lower().split()[1] == "score":
                    await bonus_score(message) # bonus score [y/n][y/n][y/n]
                else:
                    await bonus_init(message, message.content.lower().split()[1])
            if message.content.lower() in ["begin"]:
                await begin(message)
            if message.content.lower() in ["next"]:
                await next_tossup(message)
            if message.content.lower() in ["new game", "new match"]:
                await new_match(message)
            if state["awaiting sheet"]:
                await link_sheet_p2(message)
            if message.content.lower() in ["link sheet"]:
                await link_sheet_p1(message)
            if message.content.lower().startswith("tossup") or message.content.lower().startswith("tu"):
                await tossup_score(message)
            if message.content.lower() in ["load sheet"]:
                await load_sheet(message)
            if message.content.lower() in ["update sheet"]:
                await update_sheet(message)
            if message.content.lower() in ["score check"]:
                await score_check(message)
            if message.content.lower() in ["bounceback", "bounce"]:
                await bounceback(message)
            if message.content.lower() in ["return", "go back"]:
                await return_from_bounce(message)
            if message.content.lower().startswith("set tossup"):
                await set_tossup(message)
            if message.content.lower() in ["update memory"]:
                await update_memory(message)
            if message.content.lower() in ["demask all", "demask players"]:
                await demask_players(message)
            if message.content.lower() in ["take attendance"]:
                await take_attendance(message)
            if message.content.lower() in ["shut down", "shutdown"]:
                await message.channel.send("Au revoir!")
                await client.close()

client.run('Bot token here')