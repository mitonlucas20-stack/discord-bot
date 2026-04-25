import discord
from discord.ext import commands
from discord.ui import View, Select, Button
import asyncio
import random
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="+", intents=intents)

STAFF_ROLES = ["Fondateur", "Admin", "Responsable Boutique"]
LOG_CHANNEL = "logs"

PACKS = {
    "🛒 Achat Pack": "Achat boutique FiveM",
    "💳 Paiement": "Problème paiement",
    "❓ Support": "Besoin d'aide",
    "⚠️ Problème": "Bug / remboursement"
}

def is_staff(member):
    return any(role.name in STAFF_ROLES for role in member.roles)

# -------- PANEL MENU --------
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=label, description=desc)
            for label, desc in PACKS.items()
        ]
        super().__init__(placeholder="Fais un choix", options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        choice = self.values[0]

        # Anti double ticket
        for channel in guild.text_channels:
            if interaction.user.name in channel.name:
                return await interaction.response.send_message(
                    f"❌ Tu as déjà un ticket : {channel.mention}",
                    ephemeral=True
                )

        category = discord.utils.get(guild.categories, name=choice)
        if not category:
            category = await guild.create_category(choice)

        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.name}",
            category=category
        )

        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)

        embed = discord.Embed(
            title="📦 PackZone Ticket",
            description=f"Catégorie : **{choice}**\nUn staff va te répondre.",
            color=0xff0000
        )

        await channel.send(
            content=interaction.user.mention,
            embed=embed,
            view=CloseView()
        )

        await interaction.response.send_message(
            f"✅ Ticket créé : {channel.mention}",
            ephemeral=True
        )

# -------- BOUTON FERMER --------
class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fermer", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: Button):
        if not is_staff(interaction.user):
            return await interaction.response.send_message("❌ Pas autorisé", ephemeral=True)

        channel = interaction.channel

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

        await channel.delete()

# -------- COMMANDES STAFF --------
@bot.command()
async def rename(ctx, *, name: str):
    if not is_staff(ctx.author):
        return await ctx.send("❌ Pas autorisé")
    await ctx.channel.edit(name=name)
    await ctx.send(f"✏️ Rename → {name}")

@bot.command()
async def add(ctx, member: discord.Member):
    if not is_staff(ctx.author):
        return await ctx.send("❌ Pas autorisé")
    await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
    await ctx.send(f"➕ {member.mention} ajouté au ticket")

@bot.command()
async def remove(ctx, member: discord.Member):
    if not is_staff(ctx.author):
        return await ctx.send("❌ Pas autorisé")
    await ctx.channel.set_permissions(member, overwrite=None)
    await ctx.send(f"➖ {member.mention} retiré du ticket")

@bot.command()
async def claim(ctx):
    if not is_staff(ctx.author):
        return await ctx.send("❌ Pas autorisé")
    await ctx.send(f"📌 Ticket pris en charge par {ctx.author.mention}")

# -------- ANNONCE --------
@bot.command()
async def annonce(ctx, *, message: str):
    if not is_staff(ctx.author):
        return await ctx.send("❌ Pas autorisé")

    embed = discord.Embed(
        title="📢 PackZone - Annonce",
        description=message,
        color=0xff0000
    )

    embed.set_footer(text=f"Annonce par {ctx.author}")
    await ctx.send("@everyone", embed=embed)

# -------- GIVEAWAY --------
@bot.command()
async def giveaway(ctx, duration: int, winners: int, *, prize: str):
    if not is_staff(ctx.author):
        return await ctx.send("❌ Pas autorisé")

    embed = discord.Embed(
        title="🎉 GIVEAWAY PACKZONE",
        description=(
            f"🎁 **Prix :** {prize}\n"
            f"👑 **Gagnants :** {winners}\n"
            f"⏳ **Durée :** {duration} secondes\n\n"
            "👉 Réagis avec 🎉 pour participer !"
        ),
        color=0xff0000
    )

    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🎉")

    await asyncio.sleep(duration)

    msg = await ctx.channel.fetch_message(msg.id)

    users = []
    for reaction in msg.reactions:
        if str(reaction.emoji) == "🎉":
            async for user in reaction.users():
                if not user.bot:
                    users.append(user)

    if len(users) == 0:
        return await ctx.send("❌ Aucun participant")

    winners_list = random.sample(users, min(winners, len(users)))
    winner_mentions = ", ".join([user.mention for user in winners_list])

    await ctx.send(f"🎉 Félicitations {winner_mentions} ! Tu as gagné **{prize}**")

# -------- PANEL --------
@bot.command()
async def panel(ctx):
    embed = discord.Embed(
        title="📦 PackZone - Support",
        description=(
            "Bienvenue dans **PackZone** 🛒\n\n"
            "Choisis une catégorie ci-dessous.\n\n"
            "• Sois précis\n"
            "• Respect obligatoire\n"
            "• Réponse rapide\n\n"
            "PackZone 🔴"
        ),
        color=0xff0000
    )

    await ctx.send(embed=embed, view=TicketView())

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# -------- READY --------
@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    bot.add_view(CloseView())  # 🔥 garde les boutons actifs après restart

@bot.command()
async def pic(ctx, member: discord.Member = None):
    member = member or ctx.author

    embed = discord.Embed(
        title=f"📸 Profil de {member}",
        description=f"🆔 ID : `{member.id}`",
        color=0xff0000
    )

    embed.set_image(url=member.display_avatar.url)
    embed.set_footer(text="PackZone 🔴")

    await ctx.send(embed=embed)

# 🔐 TOKEN sécurisé (Render)
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    print("❌ Token manquant")
else:
    bot.run(TOKEN)