import discord
from discord.ext import commands, tasks
import os
from flask import Flask
from threading import Thread
from werkzeug.serving import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware

# Setze die benötigten Intents
intents = discord.Intents.default()
intents.members = True  # Benötigt, um Mitgliederereignisse zu erhalten
intents.guilds = True   # Benötigt, um Guild-Events zu erhalten
intents.voice_states = True  # Benötigt für Sprachkanal-Events

# Erstellen eines Bots mit einem Präfix
bot = commands.Bot(command_prefix='!', intents=intents)

# Die IDs und Namen der Rollen mit Emojis
role_ids = {
    1112389246658019468: '🟢USK12',  # ID für USK12 mit grünem Kreis
    1112389279516196924: '🔵USK16',  # ID für USK16 mit blauem Kreis
    1112389305999048824: '🔴USK18',  # ID für USK18 mit rotem Kreis
}

# Die IDs der Channels, die überwacht werden sollen
voice_channel_ids = {1300967157001355284, 1162693974281166849, 1210956161424167012, 1162694071366725672, 1260168379709395006}

# Liste der Rollen in Prioritätsreihenfolge
role_priority = list(role_ids.keys())

# Funktion, die die niedrigste Rolle in einem Kanal bestimmt
def get_lowest_role_in_channel(channel):
    for role_id in role_priority:
        for member in channel.members:
            if discord.utils.get(member.roles, id=role_id):
                return role_ids[role_id]
    return None  # Falls keine der definierten Rollen im Kanal vertreten ist

# Event, das bei Änderungen des Sprachstatus eines Mitglieds ausgelöst wird
@bot.event
async def on_voice_state_update(member, before, after):
    # Falls der Kanal gewechselt wird oder das Mitglied den Kanal betritt/verlässt
    if before.channel != after.channel:
        # Kanäle, die überprüft werden müssen
        channels_to_check = []
        if after.channel and after.channel.id in voice_channel_ids:
            channels_to_check.append(after.channel)
        if before.channel and before.channel.id in voice_channel_ids:
            channels_to_check.append(before.channel)

        for channel in channels_to_check:
            await update_channel_name(channel)

# Funktion zur Aktualisierung des Kanalnamens
async def update_channel_name(channel):
    try:
        lowest_role = get_lowest_role_in_channel(channel)
        base_name = channel.name.split("-")[0]
        new_name = f'{base_name}-{lowest_role}' if lowest_role else base_name
        if channel.name != new_name:
            await channel.edit(name=new_name)
    except discord.DiscordException as e:
        print(f"Fehler beim Aktualisieren des Kanalnamens: {e}")

# Hintergrundaufgabe, die alle 10 Minuten die Sprachkanäle überprüft
@tasks.loop(minutes=10)
async def check_channels():
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            if channel.id in voice_channel_ids:
                await update_channel_name(channel)

# Startet die Hintergrundaufgabe, wenn der Bot bereit ist
@bot.event
async def on_ready():
    print(f'Bot ist eingeloggt als {bot.user}')
    check_channels.start()  # Startet die Hintergrundaufgabe

# Flask-Server für den Health Check
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"  # Einfacher Health-Check-Endpoint

# Funktion, um den Flask-Server im Hintergrund auszuführen
def run_flask():
    # Hier verwenden wir `run_simple` für den Produktionsbetrieb
    run_simple('0.0.0.0', 8080, app, use_reloader=False, use_debugger=False)

# Funktion, die den Flask-Server im Hintergrund ausführt
def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# Bot Token einfügen (sicher in einer Umgebungsvariablen speichern)
keep_alive()  # Flask-Server starten
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
