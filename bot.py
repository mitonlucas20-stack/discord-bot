import discord
from discord.ext import commands
from discord.ui import View, Select, Button
import asyncio
import random
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="+", intents=intents)

# CONFIG
STAFF_ROLES = ["Fondateur", "Admin", "Modérateur"]
OWNER_IDS = [1246561259051028552]
LOG_CHANNEL = "logs"

warnings = {}

# -------- UTILS --------
def is_staff(member):
    return any(role.name in STAFF_ROLES for role in member.roles)

def is_owner(user):
    return user.id in OWNER_IDS

async def log(guild, msg):
    channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
    if channel:
        await channel.send(f"📜 {msg}")

# -------- TICKETS --------
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support", description="Aide"),
            discord.SelectOption(label="Paiement", description="Problème paiement"),
        ]
        super().__init__(placeholder="Choisis", options=options)

    async def callback(self, interaction):
        user = interaction.user
        guild = interaction.guild

        for c in guild.text_channels:
            if f"ticket-{user.id}" == c.name:
                return await interaction.response.send_message("❌ Ticket déjà ouvert", ephemeral=True)

        channel = await guild.create_text_channel(f"ticket-{user.id}")
        await channel.set_permissions(user, read_messages=True, send_messages=True)

        await channel.send(f"{user.mention}", view=CloseView())
        await interaction.response.send_message("✅ Ticket créé", ephemeral=True)

class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fermer", style=discord.ButtonStyle.red)
    async def close(self, interaction, button):
        if not is_staff(interaction.user):
            return await interaction.response.send_message("❌ Pas autorisé", ephemeral=True)

        messages = []
        async for m in interaction.channel.history(limit=200):
            messages.append(f"{m.author}: {m.content}")

        with open("transcript.txt", "w") as f:
            f.write("\n".join(messages))

        await log(interaction.guild, f"Ticket fermé: {interaction.channel.name}")
        await interaction.channel.delete()

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

@bot.command()
async def panel(ctx):
    await ctx.send("📦 Panel Support", view=TicketView())

# -------- MODERATION --------
@bot.command()
async def clear(ctx, amount: int):
    if not is_staff(ctx.author):
        return
    await ctx.channel.purge(limit=amount+1)

@bot.command()
async def kick(ctx, member: discord.Member):
    if not is_staff(ctx.author):
        return
    await member.kick()

@bot.command()
async def ban(ctx, member: discord.Member):
    if not is_staff(ctx.author):
        return
    await member.ban()

@bot.command()
async def unban(ctx, user_id: int):
    if not is_owner(ctx.author):
        return
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)

# -------- WARN --------
@bot.command()
async def warn(ctx, member: discord.Member, *, reason="Aucune"):
    if not is_staff(ctx.author):
        return

    warnings.setdefault(member.id, []).append(reason)
    await ctx.send(f"⚠️ {member} warn")

@bot.command()
async def casier(ctx, member: discord.Member):
    w = warnings.get(member.id, [])
    await ctx.send("\n".join(w) if w else "Aucun")

# -------- UTILS STAFF --------
@bot.command()
async def lock(ctx):
    if not is_staff(ctx.author):
        return
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)

@bot.command()
async def unlock(ctx):
    if not is_staff(ctx.author):
        return
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)

@bot.command()
async def say(ctx, *, msg):
    if not is_staff(ctx.author):
        return
    await ctx.message.delete()
    await ctx.send(msg)

@bot.command()
async def moveall(ctx):
    if not ctx.author.voice:
        return
    for m in ctx.guild.members:
        if m.voice:
            await m.move_to(ctx.author.voice.channel)

# -------- FUN --------
@bot.command()
async def pic(ctx, member: discord.Member=None):
    member = member or ctx.author
    await ctx.send(member.display_avatar.url)

@bot.command()
async def gstart(ctx, time: int, winners: int, *, prize):
    msg = await ctx.send(f"🎉 {prize}")
    await msg.add_reaction("🎉")

    await asyncio.sleep(time)

    msg = await ctx.channel.fetch_message(msg.id)
    users = [u async for u in msg.reactions[0].users() if not u.bot]

    winners = random.sample(users, min(len(users), winners))
    await ctx.send(f"Gagnant: {', '.join([u.mention for u in winners])}")

# -------- READY --------
@bot.event
async def on_ready():
    print("Bot prêt")
    bot.add_view(CloseView())

# -------- START --------
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
