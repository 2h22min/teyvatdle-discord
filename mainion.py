import os
import time
import discord
from discord import app_commands
import teyvatdle as tvd

GUILD_ID = os.getenv('GUILD_ID') # debugging server id

class Teyvatdle:
    games = []

    start_reply = 'guess the character from Teyvat !'

    help = """Guess a character from Teyvat (Genshin Impact) by typing their names!\
            \nThe characteristics of each guess will be colored like this:\
            \n> 🟩 GREEN squares = correct characteristics (in common)
                > 🟨 YELLOW squares = "close" characteristics
                > 🟥 RED squares = incorrect characteristics"""

    @staticmethod
    async def command(com, type = 0, **options):
        """Handle potential commands related to the game,
        checking the channel and user who sent it.
        
        Args:
            com (Union[Interaction, Message]): The potential command.
            type (int, optional): The type of potential command:\
                0 (start game) | 1 (guess attempt) | 2 (give up/force end) | \
                3 (turn off endless mode).
            
        Returns:
            The bot's reply `str` if any, False otherwise.
        """

        channel = com.channel
        if isinstance(com, discord.interactions.Interaction):
            user = com.user
        else:
            user = com.author

        if type:
            reply = False
        else:
            reply = Teyvatdle.start_reply

        ingame_replies = {
            # Default replies when a game is already active in the channel.
            # `False` keys for users that aren't players yet and viceversa.
            0: {False: Teyvatdle.start_reply + ' (game already started in this channel)',
                True: 'say "i give up" before guessing another character'},

            1: {False: False,
                True: False},

            2: {False: "don't give up without even trying!",
                True: False},

            3: {False: False,
                True: "> -# **endless mode turned off**"},

            }
        for tdle in Teyvatdle.games:
            if channel != tdle.channel:
                continue

            reply = ingame_replies[type][user in tdle.players]

            end_game = False
            if type == 1:
                # If potential guess attempt
                reply = await tdle.guess(com)
                if reply:
                    await com.add_reaction('⭐')
                    await channel.send(reply)
                    reply = False
                    end_game = True

            elif type == 2 and user in tdle.players:
                await channel.send('lmao ok')
                await tdle.respond(tdle.character.name)
                end_game = True

            elif type == 3:
                if not tdle.endless:
                    reply = False
                elif user in tdle.players:
                    tdle.endless = False
            
            if end_game:
                if tdle.endless:
                    # Start next game if it was "endless"
                    Teyvatdle.games.append(Teyvatdle(channel, user, True))
                    await channel.send('> -# *Send "stop" to turn off endless mode*')
                    reply = Teyvatdle.start_reply
                Teyvatdle.games.remove(tdle)
            break

        else: # When no game is active in the context channel
            if type == 0: # Start new game
                endless = False
                try:
                    endless = bool(options["endless"].value)
                except (KeyError, AttributeError):
                    pass
                Teyvatdle.games.append(Teyvatdle(channel, user, endless))
                
        return reply

    def __init__(self, channel, user, endless: bool = False):
        self.channel = channel
        self.endless = endless
        self.start_time = time.time()
        self.attempts = 0
        self.score = ""
        self.character = tvd.Character.random()
        self.players = [user]

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
            
            reply = f"{winner} is correct!\n{self.score[-140:]}\
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


class Games:
    active = {
        "tdle": Teyvatdle.games,
    }

    async def off_endless(com):
        """Turn off endless mode for current game in the channel.
        
        Args:
            com (Union[Interaction, Message]): The "stop" command.
        """
        for games in Games.active:
            for game in Games.active[games]:
                if game.channel != com.channel:
                    continue
                
                reply = await game.command(com, 3)
                try:
                    await com.response.send_message(reply)
                except AttributeError:
                    return reply
                return False


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

@tree.command(
    name="teyvatdle",
    description="start a teyvatdle game",
)
@app_commands.describe(endless = "and a new one automatically after each ends")
@app_commands.describe(thread = "inside a new thread")
@app_commands.choices(endless=[app_commands.Choice(name="True", value="1"),
                              app_commands.Choice(name="False", value=""),
                            ])
@app_commands.choices(thread=[app_commands.Choice(name="True", value="1"),
                              app_commands.Choice(name="False", value=""),
                            ])
async def tdle(interaction: discord.Interaction, endless: app_commands.Choice[str] | None, thread: app_commands.Choice[str] | None):
    await interaction.response.send_message(
        await Teyvatdle.command(interaction, endless=endless)
    )
    try:
        msg = await interaction.original_response()
        if bool(thread.value) and msg.content == Teyvatdle.start_reply:
            new_channel = await interaction.channel.create_thread(
                name="teyvatdle",
                message=msg,
                type=discord.ChannelType.public_thread,
                reason="for a Teyvatdle game"
            )
            Teyvatdle.games[-1].channel = new_channel
    except AttributeError:
        pass

@tree.command(
    name="stop",
    description="turn off endless mode for current game",
)
async def stop(interaction: discord.Interaction):
    await Games.off_endless(interaction)


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
            reply = await Teyvatdle.command(message)

        case 'i give up' | 'igu':
            reply = await Teyvatdle.command(message, 2)

        case 'stop':
            reply = await Games.off_endless(message)

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
                        reply = await Teyvatdle.command(message, 1)
    
    if reply:
        await message.channel.send(reply)


client.run(os.getenv('DISCORD_TOKEN'))
