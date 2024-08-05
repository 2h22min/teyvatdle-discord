import os
import time
import discord
import teyvatdle as tvd

class Teyvatdle:
    def __init__(self):
        self.channel = None

    def start(self, message):
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
            self.channel = None
            self.end_time = time.time()
            winner = message.author.name
            reply = f"{winner} is correct!\n{self.score}\
Guessed after {int(self.end_time-self.start_time)} seconds and {self.attempts} attempts"
            if self.attempts < 10:
                reply += " :)"
            elif self.attempts < 20:
                reply += " :["
            else:
                reply += "........"

            return reply

    async def respond(self, to_charname):
        guessed_char = tvd.getCharacters(name=to_charname)[0]
        comparison = self.character.compareTo(guessed_char)

        with open("temp/tvd_guess.png", 'rb') as image:
            await self.channel.send(file=discord.File(image, to_charname+'.png'))
            
        return comparison


class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return
        reply = False

        match message.content.lower():
            case 'ping':
                reply = 'pong'
            case 'pong':
                reply = 'ping'

            case 'teyvatdle' | 'tdle':
                reply = 'guess the character from Teyvat !'
                if message.channel == tdle.channel:
                    if message.author in tdle.players:
                        reply = 'say "i give up" before guessing another character'
                else:
                    tdle.start(message)

            case 'i give up':
                if message.channel == tdle.channel and message.author in tdle.players:
                    await message.channel.send('lmao ok')
                    await tdle.respond(tdle.character.name)
                    tdle.channel = None

            case _:
                if message.channel == tdle.channel:
                    reply = await tdle.guess(message)
                    if reply:
                        await message.add_reaction('⭐')

        if reply:
            await message.channel.send(reply)

tdle = Teyvatdle()

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(os.getenv('DISCORD_TOKEN'))