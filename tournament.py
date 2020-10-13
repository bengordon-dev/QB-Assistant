import discord
from discord.utils import get
import time
import copy

client = discord.Client()

role_names = { # ID's of each role needed for a tournament
    759864570646626335: "mod", #scrimmage moderator
    759864659611877426: "mod", #scrimmage organizer
    760233798880198716: "NCSSM A",
    760323910197313608: "NCSSM B",
    760234102497738764: "NCSSM C",
    760324001628160011: "NCSSM D",
    763231169595703298: "Ravenscroft A",
    763231344075341845: "Panther Creek A",
    763231967994314752: "Panther Creek B",
    763232157916332055: "Panther Creek C"
    
}

team_colors = { # colors of each role
    "NCSSM A": discord.Color(0x0099E1),
    "NCSSM B": discord.Color(0xF93A2F),
    "NCSSM C": discord.Color(0x00D166),
    "NCSSM D": discord.Color(0xF8C300),
    "Ravenscroft A": discord.Color(0xE67F22),
    "Panther Creek A": discord.Color(0x33E0D7),
    "Panther Creek B": discord.Color(0xFCE6A0),
    "Panther Creek C": discord.Color(0x7A2F8F)
}


new_channel_state = {
    "reset": True,
    "ready": False,
    "tossup": 1,
    "tossup player": "",
    "bonus team": "",
    "VC": 0,
    "team 1": "",
    "team 2": ""
}




state = {} # Several important state variables I decided to keep in the same place.

def is_admin(user): # Returns true if the user has the Captain or Moderator role. Controls who gets to control the bot.
    if "mod" in get_roles(user):
        return True
    else:
        return False

def get_roles(user): #important ones, that is
    role_list = [role_names[x.id] for x in user.roles if x.id in role_names.keys()]
    return role_list


def team(user, channel): # A string, depends on what roles the user has. Very important
    roles = get_roles(user)

    if (state[channel]["team 1"] in roles):
        if (state[channel]["team 2"] in roles):
            return "both"
        return state[channel]["team 1"]
    elif state[channel]["team 2"] in roles:
        return state[channel]["team 2"]
    return "neither"

def other_team(team, channel):
    if team == state[channel]["team 1"]:
        return state[channel]["team 2"]
    if team == state[channel]["team 2"]:
        return state[channel]["team 1"]
    return "write better code lol"

def team_color(user, channel): # useful shorthand. Possibilities include blue, red, gray, or purple.
    if team(user, channel) in team_colors.keys():
        return team_colors[team(user, channel)]
    return discord.Color(0x999999)

async def reset(channel, unmute_people=False, add_embed=True, is_bonus=False): # Equivalent to the reset button on a physical buzzer box. Resets state variables to allow someone else to buzz, unmutes everyone.
    if not state[channel]["reset"]:
        state[channel]["reset"] = True
        
        if add_embed:
            embed = discord.Embed(
                title = "Reset buzzer box",
                description = "Buzz away!",
                color = discord.Color(0x00ff00)
            )
            await channel.send(embed=embed)
    if unmute_people:
        await unmute_all(channel, is_bonus=is_bonus)
    state[channel]["bonus team"] = ""
    state[channel]["tossup player"] = ""

async def unmute_all(channel, is_bonus=False):
    for user in client.get_channel(state[channel]["VC"]).members: 
        if (is_bonus and team(user, channel) == other_team(state[channel]["bonus team"], channel)) or (not is_bonus): 
            await user.edit(mute=False)
    await channel.send(f"Unmuted all people in {client.get_channel(state[channel]['VC']).name}")



async def buzz(message): # The one command any player can run. Whoever buzzes first gets to answer!
    if state[message.channel]["reset"]:
        desc = ""
        if team(message.author, message.channel) == "both":
            desc = f"{message.author} appears to be on both teams! Award the bonus to whoever should get it."
        elif team(message.author, message.channel) == "neither":
            desc = "Nice buzz!"
        else:
            desc = f"If they are right, **{team(message.author, message.channel)}** gets the bonus!"

        embed = discord.Embed(
            title = (f'{message.author.display_name} buzzed first!'),
            description = desc,
            color = team_color(message.author, message.channel)
        )
        state[message.channel]["reset"] = False
        state[message.channel]["tossup player"] = message.author
        await message.channel.send(embed=embed)

async def bonus_init(message, winTeam): # Allows one team to confer during a bonus by muting everybody else.
    muteTeam = other_team(winTeam, message.channel)

    if muteTeam: #if a valid team was entered, pretty much
        state[message.channel]["bonus team"] = winTeam
        for user in client.get_channel(state[message.channel]['VC']).members:
            if team(user, message.channel) == muteTeam:
                await user.edit(mute=True)


async def begin(channel): # Equivalent to flipping the "run/pause" switch on a buzzer box. Lets people buzz in for the first tossup
    embed = discord.Embed(
        title = ("The match has begun!"),
        description = "Buzz whenever you know the answer!",
        color = discord.Color(0x00ff00)
    )
    state[channel]["ready"] = True        
    await channel.send(embed=embed)
    await channel.send("**Tossup 1**")



async def new_match(channel): # Runs reset, brings the tossup variable back to 1 and unlinks the sheet.
    await reset(channel, unmute_people=True)
    state[channel]["tossup"] = 1
    await channel.send(f'Game reset!\n**Tossup 1**')

async def next_tossup(message): #self-explanatory.
    await reset(message.channel, unmute_people=True, is_bonus=(state[message.channel]["bonus team"] != ""))
    state[message.channel]["tossup"] += 1
    await message.channel.send(f'Tossup **{state[message.channel]["tossup"]}**')

async def init_channel(channel, vc_id):
    state[channel] = copy.deepcopy(new_channel_state)
    state[channel]["VC"] = vc_id
    await channel.send(f"Intialized {channel.name} with voice channel {client.get_channel(vc_id).name}")



async def tu_response(message):
    if state[message.channel]["tossup player"]:
        if message.content.lower() in ["n", "no", "incorrect", "i"]:
            embed = discord.Embed(
                title = "Incorrect!",
                description = f"**{state[message.channel]['tossup player']}** was incorrect! **{team(state[message.channel]['tossup player'], message.channel)}** cannot buzz for the remainder of this tossup.",
                color = discord.Color(0x999999)
            )
            await message.channel.send(embed=embed)
            await reset(message.channel)
        if message.content.lower() in ["y", "yes", "correct"]:
            embed = discord.Embed(
                title = "Correct!",
                description = f"**{team(state[message.channel]['tossup player'], message.channel)}** gets a chance to answer 3 bonus questions.",
                color = team_color(state[message.channel]["tossup player"], message.channel)
            )
            await message.channel.send(embed=embed)
            await bonus_init(message, team(state[message.channel]['tossup player'], message.channel))

async def set_tossup(message):
    if len(message.content.split()) == 3:
        try: 
            state[message.channel]["tossup"] = int(message.content.lower().split()[2])
            await message.channel.send(f"Tossup **{state[message.channel]['tossup']}**")
        except ValueError:
            await message.channel.send("Tossup value must be set to a number")
    else:
        await message.channel.send("Proper format is `set tossup <tossup number>`")

async def set_team_1(channel, role_id):
    try:
        team_name = get(channel.guild.roles, id=role_id).name
        state[channel]["team 1"] = team_name
        await channel.send(f"Set team 1 to **{team_name}**")
    except AttributeError:
        await channel.send(f"Invalid role ID **{role_id}**")

async def set_team_2(channel, role_id):
    try:
        team_name = get(channel.guild.roles, id=role_id).name
        state[channel]["team 2"] = team_name
        await channel.send(f"Set team 2 to **{team_name}**")
    except AttributeError:
        await channel.send(f"Invalid role ID **{role_id}**")

def check_team(message, user_id):
    user = message.guild.get_member(user_id)
    print(get_roles(user))
    print(team(user, message.channel))
    print(team_color(user, message.channel))
    print(other_team(team(user, message.channel), message.channel))


async def take_attendance(message):
    file = open(f"./attendance/attendance {time.asctime()}.txt", "w")
    for user in client.get_channel(state[message.channel]['VC']).members:
        file.write(user.display_name + '\n')
    file.close()

async def json_stuff(message, file):
    print(file)
    if file == "practice_channels.py":
        from practice_channels import channels
        print(channels)
        for channel_id in channels.keys():
            await init_channel(client.get_channel(channel_id), channels[channel_id]["VC"])
            await set_team_1(client.get_channel(channel_id), channels[channel_id]["Team 1"])
            await set_team_2(client.get_channel(channel_id), channels[channel_id]["Team 2"])
            await begin(client.get_channel(channel_id))
    if file == "scrimmage1.py":
        from scrimmage1 import channels
        print(channels)
        for channel_id in channels.keys():
            await init_channel(client.get_channel(channel_id), channels[channel_id]["VC"])
            await set_team_1(client.get_channel(channel_id), channels[channel_id]["Team 1"])
            await set_team_2(client.get_channel(channel_id), channels[channel_id]["Team 2"])
            await begin(client.get_channel(channel_id))
    if file == "scrimmage2.py":
        from scrimmage2 import channels
        print(channels)
        for channel_id in channels.keys():
            await init_channel(client.get_channel(channel_id), channels[channel_id]["VC"])
            await set_team_1(client.get_channel(channel_id), channels[channel_id][1]["Team 1"])
            await set_team_2(client.get_channel(channel_id), channels[channel_id][1]["Team 2"])
            await begin(client.get_channel(channel_id))

async def set_round(channel_id, number):
    from scrimmage2 import channels
    await new_match(client.get_channel(channel_id))
    await set_team_1(client.get_channel(channel_id), channels[channel_id][number]["Team 1"])
    await set_team_2(client.get_channel(channel_id), channels[channel_id][number]["Team 2"])

async def global_round(number):
    from scrimmage2 import channels
    for channel_id in channels.keys():
        await new_match(client.get_channel(channel_id))
        await set_team_1(client.get_channel(channel_id), channels[channel_id][number]["Team 1"])
        await set_team_2(client.get_channel(channel_id), channels[channel_id][number]["Team 2"])


@client.event
async def on_ready():
    print('Logged on as {0}!'.format(client.user))
    
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.lower().startswith("init channel"):
        await init_channel(message.channel, int(message.content.split()[2]))
    if message.content.lower().startswith("import json"):
        print("men")
        await json_stuff(message, message.content.split(" ")[2])

    if message.channel in state.keys():
        if state[message.channel]["ready"]:
            if message.content.lower() in ["buzz", "b"]:
                await buzz(message)
        if is_admin(message.author):
            if message.content.lower() in ["reset", "r"]:
                await reset(message.channel, unmute_people=True)
            if message.content.lower() in ["begin"]:
                await begin(message.channel)
            if message.content.lower() in ["next"]:
                await next_tossup(message)
            if message.content.lower() in ["new game", "new match"]:
                await new_match(message.channel)
            if message.content.lower() in ["y", "yes", "correct", "n", "no", "incorrect", "i"]:
                await tu_response(message)
            if message.content.lower().startswith("set tossup"):
                await set_tossup(message)
            if message.content.lower().startswith("set team 1"):
                await set_team_1(message.channel, int(message.content.split()[3]))
            if message.content.lower().startswith("set team 2"):
                await set_team_2(message.channel, int(message.content.split()[3]))
            if message.content.lower().startswith("set round"):
                await set_round(message.channel.id, int(message.content.split()[2]))
            if message.content.lower().startswith("global round"): 
                await global_round(int(message.content.split()[2]))
            if message.content.lower().startswith("check team"):
                check_team(message, int(message.content.split()[2]))
            if message.content.lower() in ["take attendance"]:
                await take_attendance(message)
            if message.content.lower() in ["shut down", "shutdown"]:
                await message.channel.send("Au revoir!")
                await client.close()

client.run('Bot token here')