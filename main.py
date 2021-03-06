import asyncio
import discord
import atexit
import os
TOKEN = os.environ['PBT']
client = discord.Client()
command_prefix = "!g "


class User:
    def __init__(self, discord_id):
        self.discord_id = discord_id
        self.bladder_amount_max = 5
        self.bladder_amount_current = 0
        self.holding_time_max = 300
        self.holding_time_current = 0

    def load_from_disk(self):
        file_handle = open("Saves/" + str(self.discord_id) + ".txt", "r")
        self.bladder_amount_max = float(file_handle.readline())
        self.bladder_amount_current = float(file_handle.readline())
        self.holding_time_max = float(file_handle.readline())
        self.holding_time_current = float(file_handle.readline())
        file_handle.close()

    def save_to_disk(self):
        file_handle = open("Saves/" + str(self.discord_id) + ".txt", "w")
        file_handle.write(str(self.bladder_amount_max) + "\n")
        file_handle.write(str(self.bladder_amount_current) + "\n")
        file_handle.write(str(self.holding_time_max) + "\n")
        file_handle.write(str(self.holding_time_current) + "\n")
        file_handle.close()

    def drink(self, amount):
        self.bladder_amount_current += amount / 1000
        self.holding_time_current += 10 / 1000

    def piss(self):
        self.bladder_amount_max += self.bladder_amount_current / 10
        self.bladder_amount_current = 0
        self.holding_time_max += self.holding_time_current / 10
        self.holding_time_current = 0


People = {}


def is_mention(mention):
    return mention.startswith("<@") and mention.endswith(">") and mention[3:len(mention) - 1].isnumeric()


async def handle_overflow(channel, person):
    person.piss()
    await channel.send("<@" + str(person.discord_id) + "> just pissed themself")


async def swell_bladder(channel, person):
    while person.bladder_amount_current > 0:
        await asyncio.sleep(1)
        person.holding_time_current = int(person.holding_time_current) + 1
        if person.holding_time_current > person.holding_time_max and person.bladder_amount_current > 0:
            await handle_overflow(channel, person)


async def handle_drink_cmd(message, params):
    try:
        person = People[message.author.id]
        amount = float(params[1].rstrip("ml"))
        person.drink(amount)
        await message.channel.send("You drank " + str(amount) + "ml of water")
        if person.bladder_amount_current > person.bladder_amount_max:
            await handle_overflow(message.channel, person)
        else:
            client.loop.create_task(swell_bladder(message.channel, person))
    except (IndexError, TypeError, ValueError):
        await message.channel.send("Please use like this \n > drink [amount in ml]")


async def handle_piss_cmd(message):
    person = People[message.author.id]
    if person.bladder_amount_current >= person.bladder_amount_max * 0.5:
        person.piss()
        await message.channel.send("<@" + str(person.discord_id) + "> just pissed")
    else:
        await message.channel.send("You did not drink enough to piss")


async def handle_piss_at_cmd(message, params):
    person = People[message.author.id]
    if person.bladder_amount_current >= person.bladder_amount_max * 0.5:
        person.piss()
        if is_mention(params[1]) and params[1] != "<@" + str(person.discord_id) + ">":
            await message.channel.send("<@" + str(person.discord_id) + "> just pissed on you, " + params[1].lstrip(" ").rstrip(" "))
        else:
            await message.channel.send("<@" + str(person.discord_id) + "> just pissed themself")
    else:
        await message.channel.send("You did not drink enough to piss")


async def handle_command(message):
    command = message.content.lower()[len(command_prefix):]
    params = command.split(" ")
    if (params[0] == "drink" or params[0] == "piss" or params[0] == "piss_at") and message.author.id not in People.keys():
        People[message.author.id] = User(message.author.id)
    if params[0] == "drink":
        await handle_drink_cmd(message, params)
    elif params[0] == "piss":
        if len(params) > 1:
            await handle_piss_at_cmd(message, params)
        else:
            await handle_piss_cmd(message)


@client.event
async def on_message(message):
    if not message.author.bot and message.content.startswith(command_prefix):
        await handle_command(message)


@client.event
async def on_ready():
    print("Pissbot Online!")


def init_handler():
    if os.path.exists("Saves/"):
        print("Loading save files...")
        save_files = os.listdir("Saves/")
        for save_file in save_files:
            if not save_file.startswith(".") and save_file.endswith(".txt"):
                user_id = save_file[0:len(save_file) - 4]
                print("Loading data for user", user_id)
                person = User(user_id)
                person.load_from_disk()
                People[user_id] = person
        print("Loaded save files")
    else:
        print("First time run? Creating Saves directory...")
        os.makedirs("Saves")
        print("Saves directory created")


def exit_handler():
    print("Stopping Pissbot...")
    client.loop.stop()
    print("Saving data...")
    for person in People.values():
        print("Saving data for user", person.discord_id)
        person.save_to_disk()
    print("Pissbot stopped")


print("Starting Pissbot...")
init_handler()
atexit.register(exit_handler)
client.run(TOKEN)