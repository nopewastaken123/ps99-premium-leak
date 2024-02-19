import datetime
import string
import discord
from discord import app_commands
from discord.ext import commands
import json
import random
import time
import asyncio
import threading
import os
from enum import Enum
from discord import Button, ButtonStyle
import requests
import math
from quart import Quart, request, jsonify

app = Quart(__name__)

Config = {
    "Bot Name": "PS Bot", # will be in all embeds
    "Bot Icon": "https://static-00.iconduck.com/assets.00/gem-stone-emoji-512x509-jsec888c.png", # will be in all embeds
    "Towers" : { # Config for towers
        "WinChance" : 63,  # Percent they will win when they click a tower
        "Multis" : [1.42, 2.02, 2.86, 4.05, 5.69]  # Multipliers On The Blocks
    },
    "Mines" : { # Config for mines
        "House" : 0.1,  # The Multiplier Will Be Multiplied by 1.00 - This
    },
    "Logs": 1192746289734094979, # log channel
    "Coinflip" : { # Config for coinflip
        "1v1" : "1208487459797602365",  # Channel That Coinflips Be In
        "House": 3.5 # House Edge (%)
    },
    "Rains" : {
        "Channel" : "1208487471764078704"
    },
    "Deposit" : {
        "Webhook" : "https://discord.com/api/webhooks/1208529473423540255/v2MKFtAvDrsXAevbGPyhZ_B7URAmnv3-5PCkSAiwt28vtRccn9mPNPMWeKwzaYkmjjrL"
    },
    "Withdraw" : {
        "Webhook" : "https://discord.com/api/webhooks/1208529962508750859/hFTNc1w0FDEUFgvPuivsezYbKyI-GL8bDIlRvIvX_NdxKIOstKaW22Jnq4KIgFdchdNH"
    },
    "Tips" : {
        "Webhook" : ""
    },
    "Affiliate" : {
        "Webhook" : "https://discord.com/api/webhooks/1208530105832448022/A5nvDbxGmGASry3Qd5NjDkWAF_QjgFAMorM8N_UVtSSreOrgNTLfxeTybnEmETCa4srw"
    },
    "Upgrader": {
        "House": 0.95 # house edge (winnings*house)
    },
    "Rakeback" : 1, # Rakeback %
    "Username": "PS Casino", # The Username Of The Account Running The Bot
    "DiscordBotToken": "MTIwMzI3MjczNDc3MjMwMTg2NQ.Gix2pY.v_n29BHvzBB0c6a5b5bQeIP9-U2ESYVmClTm4k" # The token of the discord bot
}

with open("cfgtemp.json", "w") as f:
    f.write(json.dumps(Config))

username = Config['Username']

def multiplier_to_percentage(multiplier, house):
    percentage2 = (100 / multiplier) * house
    return percentage2
def percentage(percent, whole) :
    return (percent * whole) / 100.0

rb = Config['Rakeback']

TowersMultis = [1.0, 1.5, 2, 2.5, 3.0, 3.5]

MineHouseEdge = Config['Mines']['House']


def roll_percentage(percent) :
    random_num = random.uniform(0, 100)
    if random_num <= percent :
        return True
    else :
        return False


def calculate_mines_multiplier(minesamount, diamonds, houseedge) :
    def nCr(n, r) :
        f = math.factorial
        return f(n) // f(r) // f(n - r)

    house_edge = houseedge
    return (1 - house_edge) * nCr(25, diamonds) / nCr(25 - minesamount, diamonds)
def succeed(message):
    return discord.Embed(description=f":white_check_mark: {message}", color = 0x7cff6b)
def infoe(message):
    return discord.Embed(description=f":information_source: {message}", color = 0x57beff)
def fail(message):
    return discord.Embed(description=f":x: {message}", color = 0xff6b6b)
def generate_board(minesa) :
    board = [
        ["s", "s", "s", "s", "s"],
        ["s", "s", "s", "s", "s"],
        ["s", "s", "s", "s", "s"],
        ["s", "s", "s", "s", "s"],
        ["s", "s", "s", "s", "s"],
    ]
    for index in range(0, minesa) :
        end = False
        while not end :
            row = random.randint(0, 4)
            collum = random.randint(0, 4)
            if board[row][collum] == "s" :
                board[row][collum] = "m"
                end = True
    return board


class CoinSide(Enum) :
    Heads = "Heads"
    Tails = "Tails"
class Colors(Enum):
    Purple = "Purple (2x)"
    Blue = "Blue (2x)"
    Gold = "Gold (5x)"

class RPSSide(Enum) :
    Rock = "Rock"
    Paper = "Paper"
    Scissors = "Scissors"
rpsgames = []
words = ['apple', 'banana', 'fruit', 'up', 'is', 'w', 'a', 'fr', 'shift', 'left', 'down', 'code']
rains = []

def suffix_to_int(s) :
    suffixes = {
        'k' : 3,
        'm' : 6,
        'b' : 9,
        't' : 12
    }

    suffix = s[-1].lower()
    if suffix in suffixes :
        num = float(s[:-1]) * 10 ** suffixes[suffix]
    else :
        num = float(s)

    return int(num)

def readdata():
    with open("data.json", "r") as infile:
        return json.load(infile)

def writedata(data):
    with open("data.json", "w") as outfile:
        json.dump(data, outfile, indent=4)

def get_cases():
    data = readdata()
    return data['cases']

def add_bet(userid, bet, winnings):
    db = readdata()
    db['users'][userid]['Wagered'] += bet
    profit = winnings-bet
    db['users'][userid]['Net Profit'] += profit
    writedata(db)

caseslist = [case['Name'] for case in get_cases()]

def get_affiliate(uid):
    data = readdata()
    return data['users'][uid].get("Affiliate", None)

def set_affiliate(uid, uid2):
    data = readdata()
    data['users'][uid]["Affiliate"] = uid2
    writedata(data)
def is_registered(uid):
    data = readdata()
    return uid in data['users']

def register_user(uid):
    if not is_registered(uid):
        data = readdata()
        data["users"][uid] = {
            "Gems": 0,
            "CrashJoinAmount": 100000000,
            "Rakeback": 0,
            "Affiliate": None,
            "Affiliate Earnings": 0,
            "Deposited": 0,
            "Withdrawn": 0,
            "Wagered": 0,
            "Tips Got": 0,
            "Tips Sent": 0,
            "Net Profit": 0
        }
        writedata(data)

def add_code(item):
    with open("deposits.json", "r") as f:
        codes2 = json.loads(f.read())
    codes2.append(item)
    with open("deposits.json", "w") as f:
        f.write(json.dumps(codes2))

def remove_code(item):
    with open("deposits.json", "r") as f:
        codes2 = json.loads(f.read())
    codes2.remove(item)
    with open("deposits.json", "w") as f:
        f.write(json.dumps(codes2))

def get_codes():
    with open("deposits.json", "r") as f:
        codes2 = json.loads(f.read())
    return codes2

def get_gems(uid):
    try:
        data = readdata()
        return data['users'][uid]['Gems']
    except:
        pass

def set_gems(uid, gems):
    try :
        data = readdata()
        data['users'][uid]['Gems'] = gems
        writedata(data)
    except:
        pass

def get_rake_back(uid):
    data = readdata()
    return data['users'][uid].get("Rakeback", 0)

def set_rake_back(uid, amount):
    data = readdata()
    data['users'][uid]['Rakeback'] = amount
    writedata(data)

def add_rake_back(uid, amount):
    rake_back = get_rake_back(uid)
    set_rake_back(uid, rake_back + amount)

def add_gems(uid, gems):
    try:
        current_gems = get_gems(uid)
        set_gems(uid, current_gems + gems)
    except:
        pass

def subtract_gems(uid, gems):
    try :
        current_gems = get_gems(uid)
        set_gems(uid, current_gems - gems)
    except:
        pass

def set_crash_join(uid, amount):
    data = readdata()
    data['users'][uid]['CrashJoinAmount'] = amount
    writedata(data)

def get_crash_join_amount(uid):
    data = readdata()
    return data['users'][uid]['CrashJoinAmount']

def add_suffix(inte):
    gems = inte
    abs_gems = abs(gems)  # Use absolute value for formatting

    if abs_gems >= 1000000000000:  # if gems are greater than or equal to 1 trillion
        gems_formatted = f"{gems / 1000000000000:.1f}t"  # display gems in trillions with one decimal point
    elif abs_gems >= 1000000000:  # if gems are greater than or equal to 1 billion
        gems_formatted = f"{gems / 1000000000:.1f}b"  # display gems in billions with one decimal point
    elif abs_gems >= 1000000:  # if gems are greater than or equal to 1 million
        gems_formatted = f"{gems / 1000000:.1f}m"  # display gems in millions with one decimal point
    elif abs_gems >= 1000:  # if gems are greater than or equal to 1 thousand
        gems_formatted = f"{gems / 1000:.1f}k"  # display gems in thousands with one decimal point
    else:  # if gems are less than 1 thousand
        gems_formatted = str(gems)  # display gems as is

    return gems_formatted
class SystemRainButtons(discord.ui.View) :
    def __init__(self, message, entries, amount, ends, emoji) :
        super().__init__(timeout=None)
        self.message = message
        self.entries = entries
        self.amount = amount
        self.ends = ends
        self.emoji = emoji
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Join", custom_id=f"join", style=discord.ButtonStyle.green, emoji="✅")
        button.callback = self.button_join
        self.add_item(button)

    async def button_join(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        uid = str(interaction.user.id)
        found = False
        for person in self.entries:
            print(person)
            if person == uid:
                found = True
        print(found)
        if not found:
            self.entries.append(uid)
            embed = discord.Embed(title=f"{self.emoji} Rain In Progress",
                                  description=f"A Rain Has Been Started By ``System``",
                                  color=0x2ea4ff)
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="rains")
            embed.add_field(name="Details",
                            value=f":gem: **Amount:** ``{add_suffix(self.amount)}``\n:money_mouth: **Entries:** ``{len(self.entries)}``\n:gem: **Gems Per Person:** ``{add_suffix(self.amount / len(self.entries))}``\n:clock1: **Ends:** {self.ends}")
            await self.message.edit(embed=embed,
                               view=SystemRainButtons(amount=self.amount, entries=self.entries,
                                                ends=f"{self.ends}",
                                                message=self.message,emoji=self.emoji))
async def system_rain(amount, duration):
    channel = bot.get_channel(int(Config['Rains']['Channel']))
    rains.append([])
    rain = rains[-1]
    joined = 0
    if joined == 0 :
        joined = 1
    emoji = "🌤️"
    if amount <= 500000000 :
        emoji = "🌤️"
    elif amount <= 2000000000 :
        emoji = "⛅"
    elif amount <= 5000000000 :
        emoji = "🌥️"
    elif amount <= 10000000000 :
        emoji = "🌦️"
    elif amount <= 20000000000 :
        emoji = "🌧️"
    else :
        emoji = "⛈"
    embed = discord.Embed(title=f"{emoji} Rain In Progress",
                          description=f"A Rain Has Been Started By ``System``",
                          color=0x2ea4ff)
    embed.set_author(name=Config['Bot Name'],
                     icon_url=Config['Bot Icon'])
    embed.set_footer(text="rains")
    embed.add_field(name="Details",
                    value=f":gem: **Amount:** ``{add_suffix(amount)}``\n:money_mouth: **Entries:** ``{0}``\n:gem: **Gems Per Person:** ``{add_suffix(amount / joined)}``\n:clock1: **Ends:** <t:{round(time.time() + duration)}:R>")
    message = await channel.send(content=".")
    await message.edit(embed=embed,
                       view=SystemRainButtons(amount=amount, entries=rain, ends=f"<t:{round(time.time() + duration)}:R>",
                                        message=message, emoji=emoji))
    await asyncio.sleep(duration)
    if len(rain) == 0 :
        gpp = amount
    else :
        gpp = amount / len(rain)
    for person in rain :
        add_gems(person, gpp)
    embed = discord.Embed(title=":sunny: Rain Ended",
                          description=f"A Rain Has Been Started By ``System`` (ended)",
                          color=0xffe74d)
    embed.set_author(name=Config['Bot Name'],
                     icon_url=Config['Bot Icon'])
    embed.set_footer(text="rains")
    embed.add_field(name="Details",
                    value=f":gem: **Amount:** ``{add_suffix(amount)}``\n:money_mouth: **Entries:** ``{len(rain)}``\n:gem: **Gems Per Person:** ``{add_suffix(gpp)}``\n:clock1: **Ended:** <t:{round(time.time())}:R>")
    await message.edit(embed=embed, view=None)

crash_info = {}
bot = commands.Bot(command_prefix="?", intents=discord.Intents.all())
async def log(text):
    channel = await bot.fetch_channel(Config['Logs'])
    await channel.send(embed=infoe(text))

async def fancy_log(title, description, reason):
    with open("cfgtemp.json", "r") as f :
        Config = json.loads(f.read())
    embed = {
        "content": "",
        "embeds" : [
            {
                "title" : title,
                "description" : description,
                "footer" : {
                    "text" : "Notification"
                },
                "author" : {
                    "name" : Config["Bot Name"],
                    "icon_url" : Config["Bot Icon"]
                },
                "color": 35051
            }
        ]
    }
    requests.post(Config[reason]['Webhook'], json=embed)

@app.route("/deposit_request", methods=['POST'])
async def deposit_request():
    data = await request.data
    data = json.loads(data)
    gems = data['gems']
    message = data['message']
    print(f"Deposit! Gems: {gems} Code: {message}")
    codes = get_codes()
    print(codes)
    for item in codes:
        if item[1] == message:
            add_gems(str(item[0]), int(gems))
            await fancy_log("Deposit Completed", f"Someone has deposited some gems\n\n:gem: **Amount:** `{add_suffix(int(gems))}`", "Deposit")
            database = readdata()
            database['users'][str(item[0])]['Deposited'] += int(gems)
            writedata(database)
            print("add")
            remove_code(item)

    return jsonify({"message": "success"}), 200

@app.route("/get_withdraws", methods=['GET'])
async def get_withdraws():
    with open("withdraws.json", "r") as f:
        oldwithdraws = json.loads(f.read())
    with open("withdraws.json", "w") as f :
        f.write("[]")
    return jsonify(oldwithdraws), 200

@bot.event
async def on_ready() :
    print("Bot Is Online And Listening For Commands.")
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")

class DepositButtons(discord.ui.View) :
    def __init__(self, message, username) :
        super().__init__(timeout=None)
        self.message = message
        self.username = username
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Copy Username", custom_id=f"1", style=discord.ButtonStyle.blurple, emoji="📋")
        button.callback = self.button_user
        self.add_item(button)
        button = discord.ui.Button(label="Copy Code", custom_id=f"2", style=discord.ButtonStyle.blurple, emoji="📋")
        button.callback = self.button_code
        self.add_item(button)
    async def button_user(self, interaction: discord.Interaction):
        await interaction.response.send_message(content=self.username,ephemeral=True)
    async def button_code(self, interaction: discord.Interaction):
        await interaction.response.send_message(content=self.message, ephemeral=True)
@bot.tree.command(name="deposit", description="Deposit Some Gems To Gamble")
async def deposit(interaction: discord.Interaction) :
    global codes
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    if is_registered(str(interaction.user.id)) :
        random_words = random.sample(words, 3)

        code = " ".join(random_words)

        add_code([str(interaction.user.id), code])
        print(get_codes())
        embed = discord.Embed(title=":gem: Deposit",
                              description=f"To deposit gems, you must mail the bot inside of Pet Simulator 99.",
                              color=0x0a0094)
        embed.add_field(name="Mailbox Details",
                        value=f":keyboard: Username: ``{username}``\n:speech_balloon: Message: ``{code}``\n:gem: Gems: ``Any``\n")
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        await interaction.response.send_message(embed=embed,view=DepositButtons(username=username,message=code))

    else :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="/deposit")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="info", description="View Your Gem Balance")
async def info(interaction: discord.Interaction, user: discord.Member = None) :
    if user != None:
        interaction.user = user
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    if is_registered(str(interaction.user.id)) :
        gems = get_gems(str(interaction.user.id))
        if gems >= 1000000000000 :  # if gems are greater than or equal to 1 trillion
            gems_formatted = f"{gems / 1000000000000:.1f}t"  # display gems in trillions with one decimal point
        elif gems >= 1000000000 :  # if gems are greater than or equal to 1 billion
            gems_formatted = f"{gems / 1000000000:.1f}b"  # display gems in billions with one decimal point
        elif gems >= 1000000 :  # if gems are greater than or equal to 1 million
            gems_formatted = f"{gems / 1000000:.1f}m"  # display gems in millions with one decimal point
        elif gems >= 1000 :  # if gems are greater than or equal to 1 thousand
            gems_formatted = f"{gems / 1000:.1f}k"  # display gems in thousands with one decimal point
        else :  # if gems are less than 1 thaousand
            gems_formatted = str(gems)  # display gems as is

        embed = discord.Embed(title=f":gem: Stats Of {interaction.user.name}",
                              description=f"",
                              color=0x0a0094)
        uid = str(interaction.user.id)
        data_base = readdata()
        embed.add_field(name=f"Gems",
                        value=f"\n\n:gem: Gems: `{gems_formatted}`\n:gem: Total Deposited: `{add_suffix(data_base['users'][uid]['Deposited'])}`\n:gem: Total Withdrawn: `{add_suffix(data_base['users'][uid]['Withdrawn'])}`\n:gem: Total Wagered: `{add_suffix(data_base['users'][uid]['Wagered'])}`\n:gem: Net Profit: `{add_suffix(data_base['users'][uid]['Net Profit'])}`\n")
        aff_count = 0
        for user in data_base['users']:
            userdata = data_base['users'][user]
            if userdata.get("Affiliate", None) == uid:
                aff_count += 1

        if not get_affiliate(str(interaction.user.id)) :
            embed.add_field(name=f"Affiliate Program",
                            value=f":rocket: Affiliated To: `None`\n:rocket: Affiliate Count: `{aff_count}`\n:rocket: Affiliate Earnings: `{add_suffix(data_base['users'][uid]['Affiliate Earnings'])}`\n", inline=False)
            embed.set_footer(text="Dont Forget To Affiliate Someone!")
        else :
            embed.add_field(name=f"Affiliate Program",
                            value=f":rocket: Affiliated To <@{get_affiliate(str(interaction.user.id))}>\n:rocket: Affiliate Count: `{aff_count}`\n:rocket: Affiliate Earnings: `{add_suffix(data_base['users'][uid]['Affiliate Earnings'])}`\n", inline=False)
            embed.set_footer(text="Keep gambling!")
        embed.add_field(name=f"Tips",
                        value=f":inbox_tray: Tips Received: `{add_suffix(data_base['users'][uid]['Tips Got'])}`\n:outbox_tray: Tips Sent: `{add_suffix(data_base['users'][uid]['Tips Sent'])}`")
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_thumbnail(url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
    else :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="/balance")
        await interaction.response.send_message(embed=embed)

class RakeButtons(discord.ui.View) :
    def __init__(self, i) :
        super().__init__(timeout=None)
        self.i = i
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Claim Rakeback", custom_id=f"1", style=discord.ButtonStyle.grey, emoji="💰")
        button.callback = self.button_claim
        self.add_item(button)
    async def button_claim(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        rake_back = get_rake_back(uid)
        set_rake_back(uid, 0)
        add_gems(uid, rake_back)
        embed = discord.Embed(title=f":moneybag: Rakeback",
                              description=f"Rakeback Claimed! :gem: `{add_suffix(rake_back)}` Was added to your account!",
                              color=0xffad1f)
        await self.i.edit_original_response(embed=embed, view=None)

@bot.tree.command(name="rakeback", description="View Your Rakeback")
async def rake(interaction: discord.Interaction) :
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    uid = str(interaction.user.id)
    if is_registered(str(interaction.user.id)) :
        rake_back = get_rake_back(uid)

        embed = discord.Embed(title=f":moneybag: Rakeback",
                              description=f"You Currently Have :gem: ``{add_suffix(rake_back)}`` Sitting In Rake Back.\nClick the button below to claim it.",
                              color=0xffad1f)
        await interaction.response.send_message(embed=embed, view=RakeButtons(i=interaction))
    else :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="rakeback")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="affiliate", description="affiliate someone")
async def affiliate(interaction: discord.Interaction, user: discord.Member) :
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    if not is_registered(str(user.id)) :
        register_user(str(user.id))
    uid = str(interaction.user.id)
    cf = get_affiliate(uid)
    if cf :
        if interaction.user.id != 1 :
            embed = discord.Embed(title=":x: Error",
                                  description="You Are Already Affiliated To Someone!",
                                  color=0xff0000)
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="/affiliate")
            await interaction.response.send_message(embed=embed)
            return
    if not is_registered(uid) :
        embed = discord.Embed(title=":x: Error",
                              description="You Arent Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="/affiliate")
        await interaction.response.send_message(embed=embed)
        return
    if user.id == interaction.user.id :
        embed = discord.Embed(title=":x: Error",
                              description="You Cant Affiliate Yourself Bozo!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="/affiliate")
        await interaction.response.send_message(embed=embed)
        return
    set_affiliate(uid, str(user.id))
    await fancy_log("Affiliate Code Redeemed",f"{interaction.user.mention} Has Redeemed **{user.mention}'s** Affiliate Code", "Affiliate")
    await log(f"<@{uid}> Affiliated <@{user.id}>")
    add_gems(uid, 5000)
    embed = discord.Embed(title="Affiliate Code Redeemed",
                          description=f":white_check_mark: You Are Now Affiliated To <@{user.id}>",
                          color=0x98ff61)
    embed.set_author(name=Config['Bot Name'], icon_url=Config['Bot Icon'])
    embed.set_footer(text="they will receive 1% of all your bets")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="set_crash_join_amount", description="Sets Your Bet For When You Join A Crash Game")
async def crashamount(interaction: discord.Interaction, bet: str) :
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    bet = suffix_to_int(bet)
    uid = str(interaction.user.id)
    if is_registered(uid) :
        embed = discord.Embed(title=":gem: Set Crash Join Amount",
                              description=f"Your crash join amount has been set to ``{add_suffix(bet)}``, This will now be your bet when you join a game of crash",
                              color=0x0a0094)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="make sure to cash it out at the right time!")
        await interaction.response.send_message(embed=embed)
        set_crash_join(uid, bet)
    else :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="/crash")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="withdraw", description="Withdraw Gems")
@app_commands.describe(amount="The Amount Of Gems To Withdraw")
@app_commands.describe(uname="The Username To Send The Gems To")
async def withdraw(interaction: discord.Interaction, amount: str, uname: str) :
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    amount = suffix_to_int(amount)
    global withdraws
    if is_registered(str(interaction.user.id)) :
        if get_gems(str(interaction.user.id)) >= amount :
            if amount >= 19999 :
                subtract_gems(str(interaction.user.id), amount)
                gems = amount
                if gems >= 1000000000000 :  # if gems are greater than or equal to 1 trillion
                    gems_formatted = f"{gems / 1000000000000:.1f}t"  # display gems in trillions with one decimal point
                elif gems >= 1000000000 :  # if gems are greater than or equal to 1 billion
                    gems_formatted = f"{gems / 1000000000:.1f}b"  # display gems in billions with one decimal point
                elif gems >= 1000000 :  # if gems are greater than or equal to 1 million
                    gems_formatted = f"{gems / 1000000:.1f}m"  # display gems in millions with one decimal point
                elif gems >= 1000 :  # if gems are greater than or equal to 1 thousand
                    gems_formatted = f"{gems / 1000:.1f}k"  # display gems in thousands with one decimal point
                else :  # if gems are less than 1 thousand
                    gems_formatted = str(gems)  # display gems as is
                with open("withdraws.json", "r") as f :
                    oldwithdraws = json.loads(f.read())
                oldwithdraws.append({"user": uname, "amount": gems})
                with open("withdraws.json", "w") as f :
                    f.write(json.dumps(oldwithdraws))
                uid = str(interaction.user.id)
                database = readdata()
                database['users'][uid]['Withdrawn'] += gems
                writedata(database)
                embed = discord.Embed(title=":gem: Withdraw",
                                      description=f"You have withdrawn `{gems_formatted}` gems. They have been taken from your account automatically and sent to your mailbox in PS99",
                                      color=0x0a0094)
                embed.set_author(name=Config['Bot Name'],
                                 icon_url=Config['Bot Icon'])
                embed.set_footer(text="buy something nice!")
                await fancy_log("Withdraw Completed", f"Someone has withdrawn gems!\n\n:gem: **Amount:** `{add_suffix(amount)}`", "Withdraw")
                await interaction.response.send_message(embed=embed)
            else :
                embed = discord.Embed(title=":x: Error",
                                      description="You Can Only Withdraw Over 20k",
                                      color=0xff0000)
                embed.set_author(name=Config['Bot Name'],
                                 icon_url=Config['Bot Icon'])
                embed.set_footer(text="/withdraw")
                await interaction.response.send_message(embed=embed)
        else :
            embed = discord.Embed(title=":x: Error",
                                  description="You Are Too Poor For This Withdraw xD!",
                                  color=0xff0000)
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="/withdraw")
            await interaction.response.send_message(embed=embed)
    else :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="/withdraw")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="tip", description="Send Someone Gems")
@app_commands.describe(user="The User To Send To")
@app_commands.describe(amount="Amount To Send")
async def tip(interaction: discord.Interaction, amount: str, user: discord.Member) :
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    if not is_registered(str(user.id)) :
        register_user(str(user.id))
    amount = suffix_to_int(amount)
    if is_registered(str(interaction.user.id)) :
        if is_registered(str(user.id)) :
            if get_gems(str(interaction.user.id)) >= amount and amount >= 1 :
                subtract_gems(str(interaction.user.id), amount)
                time.sleep(0.5)
                add_gems(str(user.id), amount)
                database = readdata()
                database['users'][str(interaction.user.id)]['Tips Sent'] += amount
                database['users'][str(user.id)]['Tips Got'] += amount
                writedata(database)
                await fancy_log("Tip Sent", f"{interaction.user.mention} Has Tipped :gem: **{add_suffix(amount)}** To {user.mention}", "Tips")
                await log(f"<@{interaction.user.id}> Tipped {add_suffix(amount)} To <@{user.id}>")
                gems = amount
                if gems >= 1000000000000 :  # if gems are greater than or equal to 1 trillion
                    gems_formatted = f"{gems / 1000000000000:.1f}t"  # display gems in trillions with one decimal point
                elif gems >= 1000000000 :  # if gems are greater than or equal to 1 billion
                    gems_formatted = f"{gems / 1000000000:.1f}b"  # display gems in billions with one decimal point
                elif gems >= 1000000 :  # if gems are greater than or equal to 1 million
                    gems_formatted = f"{gems / 1000000:.1f}m"  # display gems in millions with one decimal point
                elif gems >= 1000 :  # if gems are greater than or equal to 1 thousand
                    gems_formatted = f"{gems / 1000:.1f}k"  # display gems in thousands with one decimal point
                else :  # if gems are less than 1 thousand
                    gems_formatted = str(gems)  # display gems as is
                embed = discord.Embed(title=":gem: Sent Gems",
                                      description=f"You have sent some gems over to <@{user.id}>'s account.",
                                      color=0x0a0094)
                embed.set_author(name=Config['Bot Name'],
                                 icon_url=Config['Bot Icon'])
                embed.set_footer(text="thanks for being nice! your tips sent stat has gone up.")
                embed.add_field(name=":mailbox: Tip",
                                value=f":outbox_tray: Sender: <@{interaction.user.id}>\n:inbox_tray: Receiver: <@{user.id}>\n:gem: Amount: ``{gems_formatted}``")
                await interaction.response.send_message(embed=embed)
            else :
                embed = discord.Embed(title=":x: Error",
                                      description="You Are Too Poor For This Tip!",
                                      color=0xff0000)
                embed.set_author(name=Config['Bot Name'],
                                 icon_url=Config['Bot Icon'])
                embed.set_footer(text="/tip")
                await interaction.response.send_message(embed=embed)
        else :
            embed = discord.Embed(title=":x: Error",
                                  description="The User You Are Trying To Send Gems To Isn't Registered!",
                                  color=0xff0000)
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="/tip")
            await interaction.response.send_message(embed=embed)
    else :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="/tip")
        await interaction.response.send_message(embed=embed)


class RainButtons(discord.ui.View) :
    def __init__(self, message, entries, amount, ends, starter, emoji) :
        super().__init__(timeout=None)
        self.message = message
        self.entries = entries
        self.amount = amount
        self.ends = ends
        self.starter = starter
        self.emoji = emoji
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Join", custom_id=f"join", style=discord.ButtonStyle.blurple, emoji="💎")
        button.callback = self.button_join
        self.add_item(button)

    async def button_join(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        uid = str(interaction.user.id)
        if not is_registered(str(interaction.user.id)) :
            register_user(str(interaction.user.id))
        found = False
        for person in self.entries:
            print(person)
            if person == uid:
                found = True
        print(found)
        if not found:
            self.entries.append(uid)
            embed = discord.Embed(title=f"{self.emoji} Rain In Progress",
                                  description=f"A Rain Has Been Started By <@{self.starter}>",
                                  color=0x0a0094)
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="rains")
            embed.add_field(name="Details",
                            value=f":gem: **Amount:** ``{add_suffix(self.amount)}``\n:money_mouth: **Entries:** ``{len(self.entries)}``\n:gem: **Gems Per Person:** ``{add_suffix(self.amount / len(self.entries))}``\n:clock1: **Ends:** {self.ends}")
            await self.message.edit(embed=embed,
                               view=RainButtons(amount=self.amount, entries=self.entries,
                                                ends=f"{self.ends}",
                                                message=self.message, starter=self.starter,emoji=self.emoji))


@bot.tree.command(name="create-rain", description="start a rain")
async def createrain(interaction: discord.Interaction, amount: str, duration: int) :
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    amount = suffix_to_int(amount)
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="rains")
        await interaction.response.send_message(embed=embed)
        return
    if amount < 5000 :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Minimum Rain Amount Is 5k",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="rains")
        await interaction.response.send_message(embed=embed)
        return
    if amount > get_gems(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Too Poor XD",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="rains")
        await interaction.response.send_message(embed=embed)
        return
    channel = bot.get_channel(int(Config['Rains']['Channel']))
    rains.append([])
    rain = rains[-1]
    joined = 0
    if joined == 0 :
        joined = 1
    subtract_gems(uid, amount)
    emoji = "🌧️"
    embed = discord.Embed(title=f"{emoji} Rain In Progress",
                          description=f"A Rain Has Been Started By <@{interaction.user.id}>",
                          color=0x0a0094)
    embed.set_author(name=Config['Bot Name'],
                     icon_url=Config['Bot Icon'])
    embed.set_footer(text="rains")
    embed.add_field(name="Details",
                    value=f":gem: **Amount:** ``{add_suffix(amount)}``\n:money_mouth: **Entries:** ``{0}``\n:gem: **Gems Per Person:** ``{add_suffix(amount / joined)}``\n:clock1: **Ends:** <t:{round(time.time() + duration)}:R>")
    message = await channel.send(content=".")
    await message.edit(embed=embed,
                       view=RainButtons(amount=amount, entries=rain, ends=f"<t:{round(time.time() + duration)}:R>",
                                        message=message, starter=uid,emoji=emoji))
    embed2 = discord.Embed(title="Rain Created", description="You have rained some gems! The rain will appear in the rain channel", color=0x0a0094)
    embed2.set_author(name=Config['Bot Name'],
                     icon_url=Config['Bot Icon'])
    embed2.set_footer(text="Thanks for being kind!")
    await interaction.response.send_message(embed=embed2)
    await asyncio.sleep(duration)
    if len(rain) == 0:
        gpp = amount
    else:
        gpp = amount / len(rain)
    for person in rain:
        add_gems(person, gpp)
    embed = discord.Embed(title=":sunny: Rain Ended",
                          description=f"This rain has ended. Congrats to all the participants!",
                          color=0xffe74d)
    embed.set_author(name=Config['Bot Name'],
                     icon_url=Config['Bot Icon'])
    embed.set_footer(text="Enjoy your gems!")
    await message.edit(embed=embed, view=None)



class MinesButtons(discord.ui.View) :
    def __init__(self, board, bombs, bet, userboard, usersafes, interaction, exploded) :
        super().__init__(timeout=None)
        self.board = board
        self.bombs = bombs
        self.usersafes = usersafes
        self.bet = bet
        self.userboard = userboard
        self.interaction = interaction
        self.exploded = exploded
        self.setup_buttons()
        self.buttons = {}

    def setup_buttons(self) :
        if not self.exploded :
            for row in range(0, 5) :
                for column in range(0, 5) :
                    square = self.userboard[row][column]
                    if square == "" :
                        button = discord.ui.Button(label=".", custom_id=f"{row} {column}",
                                                   style=discord.ButtonStyle.gray)
                        button.callback = self.button_callback
                        self.add_item(button)
                    if square == "s" :
                        button = discord.ui.Button(label=".", custom_id=f"{row} {column}",
                                                   style=discord.ButtonStyle.green, emoji="✅")
                        button.callback = self.button_cashout
                        self.add_item(button)
        else :
            for row in range(0, 5) :
                for column in range(0, 5) :
                    square = self.board[row][column]
                    if square == "" :
                        button = discord.ui.Button(label=".", custom_id=f"{row} {column}",
                                                   style=discord.ButtonStyle.gray)
                        button.callback = self.button_callback
                        button.disabled = True
                        self.add_item(button)
                    if square == "s" :
                        button = discord.ui.Button(label="", custom_id=f"{row} {column}",
                                                   style=discord.ButtonStyle.green, emoji="✅")
                        button.callback = self.button_cashout
                        button.disabled = True
                        self.add_item(button)
                    if square == "m" :
                        button = discord.ui.Button(label="", custom_id=f"{row} {column}", style=discord.ButtonStyle.red,
                                                   emoji="💀")
                        button.callback = self.button_cashout
                        button.disabled = True
                        self.add_item(button)

    async def button_cashout(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            await interaction.response.defer()
            multi = round(calculate_mines_multiplier(self.bombs, self.usersafes, MineHouseEdge), 2)
            add_gems(str(interaction.user.id), round(self.bet * multi))
            add_bet(str(interaction.user.id), self.bet, round(self.bet * multi))
            embed = discord.Embed(color=0x57ff5a, title=f":bomb: {self.bombs} Mines Cashed Out",
                                  description="Nice one! Congrats on your win!")
            embed.set_footer(text="Dont get blown up!")
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.add_field(name="Game Stats",
                            value=f":gem: Bet: `{add_suffix(self.bet)}`\n:gem: Winnings: `{add_suffix(round(self.bet * multi))}`\n:star: Multiplier: ``{round(multi, 2)}x``\n")
            await self.interaction.edit_original_response(
                embed=embed,
                view=MinesButtons(bet=self.bet, board=self.board, bombs=self.bombs, interaction=self.interaction,
                                  usersafes=self.usersafes, userboard=self.userboard, exploded=True))

    async def button_callback(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            custom_id = interaction.data["custom_id"]
            row = int(custom_id.split(" ")[0])
            collum = int(custom_id.split(" ")[1])
            if self.board[row][collum] == "s" :
                safe = True
                self.userboard[row][collum] = "s"
                self.usersafes = self.usersafes + 1
                multi = round(calculate_mines_multiplier(self.bombs, self.usersafes, MineHouseEdge), 2)
                embed = discord.Embed(color=0x208cdf, title=f":bomb: {self.bombs} Mines",
                                      description="You have started a game of mines. click tiles to build up your multiplier, if its clear your multiplier will go up. if its a bomb you lose your bet. click an already uncovered tile to cashout.")
                embed.set_footer(text="Dont get blown up!")
                embed.set_author(name=Config['Bot Name'],
                                 icon_url=Config['Bot Icon'])
                embed.add_field(name="Game Stats",
                                value=f":gem: Bet: `{add_suffix(self.bet)}`\n:gem: Winnings: `{add_suffix(round(self.bet*multi))}`\n:star: Multiplier: ``{round(multi, 2)}x``\n")
                await self.interaction.edit_original_response(
                    embed=embed,
                    view=MinesButtons(bet=self.bet, board=self.board, bombs=self.bombs, interaction=self.interaction,
                                      usersafes=self.usersafes, userboard=self.userboard, exploded=False))
            if self.board[row][collum] == "m" :
                add_rake_back(str(self.interaction.user.id), percentage(rb, self.bet))
                add_bet(str(self.interaction.user.id), self.bet, 0)
                embed = discord.Embed(color=0xf53232, title=f":bomb: {self.bombs} Mines Exploded!",
                                      description="You lost, unlucky. Make sure to claim your rakeback to get a part of this loss back!")
                embed.set_footer(text="Dont get blown up!")
                embed.set_author(name=Config['Bot Name'],
                                 icon_url=Config['Bot Icon'])
                multi = round(calculate_mines_multiplier(self.bombs, self.usersafes, MineHouseEdge), 2)
                embed.add_field(name="Game Stats",
                                value=f":gem: Bet: `{add_suffix(self.bet)}`\n:gem: Winnings Lost: `{add_suffix(round(self.bet*multi))}`\n:star: Multiplier Lost: ``{round(multi, 2)}x``\n")
                await self.interaction.edit_original_response(
                    embed=embed,
                    view=MinesButtons(bet=self.bet, board=self.board, bombs=self.bombs, interaction=self.interaction,
                                      usersafes=self.usersafes, userboard=self.userboard, exploded=True))
            await interaction.response.defer()


@bot.tree.command(name="mines", description="Start A Game Of Mines")
async def mines(interaction: discord.Interaction, mines_amount: int, bet: str) :
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    valid = True
    uid = str(interaction.user.id)
    bet = suffix_to_int(bet)
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet <= 999 :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Minimum Bet Is 1k",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet > get_gems(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Too Poor XD",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if mines_amount >= 25 or mines_amount <= 0 :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Invalid Number Of Mines",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if valid :
        subtract_gems(uid, bet)
        af = get_affiliate(str(interaction.user.id))
        add_gems(af, bet * 0.01)
        db = readdata()
        try:
            db['users'][af]['Affiliate Earnings'] += bet*0.01
        except:
            pass
        writedata(db)
        board = generate_board(mines_amount)
        userboard = [
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
        ]
        coollooking = '\n'.join([' '.join(sublist) for sublist in board])
        await log(f"{interaction.user.name} Started A Mines Game! Board:\n\n{coollooking}")
        embed = discord.Embed(color=0x208cdf, title=f":bomb: {mines_amount} Mines", description="You have started a game of mines. click tiles to build up your multiplier, if its clear your multiplier will go up. if its a bomb you lose your bet. click an already uncovered tile to cashout.")
        embed.set_footer(text="Dont get blown up!")
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.add_field(name="Game Stats", value=f":gem: Bet: `{add_suffix(bet)}`\n:gem: Winnings: `{add_suffix(bet)}`\n:star: Multiplier: ``1.00x``\n")
        await interaction.response.send_message(
            embed=embed,
            view=MinesButtons(bet=bet, board=board, bombs=mines_amount, interaction=interaction, usersafes=0,
                              userboard=userboard, exploded=False))

def generate_scratch_multiplier():
    multipliers = [0, 1.5, 2, 3, 5]
    probabilities = [0.40, 0.20, 0.10, 0.05, 0.025]

    selected_multiplier = random.choices(multipliers, weights=probabilities, k=10)[0]

    return selected_multiplier

class ScratchButtons(discord.ui.View) :
    def __init__(self, interaction, price, multi, board, revealed2):
        super().__init__(timeout=None)
        self.interaction=interaction
        self.price=price
        self.multi=multi
        self.board=board
        self.finished=False
        self.revealed = revealed2
        self.true_count = 0
        for i in self.revealed:
            for i2 in i:
                if i2:
                    self.true_count += 1
        if self.true_count == 9:
            self.finished = True
        self.setup_buttons()
    def setup_buttons(self):
        if not self.finished:
            for row in range(0, 3):
                for column in range(0, 3):
                    square = self.board[row][column]
                    revealed = self.revealed[row][column]
                    if not revealed:
                        button = discord.ui.Button(label=".", custom_id=f"{row} {column}",
                                                       style=discord.ButtonStyle.gray, row=row)
                        button.callback = self.button_callback
                        self.add_item(button)
                    if revealed:
                        button = discord.ui.Button(label=str(square) + "x", custom_id=f"{row} {column}",
                                                       style=discord.ButtonStyle.blurple, row=row)
                        button.callback = self.button_callback
                        button.disabled = True
                        self.add_item(button)
        else:
            for row in range(0, 3):
                for column in range(0, 3):
                    square = self.board[row][column]
                    revealed = self.revealed[row][column]
                    if square == self.multi:
                        button = discord.ui.Button(label=str(square) + "x", custom_id=f"{row} {column}",
                                                       style=discord.ButtonStyle.green, row=row)
                        self.add_item(button)
                    else:
                        button = discord.ui.Button(label=str(square) + "x", custom_id=f"{row} {column}",
                                                       style=discord.ButtonStyle.red, row=row)
                        button.disabled = True
                        self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            custom_id = interaction.data["custom_id"]
            row = int(custom_id.split(" ")[0])
            collum = int(custom_id.split(" ")[1])
            self.revealed[row][collum] = True
            self.true_count = 0
            for i in self.revealed :
                for i2 in i :
                    if i2 :
                        self.true_count += 1
            if self.true_count != 9 :
                embed = discord.Embed(color=0x208cdf, title=f"Scratch Card", description="Scratch off your numbers!")
                embed.set_footer(text="")
                embed.set_author(name=Config['Bot Name'],
                                 icon_url=Config['Bot Icon'])
                embed.add_field(name="Game Stats",
                                value=f":gem: Card Price: `{add_suffix(self.price)}`\n:gem: Winnings: `0`")
                await self.interaction.edit_original_response(embed=embed, view=ScratchButtons(self.interaction, self.price, self.multi, self.board, self.revealed))
            else:
                if self.multi == 0:
                    embed = discord.Embed(color=0xff8080, title=f"Scratch Card | You Lost!", description="Better luck next time (you need 3 of the same number to win)")
                    embed.set_footer(text="")
                    embed.set_author(name=Config['Bot Name'],
                                     icon_url=Config['Bot Icon'])
                    embed.add_field(name="Game Stats",
                                    value=f":gem: Card Price: `{add_suffix(self.price)}`\n:gem: Winnings: `0`")
                    await self.interaction.edit_original_response(embed=embed,
                                                                  view=ScratchButtons(self.interaction, self.price,
                                                                                      self.multi, self.board,
                                                                                      self.revealed))
                else:
                    embed = discord.Embed(color=0x80ff8e, title=f"Scratch Card | You Win!",
                                          description="You found 3 of the same number!")
                    winnings = round(self.multi*self.price)
                    add_gems(str(self.interaction.user.id), winnings)
                    embed.set_footer(text="")
                    embed.set_author(name=Config['Bot Name'],
                                     icon_url=Config['Bot Icon'])
                    embed.add_field(name="Game Stats",
                                    value=f":gem: Card Price: `{add_suffix(self.price)}`\n:gem: Winnings: `{add_suffix(winnings)}`")
                    await self.interaction.edit_original_response(embed=embed,
                                                                  view=ScratchButtons(self.interaction, self.price,
                                                                                      self.multi, self.board,
                                                                                      self.revealed))
            await interaction.response.defer()

@bot.tree.command(name="scratch_card", description="Buy a scratch card")
async def scratch_card(interaction: discord.Interaction, price: str) :
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    valid = True
    uid = str(interaction.user.id)
    price = suffix_to_int(price)
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if price <= 999 :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Minimum Price Is 1k",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if price > get_gems(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Too Poor XD",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if valid :
        multi = generate_scratch_multiplier()
        subtract_gems(str(interaction.user.id), price)
        already_added = {}
        choices = [1.5, 2, 3, 5, 10]
        board = []
        if multi != 0:
            choices.remove(multi)
        if multi == 0:
            print("0")
            for i in range(0, 3) :
                print("0")
                row = []
                for i2 in range(0, 3) :
                    print("0")
                    while 1 :
                        choice = random.choice(choices)
                        if already_added.get(str(choice), 0) < 2 :
                            row.append(choice)
                            if str(choice) in already_added :
                                already_added[str(choice)] += 1
                            else :
                                already_added[str(choice)] = 1
                            break
                board.append(row)
        else:
            print("not 0")
            for i in range(0, 3) :
                row = []
                multirow = random.choice([0, 1, 2])
                for i2 in range(0, 3) :
                    if i2 == multirow:
                        row.append(multi)
                    else :
                        while 1 :
                            choice = random.choice(choices)
                            if already_added.get(str(choice), 0) < 2 :
                                row.append(choice)
                                if str(choice) in already_added :
                                    already_added[str(choice)] += 1
                                else :
                                    already_added[str(choice)] = 1
                                break
                board.append(row)
        print(board)
        embed = discord.Embed(color=0x208cdf, title=f"Scratch Card", description="Scratch off your numbers!")
        embed.set_footer(text="")
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.add_field(name="Game Stats", value=f":gem: Card Price: `{add_suffix(price)}`\n:gem: Winnings: `0`")
        await interaction.response.send_message(
            embed=embed,
            view=ScratchButtons(interaction, price, multi, board, [[False,False,False],[False,False,False],[False,False,False]]))

def base_keno_board(tiles) :
    table = []
    for i in range(0, tiles) :
        table.append("")
    return table


class NumberGenerator :
    def __init__(self) :
        self.numbers = list(range(23))

    def generate_number(self) :
        if not self.numbers :
            raise ValueError("No more numbers available.")

        num = random.choice(self.numbers)
        self.numbers.remove(num)
        return num


def keno_diff_to_string(diff) :
    if diff == "Easy" :
        return "0: 0.00x 1: 0.00x 2: 1.10x 3: 2.00x 4: 6.20x 5: 20x 6: 45x (Press The Confirm Button To Roll)"
    if diff == "Hard" :
        return "0: 0.00x 1: 0.00x 2: 0.00x 3: 0.00x 4: 11.00x 5: 50x 6: 200x (Press The Confirm Button To Roll)"


def amount_to_give(diff, tiles, bet) :
    if diff == "Easy" :
        multis = [0.00, 0.00, 1.50, 2.00, 5.00, 20.00, 50.00]
        return round(multis[tiles] * bet)
    if diff == "Hard" :
        multis = [0.00, 0.00, 0.00, 2.00, 10.00, 50.00, 200.00]
        return round(multis[tiles] * bet)


class KenoPlayButtons(discord.ui.View) :
    def __init__(self, bet, board, interaction, difficulty, tiles=0, roll=False) :
        super().__init__(timeout=None)
        self.bet = bet
        self.board = board
        self.interaction = interaction
        self.tiles = tiles
        self.roll = roll
        self.buttons = {}
        self.con = None
        self.can = None
        self.difficulty = difficulty
        numgen = NumberGenerator()
        self.numbers = []
        for _ in range(6) :
            num = numgen.generate_number()
            self.numbers.append(num)
        self.setup_buttons()

    async def roll_anim(self) :
        tiles = 0
        uid = str(self.interaction.user.id)
        subtract_gems(uid, self.bet)
        af = get_affiliate(uid)
        add_gems(af, self.bet * 0.01)
        db = readdata()
        try :
            db['users'][af]['Affiliate Earnings'] += self.bet * 0.01
        except :
            pass
        writedata(db)
        for number in self.numbers :
            b = self.buttons[number]
            if b.style == discord.ButtonStyle.gray :
                b.style = discord.ButtonStyle.red
            else :
                b.style = discord.ButtonStyle.green
                tiles = tiles + 1
        bal = amount_to_give(diff=self.difficulty, tiles=tiles, bet=self.bet)
        if bal == 0 :
            add_rake_back(str(uid), percentage(rb, self.bet))
        add_gems(uid, bal)
        add_bet(uid, self.bet, bal)
        embed = discord.Embed(title=f"Keno Game In Play!",
                              description=f"You hit {tiles} tiles: You won `{add_suffix(bal)}` gems!", color=0x57b6ff)
        embed.set_author(name=Config['Bot Name'], icon_url=Config['Bot Icon'])
        embed.set_footer(text="Good luck!")
        self.con.disabled = False
        self.can.disabled = False
        await self.interaction.edit_original_response(embed=embed, view=self)

    def setup_buttons(self) :
        for tile in range(0, len(self.board)) :
            tileF = self.board[tile]
            if tileF == "" :
                button = discord.ui.Button(label=f"{tile + 1}", custom_id=f"{tile}", style=discord.ButtonStyle.gray)
                button.disabled = True
                self.buttons[tile] = button
                self.add_item(button)
            else :
                button = discord.ui.Button(label=f"{tile + 1}", custom_id=f"{tile}", style=discord.ButtonStyle.blurple)
                button.disabled = True
                self.buttons[tile] = button
                self.add_item(button)
        cobutton = discord.ui.Button(label=f"", custom_id=f"confirm", style=discord.ButtonStyle.primary, emoji="✅")
        cobutton.callback = self.con_clicked
        if self.roll :
            cobutton.disabled = True
            cobutton.label = "Roll Again"
        self.con = cobutton
        self.add_item(cobutton)
        cabutton = discord.ui.Button(label=f"Cancel", custom_id=f"cancel", style=discord.ButtonStyle.red)
        cabutton.callback = self.del_clicked
        if self.roll :
            cabutton.disabled = True
        self.can = cabutton
        self.add_item(cabutton)
        if self.roll :
            asyncio.create_task(self.roll_anim())

    async def del_clicked(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        if interaction.user.id == self.interaction.user.id :
            await self.interaction.delete_original_response()

    async def con_clicked(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        if interaction.user.id == self.interaction.user.id and get_gems(str(self.interaction.user.id)) >= self.bet :
            embed = discord.Embed(title=f"Keno Game In Play!",
                                  description="Press the confirm button to roll!!",
                                  color=0x57b6ff)
            embed.set_author(name=Config['Bot Name'], icon_url=Config['Bot Icon'])
            embed.set_footer(text="Good luck!")
            await self.interaction.edit_original_response(embed=embed,
                                                          view=KenoPlayButtons(bet=self.bet, board=self.board,
                                                                               interaction=self.interaction, roll=True,
                                                                               difficulty=self.difficulty))
        if get_gems(str(self.interaction.user.id)) <= self.bet - 1 :
            await self.interaction.delete_original_response()


class KenoSelectButtons(discord.ui.View) :
    def __init__(self, bet, board, interaction, difficulty, tiles=0) :
        super().__init__(timeout=None)
        self.bet = bet
        self.board = board
        self.interaction = interaction
        self.tiles = tiles
        self.difficulty = difficulty
        self.setup_buttons()

    def setup_buttons(self) :
        for tile in range(0, len(self.board)) :
            tileF = self.board[tile]
            if tileF == "" :
                button = discord.ui.Button(label=f"{tile + 1}", custom_id=f"{tile}", style=discord.ButtonStyle.gray)
                button.callback = self.tile_clicked
                if self.tiles >= 6 :
                    button.disabled = True
                self.add_item(button)
            else :
                button = discord.ui.Button(label=f"{tile + 1}", custom_id=f"{tile}", style=discord.ButtonStyle.blurple)
                button.disabled = True
                self.add_item(button)
        cobutton = discord.ui.Button(label=f"", custom_id=f"confirm", style=discord.ButtonStyle.primary, emoji="✅")
        cobutton.callback = self.con_clicked
        if self.tiles <= 5 :
            cobutton.disabled = True
        self.add_item(cobutton)
        cabutton = discord.ui.Button(label=f"Cancel", custom_id=f"cancel", style=discord.ButtonStyle.red)
        cabutton.callback = self.del_clicked
        self.add_item(cabutton)

    async def tile_clicked(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            await interaction.response.defer()
            customid = interaction.data["custom_id"]
            self.board[int(customid)] = "s"
            self.tiles = self.tiles + 1
            embed = discord.Embed(title=f"Keno Game Created!",
                                  description="Select 6 random tiles to continue. Make sure they're lucky!",
                                  color=0x57b6ff)
            embed.set_author(name=Config['Bot Name'], icon_url=Config['Bot Icon'])
            embed.set_footer(text="Good luck!")
            await self.interaction.edit_original_response(
                embed=embed,
                view=KenoSelectButtons(bet=self.bet, board=self.board, interaction=self.interaction, tiles=self.tiles,
                                       difficulty=self.difficulty))

    async def del_clicked(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        if interaction.user.id == self.interaction.user.id :
            await self.interaction.delete_original_response()

    async def con_clicked(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        if interaction.user.id == self.interaction.user.id :
            embed = discord.Embed(title=f"Keno Game In Play!",
                                  description="Press the confirm button to roll!!",
                                  color=0x57b6ff)
            embed.set_author(name=Config['Bot Name'], icon_url=Config['Bot Icon'])
            embed.set_footer(text="Good luck!")
            await self.interaction.edit_original_response(embed=embed,
                                                          view=KenoPlayButtons(bet=self.bet, board=self.board,
                                                                               interaction=self.interaction,
                                                                               tiles=self.tiles,
                                                                               difficulty=self.difficulty))


@bot.tree.command(name="keno", description="Start A Game Of Keno (omg (wowzerz) (:star_struck:)))")
@app_commands.describe(difficulty="Easy or Hard")
async def keno(interaction: discord.Interaction, bet: str, difficulty: str) :
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    valid = True
    uid = str(interaction.user.id)
    bet = suffix_to_int(bet)
    valid_difficulties = ["Easy", "Hard"]
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if not difficulty in valid_difficulties :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Difficulty Can Only Be: Easy or Hard",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet <= 999 :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Minimum Bet Is 1k",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet > get_gems(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Too Poor XD",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if valid :
        embed = discord.Embed(title=f"Keno Game Created!", description="Select 6 random tiles to continue. Make sure they're lucky!", color=0x57b6ff)
        embed.set_author(name=Config['Bot Name'], icon_url=Config['Bot Icon'])
        embed.set_footer(text="Good luck!")
        await interaction.response.send_message(
            embed=embed,
            view=KenoSelectButtons(bet=bet, board=base_keno_board(23), interaction=interaction, difficulty=difficulty))


class TowersButtons(discord.ui.View) :
    def __init__(self, bet, interaction) :
        super().__init__(timeout=None)
        self.bet = bet
        self.interaction = interaction
        self.buttons = [[], [], [], [], []]
        self.layer = 0
        self.multi = 1.0
        self.cash = None
        self.setup_buttons()

    def setup_buttons(self) :
        for layer in range(0, 5) :
            for tower in range(0, 3) :
                button = discord.ui.Button(label=f"{add_suffix(round(Config['Towers']['Multis'][layer] * self.bet))}",
                                           custom_id=f"{layer} {tower}", style=discord.ButtonStyle.gray, row=layer,
                                           emoji="💰")
                button.callback = self.tower_clicked
                if layer == 0 :
                    button.style = discord.ButtonStyle.blurple
                self.buttons[layer].append(button)
                self.add_item(button)
        button = discord.ui.Button(label=f"Cashout", custom_id=f"cash", style=discord.ButtonStyle.green, row=4)
        button.callback = self.cash_clicked
        self.cash = button
        self.add_item(button)

    async def cash_clicked(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            await interaction.response.defer()
            winnings = round(self.bet * self.multi)
            add_gems(str(self.interaction.user.id), winnings)
            add_bet(str(self.interaction.user.id), self.bet, winnings)
            af = get_affiliate(str(self.interaction.user.id))
            for i2 in self.buttons :
                for i3 in i2 :
                    i3.disabled = True
            self.cash.disabled = True
            embed = discord.Embed(title="Cashed Out Towers!",
                                  description="You cashed out your towers game!",
                                  color=0x57b6ff)
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="Climb as high as you can!")
            embed.add_field(name="Game Data",value=f":gem: Bet: `{add_suffix(self.bet)}`\n:gem: Winnings: `{add_suffix(winnings)}`")
            await self.interaction.edit_original_response(
                embed=embed,
                view=self)

    async def tower_clicked(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            await interaction.response.defer()
            customid = interaction.data["custom_id"]
            layer = int(customid.split(" ")[0])
            tower = int(customid.split(" ")[1])
            print(layer)
            print(self.layer)
            if layer == self.layer :
                for tower2 in self.buttons[layer] :
                    tower2.disabled = True
                    tower2.style = discord.ButtonStyle.gray
                if layer != 4 :
                    for tower2 in self.buttons[layer + 1] :
                        tower2.style = discord.ButtonStyle.blurple
                if roll_percentage(Config['Towers']['WinChance']) :
                    self.buttons[layer][tower].style = discord.ButtonStyle.green
                    self.multi = Config["Towers"]["Multis"][layer]
                else :
                    self.buttons[layer][tower].style = discord.ButtonStyle.red
                    self.cash.disabled = True
                    await self.interaction.edit_original_response(view=self)
                    for i2 in self.buttons :
                        for i3 in i2 :
                            i3.disabled = True
                    await self.interaction.edit_original_response(view=self)
                    await asyncio.sleep(3)
                    add_rake_back(str(interaction.user.id), percentage(rb, self.bet))
                    add_bet(str(interaction.user.id), self.bet, 0)
                    return
                await self.interaction.edit_original_response(view=self)
                self.layer = self.layer + 1


@bot.tree.command(name="towers", description="Start A Game Of Towers")
async def towers(interaction: discord.Interaction, bet: str) :
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    valid = True
    uid = str(interaction.user.id)
    bet = suffix_to_int(bet)
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet <= 999 :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Minimum Bet Is 1k",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet > get_gems(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Too Poor XD",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if valid :
        subtract_gems(uid, bet)
        af = get_affiliate(str(interaction.user.id))
        add_gems(af, bet * 0.01)
        db = readdata()
        try :
            db['users'][af]['Affiliate Earnings'] += bet * 0.01
        except :
            pass
        writedata(db)
        await log(f"<@{uid}> Bet {add_suffix(bet)}> On Towers")
        embed = discord.Embed(title="Towers", description="Press one of the blue buttons to climb! 2 are safe and will give you more money, however, one is unstable and will cause you to fall.", color=0x57b6ff)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="Climb as high as you can!")
        embed.add_field(name="Game Data",value=f":gem: Bet: `{add_suffix(bet)}`")
        await interaction.response.send_message(embed=embed, view=TowersButtons(bet=bet, interaction=interaction))


class FlipButtons(discord.ui.View) :
    def __init__(self, msg, bet, side, user) :
        super().__init__(timeout=None)
        self.bet = bet
        self.msg = msg
        self.side = side
        self.user = user
        self.buttons = []
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label=f"Join", custom_id=f"join", style=discord.ButtonStyle.primary, emoji="🪙")
        button.callback = self.join_clicked
        self.buttons.append(button)
        self.add_item(button)
        button = discord.ui.Button(label=f"Call Bot", custom_id=f"bot", style=discord.ButtonStyle.green, emoji="🤖")
        button.callback = self.bot
        self.buttons.append(button)
        self.add_item(button)

    async def join_clicked(self, interaction: discord.Interaction) :
        uid = str(interaction.user.id)
        if not is_registered(str(interaction.user.id)) :
            register_user(str(interaction.user.id))
        if get_gems(uid) < self.bet :
            await interaction.response.send_message(content="You cant afford this pooron", ephemeral=True)
            return
        if uid == self.user :
            await interaction.response.send_message(content="NAHH BRO U CANT JOIN UR OWN FLIP :skull:", ephemeral=True)
            return
        await interaction.response.send_message(content="Joined the game", ephemeral=True)
        for button in self.buttons :
            button.disabled = True
        subtract_gems(uid, self.bet)
        af = get_affiliate(str(interaction.user.id))
        add_gems(af, self.bet * 0.01)
        db = readdata()
        try :
            db['users'][af]['Affiliate Earnings'] += self.bet * 0.01
        except :
            pass
        writedata(db)
        await self.msg.edit(view=self)
        choiches = ["Heads", "Tails"]
        choice = random.choice(choiches)
        embed = discord.Embed(title=f"Rolled {choice}", description=f"", color=0xffc800)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        if self.side == "Heads" :
            embed.add_field(name="Flip", value=f":coin: **{self.side}:** <@{self.user}>\n:coin: **Tails:** <@{uid}>")
        if self.side == "Tails" :
            embed.add_field(name="Flip", value=f":coin: **{self.side}:** <@{self.user}>\n:coin: **Heads:** du<@{uid}>")
        if choice == self.side :
            embed.add_field(name="Winner", value=f"<@{self.user}> - {add_suffix(round(self.bet * 1.95))}")
            add_gems(self.user, round(self.bet * 2.05))
            add_bet(self.user, self.bet, round(self.bet * 2.05))
            add_bet(uid, self.bet, 0)
        else :
            embed.add_field(name="Winner", value=f"<@{uid}> - {add_suffix(round(self.bet * 1.95))}")
            add_gems(uid, round(self.bet * 1.95))
            add_bet(uid, self.bet, round(self.bet * 1.95))
            add_bet(self.user, self.bet, 0)
            add_rake_back(self.user, percentage(rb, self.bet))
        await self.msg.edit(embed=embed)

    async def bot(self, interaction: discord.Interaction) :
        if not is_registered(str(bot.user.id)):
            register_user(str(bot.user.id))
        uid = str(bot.user.id)
        await interaction.response.send_message(content="Joined the game", ephemeral=True)
        for button in self.buttons :
            button.disabled = True
        subtract_gems(uid, self.bet)
        await self.msg.edit(view=self)
        choice = "Tails"
        if self.side == "Heads" :
            if roll_percentage(50 + Config['Coinflip']['House']) :
                choice = "Tails"
            else :
                choice = "Heads"
        if self.side == "Tails" :
            if roll_percentage(50 + Config['Coinflip']['House']) :
                choice = "Heads"
            else :
                choice = "Tails"
        embed = discord.Embed(title=f"Rolled {choice}", description=f"", color=0xffc800)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        if self.side == "Heads" :
            embed.add_field(name="Flip", value=f":coin: **{self.side}:** <@{self.user}>\n:coin: **Tails:** <@{uid}>")
        if self.side == "Tails" :
            embed.add_field(name="Flip", value=f":coin: **{self.side}:** <@{self.user}>\n:coin: **Heads:** du<@{uid}>")
        if choice == self.side :
            embed.add_field(name="Winner", value=f"<@{self.user}> - {add_suffix(round(self.bet * 1.95))}")
            add_gems(self.user, round(self.bet * 1.95))
            add_bet(self.user, self.bet, round(self.bet * 1.95))
            add_bet(uid, self.bet, 0)
        else :
            embed.add_field(name="Winner", value=f"<@{uid}> - {add_suffix(round(self.bet * 1.95))}")
            add_gems(uid, round(self.bet * 1.95))
            add_rake_back(self.user, percentage(rb, self.bet))
            add_bet(self.user, self.bet, 0)
            add_bet(uid, self.bet, round(self.bet * 1.95))
        await self.msg.edit(embed=embed)


@bot.tree.command(name="1v1-flip", description="1v1 Coinflip (:scream:)")
async def flip(interaction: discord.Interaction, bet: str, side: CoinSide) :
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    valid = True
    uid = str(interaction.user.id)
    bet = suffix_to_int(bet)
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet <= 999 :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Minimum Bet Is 1k",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet > get_gems(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Too Poor XD",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if valid :
        subtract_gems(uid, bet)
        af = get_affiliate(str(interaction.user.id))
        add_gems(af, bet * 0.01)
        db = readdata()
        try :
            db['users'][af]['Affiliate Earnings'] += bet * 0.01
        except :
            pass
        writedata(db)
        channel = bot.get_channel(int(Config['Coinflip']['1v1']))
        embed = discord.Embed(title="Coinflip", description=f"<@{uid}> Started A Coinflip", color=0xffc800)
        if side.value == "Heads" :
            embed.add_field(name="Flip", value=f":coin: **{side.value}:** <@{uid}>\n:coin: **Tails:** ``???``")
        if side.value == "Tails" :
            embed.add_field(name="Flip", value=f":coin: **{side.value}:** <@{uid}>\n:coin: **Heads:** ``???``")
        embed.add_field(name="Bet", value=f":gem: **Amount:** ``{add_suffix(bet)}``")
        embed.set_footer(text="Will it be heads or tails?")
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        msg = await channel.send(embed=embed)
        await msg.edit(embed=embed, view=FlipButtons(msg, bet, side.value, uid))
        await interaction.response.send_message(content=f"<#{Config['Coinflip']['1v1']}>")
def open_case(Case):
    casesdata = get_cases()
    casedata = {}
    for case in casesdata:
        if case['Name'] == Case:
            casedata = case
    choice = None
    for pet in reversed(casedata['Drops']):
        if roll_percentage(pet['Chance']):
            choice = pet
            break
    if choice == None:
        choice = casedata['Drops'][0]
    return choice
@bot.tree.command(name="cases", description="View All Cases")
async def cases(interaction: discord.Interaction):
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    embed = discord.Embed(title="Cases", description="Viewing a list of all cases currently in the bot.",
                          color=0x6652ff)
    embed.set_author(name=Config['Bot Name'],
                     icon_url=Config['Bot Icon'])
    for case in get_cases():
        infostr = ""
        for pet in case['Drops']:
            infostr += f"- {pet['Name']} ({pet['Chance']}%) - ``{add_suffix(pet['Worth'])}``\n"
        embed.add_field(name=f"{case['Name']}", value=f":gem: **Price:** ``{add_suffix(case['Price'])}``\n:four_leaf_clover: **Drops:**\n{infostr}", inline=False)
        embed.set_footer(text="cases")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="unbox-case", description="Open a Case")
async def unbox_case(interaction: discord.Interaction, case_name: str):
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    casedata = None
    for caseD in get_cases():
        if caseD['Name'] == case_name:
            casedata = caseD
            break
    if not casedata:
        embed = discord.Embed(title=":x: Error",
                              description="Invalid Case! Do /cases For A List Of All Cases",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    if get_gems(uid) < casedata['Price']:
        embed = discord.Embed(title=":x: Error",
                              description="You Cannot Afford This Case",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    outcome = open_case(case_name)
    subtract_gems(uid, casedata['Price'])
    embed = discord.Embed(title="Opening Case", description=f"Opening {case_name} <t:{round(time.time()+5)}:R>")
    embed.set_thumbnail(url=casedata['Icon'])
    await interaction.response.send_message(embed=embed)
    await asyncio.sleep(5)
    embed = None
    add_gems(uid, outcome['Worth'])
    add_bet(uid,casedata['Price'],outcome['Worth'])
    if casedata['Price'] <= outcome['Worth']:
        embed = discord.Embed(title="Opened Case", description=f"You Unboxed A {outcome['Name']}!",color=0x82ff80)
        embed.add_field(name="Winnings",value=f":gem: **Case Price**: ``{add_suffix(casedata['Price'])}``\n:gem: **{outcome['Name']} Price**: ``{add_suffix(outcome['Worth'])}``\n:gem: **Profit**: ``{add_suffix(outcome['Worth']-casedata['Price'])}``")
        embed.set_thumbnail(url=outcome['Icon'])
    else:
        embed = discord.Embed(title="Opened Case", description=f"You Unboxed A {outcome['Name']}!", color=0xff7575)
        embed.add_field(name="Winnings", value=f":gem: **Case Price**: ``{add_suffix(casedata['Price'])}``\n:gem: **{outcome['Name']} Price**: ``{add_suffix(outcome['Worth'])}``\n:gem: **Profit**: ``-{add_suffix(casedata['Price'] - outcome['Worth'])}``")
        embed.set_thumbnail(url=outcome['Icon'])
    await interaction.edit_original_response(embed=embed)

class UpgradeButton(discord.ui.View) :
    def __init__(self, interaction, bet, chance, multiplier, roll=1):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.bet = bet
        self.chance = chance
        self.multiplier = multiplier
        self.roll = roll
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label=f"Upgrade", custom_id=f"join", style=discord.ButtonStyle.blurple, emoji="💰")
        button.callback = self.join_clicked
        self.add_item(button)
    async def join_clicked(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        af = get_affiliate(uid)
        add_gems(af, self.bet * 0.01)
        db = readdata()
        try :
            db['users'][af]['Affiliate Earnings'] += self.bet * 0.01
        except :
            pass
        print("1")
        if uid != str(self.interaction.user.id):
            return
        print("2")
        if self.bet > get_gems(uid):
            await self.interaction.edit_original_response(embed=fail("You Can No Longer Afford This Bet"),view=None)
            return
        print("3")
        subtract_gems(uid,self.bet)
        won = roll_percentage(self.chance)

        if won:
            print("4")
            add_gems(uid, round(self.bet*self.multiplier))
            add_bet(uid, self.bet, self.bet*self.multiplier)
            embed = discord.Embed(title="Upgrade Won!",description="You won this upgrade!",color=0x4dff58)
            embed.add_field(name="Input", value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:four_leaf_clover: **Chance:** ``{round(self.chance, 1)}%``\n:star: **Multiplier:** ``{self.multiplier}x``\n:moneybag: **Winnings:** ``{add_suffix(round(self.bet*self.multiplier))}``")
            await self.interaction.edit_original_response(embed=embed, view=None)
        else:
            print("5")
            add_bet(uid, self.bet, 0)
            embed = discord.Embed(title="Upgrade Lost!",description="You lost this upgrade!",color=0xff6b6b)
            embed.add_field(name="Input", value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:four_leaf_clover: **Chance:** ``{round(self.chance, 1)}%``\n:star: **Multiplier:** ``{self.multiplier}x``\n:moneybag: **Winnings:** ``{add_suffix(round(self.bet*self.multiplier))}``")
            await self.interaction.edit_original_response(embed=embed, view=None)

green = 0x4dff58
red = 0xff6b6b
yellow = 0xfff93d

@bot.tree.command(name="upgrader", description="Put Some Gems In The Upgrade Machine!")
async def upgrade(interaction: discord.Interaction, bet: str, multiplier: float):
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    bet = suffix_to_int(bet)
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    if multiplier < 1.1:
        embed = discord.Embed(title=":x: Error",
                              description="Invalid Multiplier! Cannot be under 1.1",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    if get_gems(uid) < bet:
        embed = discord.Embed(title=":x: Error",
                              description="You Cannot Afford This Bet",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    if bet < 999:
        embed = discord.Embed(title=":x: Error",
                              description="Cannot bet under 1k",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    embed = discord.Embed(title="Upgrade Machine", description="Have a chance at upgrading your bet or losing everything!",color=0x4dbbff)
    win_chance = multiplier_to_percentage(multiplier,Config['Upgrader']['House'])
    winnings = round(bet*multiplier)
    embed.add_field(name="Input",value=f":gem: **Bet:** ``{add_suffix(bet)}``\n:four_leaf_clover: **Chance:** ``{round(win_chance, 1)}%``\n:star: **Multiplier:** ``{multiplier}x``\n:moneybag: **Winnings:** ``{add_suffix(winnings)}``")

    await interaction.response.send_message(embed=embed,view=UpgradeButton(interaction,bet,win_chance,multiplier))
def roll_dice():
    return random.randint(1, 6)
@bot.tree.command(name="dice", description="Roll A Dice Against The Bot")
async def dice(interaction: discord.Interaction, bet: str):
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    bet = suffix_to_int(bet)
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    if get_gems(uid) < bet :
        embed = discord.Embed(title=":x: Error",
                              description="You Cannot Afford This Bet",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    if bet < 999 :
        embed = discord.Embed(title=":x: Error",
                              description="Cannot bet under 1k",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    yourdie = roll_dice()
    botdie = roll_dice()
    subtract_gems(uid,bet)
    winnings = 0
    af = get_affiliate(uid)
    add_gems(af, bet * 0.01)
    db = readdata()
    try:
        db['users'][af]['Affiliate Earnings'] += bet * 0.01
    except:
        pass
    if yourdie > botdie:
        winnings = round((bet*2)/1.02)
        embed = discord.Embed(title="You Rolled A Dice!", description="You Rolled Higher Than The Bot. You Win!", color=green)
        embed.add_field(name="Game",value=f"🎲 **You Rolled:** ``{yourdie}``\n🎲 **Bot Rolled:** ``{botdie}``\n:gem: **Winnings:** ``{add_suffix(winnings)}``")
    elif yourdie < botdie:
        winnings = 0
        embed = discord.Embed(title="You Rolled A Dice!", description="You Rolled Lower Than The Bot. You Lose!",
                              color=red)
        embed.add_field(name="Game",
                        value=f"🎲 **You Rolled:** ``{yourdie}``\n🎲 **Bot Rolled:** ``{botdie}``\n:gem: **Winnings:** ``{add_suffix(winnings)}``")
    else:
        winnings = bet
        embed = discord.Embed(title="You Rolled A Dice!", description="Its A Tie!",
                              color=yellow)
        embed.add_field(name="Game",
                        value=f"🎲 **You Rolled:** ``{yourdie}``\n🎲 **Bot Rolled:** ``{botdie}``\n:gem: **Winnings:** ``{add_suffix(winnings)}``")
    add_gems(uid, winnings)
    add_bet(uid, bet, winnings)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="set-gems",description="Administrator Required")
async def setgems(interaction: discord.Interaction, user: discord.Member, gems: str):
    gems = suffix_to_int(gems)
    uid = str(user.id)
    if interaction.user.guild_permissions.administrator:
        set_gems(uid, gems)
        await interaction.response.send_message(embed=succeed(f"Set <@{uid}> Gems To {add_suffix(gems)}"))
@bot.tree.command(name="add-gems",description="Administrator Required")
async def addgems(interaction: discord.Interaction, user: discord.Member, gems: str):
    gems = suffix_to_int(gems)
    uid = str(user.id)
    if interaction.user.guild_permissions.administrator:
        add_gems(uid, gems)
        await interaction.response.send_message(embed=succeed(f"Added {add_suffix(gems)} Gems To <@{uid}>"))
@bot.tree.command(name="remove-gems",description="Administrator Required")
async def removegems(interaction: discord.Interaction, user: discord.Member, gems: str):
    gems = suffix_to_int(gems)
    uid = str(user.id)
    if interaction.user.guild_permissions.administrator:
        subtract_gems(uid, gems)
        await interaction.response.send_message(embed=succeed(f"Removed {add_suffix(gems)} Gems From <@{uid}>"))

@bot.tree.command(name="roulette", description="Spin the roulette wheel")
async def roulette(interaction: discord.Interaction, bet: str, color: Colors):
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
    bet = suffix_to_int(bet)
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="roulette")
        await interaction.response.send_message(embed=embed)
        return
    if get_gems(uid) < bet:
        embed = discord.Embed(title=":x: Error",
                              description="You Cannot Afford This Bet",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="roulette")
        await interaction.response.send_message(embed=embed)
        return
    if bet < 999:
        embed = discord.Embed(title=":x: Error",
                              description="Cannot bet under 1k",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="roulette")
        await interaction.response.send_message(embed=embed)
        return
    won = False
    winnings = 0
    print(color.value)
    if color.name == "Blue":
        won = roll_percentage(46)
        if won:
            winnings = bet*2
    if color.name == "Purple":
        won = roll_percentage(46)
        if won:
            winnings = bet*2
    if color.name == "Gold":
        won = roll_percentage(8)
        if won:
            winnings = bet*8
    timee = time.time()+5
    embed = discord.Embed(title="Roullete",
                          description=f"You placed `{add_suffix(bet)}` gems on `{color.name}`. Rolling <t:{round(timee)}:R>", color=0xadadad)
    embed.set_author(name=Config['Bot Name'],
                     icon_url=Config['Bot Icon'])
    embed.set_footer(text="Good luck!")
    await interaction.response.send_message(embed=embed)
    await asyncio.sleep(5)
    if won:
        embed = discord.Embed(title="Roullete Won!",
                              description=f"You placed `{add_suffix(bet)}` gems on `{color.name}`", color=0x62ff57)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="Good luck!")
        embed.add_field(name="Game Outcome", value=f":gem: Bet: `{add_suffix(bet)}`\n:star: Color Chosen: `{color.value}`\n:gem: Winnings: `{add_suffix(winnings)}`")
    else:
        embed = discord.Embed(title="Roullete Lost!",
                              description=f"You placed `{add_suffix(bet)}` gems on `{color.name}`", color=0xff5757)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="Good luck!")
        embed.add_field(name="Game Outcome", value=f":gem: Bet: `{add_suffix(bet)}`\n")
    await interaction.edit_original_response(embed=embed)

@bot.tree.command(name="create-promocode", description="Create a promocode")
async def cp(interaction: discord.Interaction, code: str, reward: str, max_uses: int):
    if interaction.user.guild_permissions.administrator :
        with open("promocodes.json", "r") as f:
            pc = json.loads(f.read())
        reward = suffix_to_int(reward)
        pc.append({"code": code, "reward": reward, "max_uses": max_uses, "uses": 0, "users": []})
        with open("promocodes.json", "w") as f:
            f.write(json.dumps(pc))
        embed = discord.Embed(title="Promocode Created!", description=f"You created the promocode: `{code}`", color=0x62ff57)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="Thanks for your generosity!")
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="redeem-promocode", description="Redeem a promocode")
async def rcp(interaction: discord.Interaction, code: str):
    with open("promocodes.json", "r") as f:
        pc = json.loads(f.read())
    reward = 0
    for pcc in pc:
        if pcc['code'] == code:
            if pcc['max_uses'] > pcc['uses'] and interaction.user.id not in pcc['users']:
                reward = pcc['reward']
                pcc['uses'] += 1
                pcc['users'].append(interaction.user.id)
    with open("promocodes.json", "w") as f:
        f.write(json.dumps(pc))

    if reward > 0:
        add_gems(str(interaction.user.id), reward)
        embed = discord.Embed(title="Promocode Redeemed!", description=f"You redeemed the code: `{code}` and got `{add_suffix(reward)}` Gems!", color=0x62ff57)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="free gems!")
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="Invalid Code!", description=f"This code dosent seem to exist, has hit its max uses or you have already redeemed it.", color=0xff3d3d)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="free gems!")
        await interaction.response.send_message(embed=embed)

basedeck = [
    "2♠", "3♠", "4♠", "5♠", "6♠", "7♠", "8♠", "9♠", "10♠", "J♠", "Q♠", "K♠", "A♠",
    "2♥", "3♥", "4♥", "5♥", "6♥", "7♥", "8♥", "9♥", "10♥", "J♥", "Q♥", "K♥", "A♥",
    "2♦", "3♦", "4♦", "5♦", "6♦", "7♦", "8♦", "9♦", "10♦", "J♦", "Q♦", "K♦", "A♦",
    "2♣", "3♣", "4♣", "5♣", "6♣", "7♣", "8♣", "9♣", "10♣", "J♣", "Q♣", "K♣", "A♣"
]


def card_to_value(card) :
    if "10" in card:
        return 10
    card = card[0]
    if card == "J" :
        card = 10
    if card == "Q" :
        card = 10
    if card == "K" :
        card = 10
    if card == "A" :
        card = 11
    return int(card)


def hand_to_value(hand) :
    dvalue = 0
    for card in hand :
        dvalue += card_to_value(card)
    return dvalue


def pick_card(deck) :
    card = random.choice(deck)
    deck.remove(card)
    return card, deck


def render_blackjack_hand(hand, hide) :
    if not hide :
        Hstr = ""
        Hvalue = hand_to_value(hand)
        for card in hand :
            Hstr += f"**{card}**  "
        Hstr += f"\n\n**Value:** ``{Hvalue}``"
        return Hstr
    else :
        Hstr = ""
        Hvalue = card_to_value(hand[0])
        Hstr += f"**{hand[0]}**  ??"
        Hstr += f"\n\n**Value:** ``{Hvalue}``"
        return Hstr


class BJButton(discord.ui.View) :
    def __init__(self, interaction, bet, user_hand, dealer_hand, deck) :
        super().__init__(timeout=None)
        self.interaction = interaction
        self.bet = bet
        self.user_hand = user_hand
        self.dealer_hand = dealer_hand
        self.deck = deck
        self.buttons = []
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label=f"Hit", custom_id=f"hit", style=discord.ButtonStyle.green, emoji="🎯")
        button.callback = self.hit_clicked
        self.buttons.append(button)
        self.add_item(button)
        button = discord.ui.Button(label=f"Stand", custom_id=f"stand", style=discord.ButtonStyle.red, emoji="⚫")
        button.callback = self.stand_clicked
        self.buttons.append(button)
        self.add_item(button)
        button = discord.ui.Button(label=f"Double", custom_id=f"double", style=discord.ButtonStyle.blurple, emoji="💰")
        button.callback = self.double_clicked
        self.buttons.append(button)
        self.add_item(button)

    async def hit_clicked(self, interaction: discord.Interaction) :
        uid = str(interaction.user.id)
        await interaction.response.defer()
        if uid != str(self.interaction.user.id) :
            return
        card, self.deck = pick_card(self.deck)
        self.user_hand.append(card)
        if hand_to_value(self.user_hand) == 21 :
            add_gems(uid, self.bet * 2)
            add_bet(uid, self.bet, self.bet*2)
            embed = discord.Embed(title="Blackjack - You Won!", description="You Got 21!", color=green)
            embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(self.user_hand, False))
            embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(self.dealer_hand, False))
            embed.add_field(name="👑 Bet",
                            value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(self.bet * 2)}``")
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="good luck!")
            await self.interaction.edit_original_response(embed=embed, view=None)
            return
        if hand_to_value(self.user_hand) >= 22 :
            add_bet(uid, self.bet, 0)
            embed = discord.Embed(title="Blackjack - You Lost!", description="You Went Bust!", color=red)
            embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(self.user_hand, False))
            embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(self.dealer_hand, False))
            embed.add_field(name="👑 Bet",
                            value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(self.bet * 2)}``")
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="good luck!")
            await self.interaction.edit_original_response(embed=embed, view=None)
            return
        embed = discord.Embed(title="Blackjack", description="Hit Or Stand?", color=yellow)
        embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(self.user_hand, False))
        embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(self.dealer_hand, True))
        embed.add_field(name="👑 Bet",
                        value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(self.bet * 2)}``")
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="good luck!")
        await self.interaction.edit_original_response(embed=embed,
                                                      view=BJButton(self.interaction, self.bet, self.user_hand,
                                                                    self.dealer_hand, self.deck))

    async def stand_clicked(self, interaction: discord.Interaction) :
        uid = str(interaction.user.id)
        await interaction.response.defer()
        if uid != str(self.interaction.user.id) :
            return
        await self.interaction.edit_original_response(view=None)
        while 1 :
            if hand_to_value(self.dealer_hand) >= 17 :
                break
            card, self.deck = pick_card(self.deck)
            self.dealer_hand.append(card)
        if hand_to_value(self.dealer_hand) == 21 :
            add_bet(uid, self.bet, 0)
            embed = discord.Embed(title="Blackjack - You Lost!", description="Dealer Got 21!", color=red)
            embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(self.user_hand, False))
            embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(self.dealer_hand, False))
            embed.add_field(name="👑 Bet",
                            value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(self.bet * 2)}``")
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="good luck!")
            await self.interaction.edit_original_response(embed=embed, view=None)
            return
        if hand_to_value(self.dealer_hand) >= 22 :
            add_gems(uid, self.bet * 2)
            add_bet(uid, self.bet, self.bet*2)
            embed = discord.Embed(title="Blackjack - You Won!", description="You won", color=green)
            embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(self.user_hand, False))
            embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(self.dealer_hand, False))
            embed.add_field(name="👑 Bet",
                            value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(self.bet * 2)}``")
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="good luck!")
            await self.interaction.edit_original_response(embed=embed, view=None)
            return
        if hand_to_value(self.dealer_hand) < hand_to_value(self.user_hand) :
            add_gems(uid, self.bet * 2)
            add_bet(uid, self.bet, self.bet*2)
            embed = discord.Embed(title="Blackjack - You Won!", description="You won", color=green)
            embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(self.user_hand, False))
            embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(self.dealer_hand, False))
            embed.add_field(name="👑 Bet",
                            value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(self.bet * 2)}``")
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="good luck!")
            await self.interaction.edit_original_response(embed=embed, view=None)
        if hand_to_value(self.dealer_hand) > hand_to_value(self.user_hand) :
            add_bet(uid, self.bet, 0)
            embed = discord.Embed(title="Blackjack - You Lost!", description="you lost", color=red)
            embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(self.user_hand, False))
            embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(self.dealer_hand, False))
            embed.add_field(name="👑 Bet",
                            value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(self.bet * 2)}``")
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="good luck!")
            await self.interaction.edit_original_response(embed=embed, view=None)
            return

    async def double_clicked(self, interaction: discord.Interaction) :
        uid = str(interaction.user.id)
        await interaction.response.defer()
        if uid != str(self.interaction.user.id) :
            return
        self.bet = self.bet * 2
        subtract_gems(uid, self.bet / 2)
        await self.interaction.edit_original_response(view=None)
        card, self.deck = pick_card(self.deck)
        self.user_hand.append(card)
        if hand_to_value(self.user_hand) == 21 :
            add_gems(uid, self.bet * 2)
            add_bet(uid, self.bet, self.bet*2)
            embed = discord.Embed(title="Blackjack - You Won!", description="You Got 21!", color=green)
            embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(self.user_hand, False))
            embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(self.dealer_hand, False))
            embed.add_field(name="👑 Bet",
                            value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(self.bet * 2)}``")
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="good luck!")
            await self.interaction.edit_original_response(embed=embed, view=None)
            return
        if hand_to_value(self.user_hand) >= 22 :
            add_bet(uid, self.bet, 0)
            embed = discord.Embed(title="Blackjack - You Lost!", description="You Went Bust!", color=red)
            embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(self.user_hand, False))
            embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(self.dealer_hand, False))
            embed.add_field(name="👑 Bet",
                            value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(self.bet * 2)}``")
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="good luck!")
            await self.interaction.edit_original_response(embed=embed, view=None)
            return

        while 1 :
            if hand_to_value(self.dealer_hand) >= 17 :
                break
            card, self.deck = pick_card(self.deck)
            self.dealer_hand.append(card)
        if hand_to_value(self.dealer_hand) == 21 :
            embed = discord.Embed(title="Blackjack - You Lost!", description="Dealer Got 21!", color=red)
            add_bet(uid, self.bet, 0)
            embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(self.user_hand, False))
            embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(self.dealer_hand, False))
            embed.add_field(name="👑 Bet",
                            value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(self.bet * 2)}``")
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="good luck!")
            await self.interaction.edit_original_response(embed=embed, view=None)
            return
        if hand_to_value(self.dealer_hand) >= 22 :
            add_gems(uid, self.bet * 2)
            add_bet(uid, self.bet, self.bet*2)
            embed = discord.Embed(title="Blackjack - You Won!", description="You won", color=green)
            embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(self.user_hand, False))
            embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(self.dealer_hand, False))
            embed.add_field(name="👑 Bet",
                            value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(self.bet * 2)}``")
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="good luck!")
            await self.interaction.edit_original_response(embed=embed, view=None)
            return
        if hand_to_value(self.dealer_hand) < hand_to_value(self.user_hand) :
            add_gems(uid, self.bet * 2)
            add_bet(uid, self.bet, self.bet*2)
            embed = discord.Embed(title="Blackjack - You Won!", description="You won", color=green)
            embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(self.user_hand, False))
            embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(self.dealer_hand, False))
            embed.add_field(name="👑 Bet",
                            value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(self.bet * 2)}``")
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="good luck!")
            await self.interaction.edit_original_response(embed=embed, view=None)
        if hand_to_value(self.dealer_hand) > hand_to_value(self.user_hand) :
            add_bet(uid, self.bet, 0)
            embed = discord.Embed(title="Blackjack - You Lost!", description="you lost", color=red)
            embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(self.user_hand, False))
            embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(self.dealer_hand, False))
            embed.add_field(name="👑 Bet",
                            value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(self.bet * 2)}``")
            embed.set_author(name=Config['Bot Name'],
                             icon_url=Config['Bot Icon'])
            embed.set_footer(text="good luck!")
            await self.interaction.edit_original_response(embed=embed, view=None)
            return


@bot.tree.command(name="blackjack", description="Play A Game Of BJ")
async def blackjack(interaction: discord.Interaction, bet: str) :
    bet = suffix_to_int(bet)
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        register_user(uid)
    if not is_registered(uid) :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="good luck!")
        await interaction.response.send_message(embed=embed)
        return
    if get_gems(uid) < bet :
        embed = discord.Embed(title=":x: Error",
                              description="You Cannot Afford This Bet",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="good luck!")
        await interaction.response.send_message(embed=embed)
        return
    if bet < 1000 :
        embed = discord.Embed(title=":x: Error",
                              description="Cannot bet under 1k",
                              color=0xff0000)
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="good luck!")
        await interaction.response.send_message(embed=embed)
        return
    subtract_gems(uid, bet)
    deck = basedeck
    user_hand = []
    card, deck = pick_card(deck)
    user_hand.append(card)
    card, deck = pick_card(deck)
    user_hand.append(card)
    dealer_hand = []
    card, deck = pick_card(deck)
    dealer_hand.append(card)
    card, deck = pick_card(deck)
    dealer_hand.append(card)

    if hand_to_value(user_hand) == 21 :
        add_gems(uid, bet * 2)
        embed = discord.Embed(title="Blackjack - You Won!", description="You Got 21!", color=green)
        embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(user_hand, False))
        embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(dealer_hand, False))
        embed.add_field(name="👑 Bet",
                        value=f":gem: **Bet:** ``{add_suffix(bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(bet * 2)}``")
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="good luck!")
        await interaction.response.send_message(embed=embed)
        return
    if hand_to_value(dealer_hand) == 21 :
        embed = discord.Embed(title="Blackjack - You Lost!", description="Dealer Got 21!", color=red)
        embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(user_hand, False))
        embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(dealer_hand, False))
        embed.add_field(name="👑 Bet",
                        value=f":gem: **Bet:** ``{add_suffix(bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(bet * 2)}``")
        embed.set_author(name=Config['Bot Name'],
                         icon_url=Config['Bot Icon'])
        embed.set_footer(text="good luck!")
        await interaction.response.send_message(embed=embed)
        return
    embed = discord.Embed(title="Blackjack", description="Hit Or Stand?", color=yellow)
    embed.add_field(name="👑 Your Hand", value=render_blackjack_hand(user_hand, False))
    embed.add_field(name="👑 Dealer Hand", value=render_blackjack_hand(dealer_hand, True))
    embed.add_field(name="👑 Bet",
                    value=f":gem: **Bet:** ``{add_suffix(bet)}``\n:gem: **Potential Winnings:** ``{add_suffix(bet * 2)}``")
    embed.set_author(name=Config['Bot Name'],
                     icon_url=Config['Bot Icon'])
    embed.set_footer(text="good luck!")
    await interaction.response.send_message(embed=embed, view=BJButton(interaction, bet, user_hand, dealer_hand, deck))


from multiprocessing import Process

def start_bot():
    bot.run(Config['DiscordBotToken'])

def start_web_server():
    app.run(debug=False, port=80, host="0.0.0.0")

if __name__ == '__main__':
    flask_process = Process(target=start_web_server)
    discord_process = Process(target=start_bot)

    flask_process.start()
    discord_process.start()

    flask_process.join()
    discord_process.join()