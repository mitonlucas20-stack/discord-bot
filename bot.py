import discord
from discord.ext import commands
from discord.ui import View, Select, Button
import asyncio
import random
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="+", intents=intents)

# -------- CONFIG --------
STAFF_ROLES = ["Fondateur", "Admin", "Responsable Boutique"]
OWNER_IDS = [1246561259051028552]
WHITELIST = [1246561259051028552]
LOG_CHANNEL = "logs"

PACKS = {
    "🛒 Achat Pack": "Achat boutique FiveM",
    "💳 Paiement": "Problème paiement",
    "❓ Support": "Besoin d'aide",
    "⚠️ Problème": "Bug / remboursement"
}

# -------- UTILS --------
def is_staff(member):
    return any(role.name in STAFF_ROLES for role in member.roles)

def is_owner(user):
    return user.id in OWNER_IDS

def is_whitelisted(user):
    return user.id in WHITELIST

async def send_log(guild, message):
    log_channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
    if log_channel:
        await log_channel.send(f"📜 {message}")

# -------- TICKET --------
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=label, description=desc)
            for label, desc in PACKS.items()
        ]
        super().__init__(placeholder="Fais un choix", options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        # Anti double ticket
        for channel in guild.text_channels:
            if f"ticket-{user.id}" == channel.name:
                return await interaction.response.send_message(
                    f"❌ Tu as déjà un ticket : {channel.mention}",
                    ephemeral=True
                )

        category = discord.utils.get(guild.categories, name=self.values[0])
        if not category:
            category = await guild.create_category(self.values[0])

        channel = await guild.create_text_channel(
            f"ticket-{user.id}",
            category=category
        )

        await channel.set_permissions(user, read_messages=True, send_messages=True)

        embed = discord.Embed(
            title="📦 Support",
            description="Un staff va te répondre.",
            color=0xff6600
        )

        await channel.send(user.mention, embed=embed, view=CloseView())
        await interaction.response.send_message("✅ Ticket créé", ephemeral=True)

# -------- CLOSE --------
class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fermer", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: Button):

        if not is_staff(interaction.user):
            return await interaction.response.send_message("❌ Pas autorisé", ephemeral=True)

        await interaction.response.send_message("🔒 Fermeture...", ephemeral=True)

        channel = interaction.channel

        try:
            messages = []
            async for msg in channel.history(limit=200):
                messages.append(f"{msg.author}: {msg.content}")

            with open("transcript.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(messages))

            log_channel = discord.utils.get(interaction.guild.text_channels, name=LOG_CHANNEL)
            if log_channel:
                await log_channel.send(
                    f"📄 Ticket fermé : {channel.name}",
                    file=discord.File("transcript.txt")
                )

            await asyncio.sleep(2)
            await channel.delete()

        except Exception as e:
            print(e)

# -------- PANEL --------
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

@bot.command()
async def panel(ctx):
    embed = discord.Embed(
        title="📦 Support PackZone",
        description="Choisis une catégorie ci-dessous.",
        color=0xff6600
    )
    await ctx.send(embed=embed, view=TicketView())

# -------- STAFF --------
@bot.command()
async def addfonda(ctx, member: discord.Member):
    if not is_whitelisted(ctx.author):
        return await ctx.send("❌ Accès refusé")

    role = discord.utils.get(ctx.guild.roles, name="Fondateur")
    if not role:
        role = await ctx.guild.create_role(name="Fondateur", permissions=discord.Permissions(administrator=True))

    await member.add_roles(role)
    await ctx.send(f"👑 {member.mention} promu Fondateur")
    await send_log(ctx.guild, f"{ctx.author} → Fondateur → {member}")

@bot.command()
async def recup(ctx):
    if ctx.author.id not in OWNER_IDS:
        return await ctx.send("❌ Accès refusé")

    role = discord.utils.get(ctx.guild.roles, name="Fondateur")
    if not role:
        role = await ctx.guild.create_role(name="Fondateur", permissions=discord.Permissions(administrator=True))

    await ctx.author.add_roles(role)
    await ctx.send("👑 Permissions récupérées")

# -------- FUN --------
@bot.command()
async def pic(ctx, member: discord.Member = None):
    member = member or ctx.author

    embed = discord.Embed(
        title=f"📸 {member}",
        color=0xff6600
    )
    embed.set_image(url=member.display_avatar.url)

    await ctx.send(embed=embed)

# -------- READY --------
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    bot.add_view(CloseView())

# -------- ANTI BUG --------
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

@bot.command()
async def addrole(ctx, member: discord.Member, *, role_name):
    if not is_staff(ctx.author):
        return await ctx.send("❌ Pas autorisé")

    role = discord.utils.get(ctx.guild.roles, name=role_name)

    if not role:
        return await ctx.send("❌ Rôle introuvable")

    await member.add_roles(role)
    await ctx.send(f"✅ {member.mention} a reçu le rôle **{role.name}**")

    await send_log(ctx.guild, f"{ctx.author} a donné {role.name} à {member}")

@bot.command()
async def bl(ctx, member: discord.Member, *, reason="Blacklist"):
    if not is_owner(ctx.author):
        return await ctx.send("❌ Accès réservé au fondateur")

    try:
        await member.ban(reason=reason)

        await ctx.send(f"⛔ {member} a été blacklist du serveur")
        await send_log(ctx.guild, f"{ctx.author} a blacklist {member} | Raison: {reason}")

    except Exception as e:
        await ctx.send("❌ Erreur lors du ban")
        print(e)

# -------- START --------
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ Token manquant")
else:
    bot.run(TOKEN)
