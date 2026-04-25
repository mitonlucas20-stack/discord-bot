# -------- CONFIG --------
OWNER_IDS = [123456789012345678]  # 🔥 TON ID DISCORD ICI
WHITELIST = [123456789012345678]  # personnes autorisées bot
LOG_CHANNEL = "logs"

def is_owner(user):
    return user.id in OWNER_IDS

def is_whitelisted(user):
    return user.id in WHITELIST

def is_staff(member):
    return any(role.name in STAFF_ROLES for role in member.roles)

# -------- LOG --------
async def send_log(guild, message):
    log_channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
    if log_channel:
        embed = discord.Embed(
            title="📜 Staff Log",
            description=message,
            color=0xff6600
        )
        await log_channel.send(embed=embed)

# -------- ADD FONDATEUR --------
@bot.command()
async def addfonda(ctx, member: discord.Member):
    if not is_whitelisted(ctx.author):
        return await ctx.send("❌ Accès refusé (whitelist)")

    role = discord.utils.get(ctx.guild.roles, name="Fondateur")

    if role is None:
        return await ctx.send("❌ Rôle Fondateur introuvable")

    await member.add_roles(role)

    embed = discord.Embed(
        title="👑 Promotion",
        description=f"{member.mention} est maintenant **Fondateur**",
        color=0xff0000
    )
    embed.set_footer(text=f"Action par {ctx.author}")

    await ctx.send(embed=embed)
    await send_log(ctx.guild, f"{ctx.author} a promu {member} en Fondateur")

# -------- REMOVE FONDATEUR --------
@bot.command()
async def removefonda(ctx, member: discord.Member):
    if not is_whitelisted(ctx.author):
        return await ctx.send("❌ Accès refusé (whitelist)")

    role = discord.utils.get(ctx.guild.roles, name="Fondateur")

    if role is None:
        return await ctx.send("❌ Rôle Fondateur introuvable")

    await member.remove_roles(role)

    embed = discord.Embed(
        title="❌ Rétrogradation",
        description=f"{member.mention} n'est plus **Fondateur**",
        color=0xff0000
    )

    await ctx.send(embed=embed)
    await send_log(ctx.guild, f"{ctx.author} a retiré Fondateur à {member}")

# -------- AJOUT WHITELIST --------
@bot.command()
async def whitelist(ctx, member: discord.Member):
    if not is_owner(ctx.author):
        return await ctx.send("❌ Seul le fondateur bot peut faire ça")

    if member.id not in WHITELIST:
        WHITELIST.append(member.id)

    await ctx.send(f"✅ {member.mention} ajouté à la whitelist")

# -------- REMOVE WHITELIST --------
@bot.command()
async def unwhitelist(ctx, member: discord.Member):
    if not is_owner(ctx.author):
        return await ctx.send("❌ Seul le fondateur bot peut faire ça")

    if member.id in WHITELIST:
        WHITELIST.remove(member.id)

    await ctx.send(f"❌ {member.mention} retiré de la whitelist")
