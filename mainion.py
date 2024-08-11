import os
import time
import discord
from discord import app_commands
import teyvatdle as tvd

GUILD_ID = os.getenv('GUILD_ID') # debugging server id

class Teyvatdle:
    help = """Guess a character from Teyvat (Genshin Impact) by typing their names!\
            \nThe characteristics of each guess will be colored like this:\
            \n> 🟩 GREEN squares = correct characteristics (in common)
                > 🟨 YELLOW squares = "close" characteristics
                > 🟥 RED squares = incorrect characteristics"""

    def __init__(self, message):
        self.channel = message.channel
        self.start_time = time.time()
        self.attempts = 0
        self.score = ""
        self.character = tvd.Character.random()
        self.players = [message.author]

    async def guess(self, message):
        char_name = tvd.Character.exists(message.content)
        if not char_name:
            return False
        
        char_name = tvd.Character.completeName(char_name)
        if not char_name:
            return False
        
        self.attempts += 1
        if message.author not in self.players:
            self.players.append(message.author)
        
        comparison = await self.respond(char_name)
        for field in comparison:
            match comparison[field]:
                case 0:
                    self.score += "🟥"
                case 0.5:
                    self.score += "🟨"
                case 1:
                    self.score += "🟩"
        else:
            self.score += "\n"

        correct = not any(value != 1 for value in comparison.values())
        if correct:
            end_time = time.time()
            duration = int( end_time - self.start_time)
            winner = message.author.name
            
            reply = f"{winner} is correct!\n{self.score}\
Guessed after {duration} seconds and {self.attempts} attempts"
            if self.attempts < 10:
                reply += " :)"
            elif self.attempts < 20:
                reply += " :["
            else:
                reply += "...."

            return reply

    async def respond(self, to_charname):
        guessed_char = tvd.getCharacters(name=to_charname)[0]
        comparison = self.character.compareTo(guessed_char)

        with open("temp/tvd_guess.png", 'rb') as image:
            await self.channel.send(file=discord.File(image, to_charname+'.png'))
            
        return comparison


tdle_games = []

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(
    name="ping",
    description="pong",
    # guild=discord.Object(id=GUILD_ID)
)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'pong (in {round(client.latency * 1000)}ms)')

@tree.command(
    name="help",
    description="displays help information"
)
@app_commands.describe(command = "about a specific command")
@app_commands.choices(command=[
    app_commands.Choice(name="teyvatdle", value="tdle"),
    app_commands.Choice(name="other", value="other"),
    ])
async def help(interaction: discord.Interaction, command: app_commands.Choice[str] | None):
    if command is None:
        help = """This is a silly little bot in development. It currently includes a Wordle-like character guessing game of Genshin Impact ("Teyvatdle")"""
    else:
        match command.value:
            case "tdle":
                help = Teyvatdle.help
            case "other":
                help = ":)"
    await interaction.response.send_message(help, ephemeral=True)


@client.event
async def on_ready():
    # await tree.sync(guild=discord.Object(id=GUILD_ID))
    await tree.sync()
    print("Logged on as", client.user)

@client.event
async def on_message(message):
    # don't respond to ourselves
    if message.author == client.user:
        return
    reply = False

    match message.content.lower():
        case 'teyvatdle' | 'tdle':
            reply = 'guess the character from Teyvat !'
            for tdle in tdle_games:
                if message.channel == tdle.channel:
                    if message.author in tdle.players:
                        reply = 'say "i give up" before guessing another character'
                    else:
                        reply += " (game already started in this channel)"
                    break
            else:
                tdle_games.append(Teyvatdle(message))

        case 'i give up' | 'igu':
            for tdle in tdle_games:
                if message.channel == tdle.channel and message.author in tdle.players:
                    await message.channel.send('lmao ok')
                    await tdle.respond(tdle.character.name)
                    del tdle_games[tdle_games.index(tdle)]
                    break

        case _:
            msg_args = message.content.lower().split()
            if "help" in msg_args:
                h = ["help"]
                if any(arg not in h for arg in msg_args):
                    if not any(arg not in h+["tdle","teyvatdle"] for arg in msg_args):
                        reply = Teyvatdle.help
            else:
                match message.content:  
                    case _:
                        for tdle in tdle_games:
                            if message.channel == tdle.channel:
                                reply = await tdle.guess(message)
                                if reply:
                                    await message.add_reaction('⭐')
                                    del tdle_games[tdle_games.index(tdle)]
                                break
    
    if reply:
        await message.channel.send(reply)


client.run(os.getenv('DISCORD_TOKEN'))
