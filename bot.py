import discord
from discord.ext import commands
from discord.ui import View, Select
import asyncio
import random
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="+", intents=intents)

STAFF_ROLES = ["Fondateur", "Admin", "Modérateur"]
LOG_CHANNEL = "logs"

def is_staff(member):
    return any(role.name in STAFF_ROLES for role in member.roles)

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

async def log(guild, message):
    channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
    if channel:
        await channel.send(f"📜 {message}")

# -------- COMMANDES --------

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong !")

@bot.command()
async def clear(ctx, amount: int):
    if not is_staff(ctx.author):
        return await ctx.send("❌ Permission refusée")
    await ctx.channel.purge(limit=amount)
    msg = await ctx.send(f"🧹 {amount} messages supprimés")
    await msg.delete(delay=3)

@bot.command()
async def addrole(ctx, member: discord.Member, role: discord.Role):
    if not is_staff(ctx.author):
        return await ctx.send("❌ Permission refusée")
    await member.add_roles(role)
    await ctx.send(f"✅ {role.name} ajouté à {member.mention}")

@bot.command()
async def removerole(ctx, member: discord.Member, role: discord.Role):
    if not is_staff(ctx.author):
        return await ctx.send("❌ Permission refusée")
    await member.remove_roles(role)
    await ctx.send(f"❌ {role.name} retiré à {member.mention}")

@bot.command()
async def moveall(ctx, channel: discord.VoiceChannel):
    if not is_staff(ctx.author):
        return await ctx.send("❌ Permission refusée")
    if not ctx.author.voice:
        return await ctx.send("❌ Tu dois être en vocal")
    source = ctx.author.voice.channel
    for member in source.members:
        await member.move_to(channel)
    await ctx.send(f"🔁 Tous déplacés vers {channel.name}")

@bot.command()
async def annonce(ctx, *, message):
    if not is_staff(ctx.author):
        return await ctx.send("❌ Permission refusée")
    await ctx.send(f"📢 @everyone\n{message}")

@bot.command()
async def roleping(ctx, role: discord.Role, *, message):
    if not is_staff(ctx.author):
        return await ctx.send("❌ Permission refusée")
    await ctx.send(f"{role.mention} {message}")

# -------- FUN --------

@bot.command()
async def ratio(ctx, member: discord.Member = None):
    member = member or ctx.author
    score = random.randint(0, 100)
    await ctx.send(f"📊 Ratio de {member.mention} : {score}%")

# -------- RUN --------

bot.run(os.getenv("TOKEN"))
