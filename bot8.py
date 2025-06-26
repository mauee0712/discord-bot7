import discord
from discord.ext import commands, tasks
import asyncio
import os
import random

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ----- Ban -----
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.mention} was banned. Reason: {reason if reason else 'No reason provided'}")

# ----- Unban -----
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    try:
        name, discriminator = member.split("#")
    except ValueError:
        await ctx.send("❌ Please provide full username with discriminator (e.g. User#1234).")
        return
    for ban_entry in banned_users:
        user = ban_entry.user
        if (user.name, user.discriminator) == (name, discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f"✅ Unbanned {user.mention}")
            return
    await ctx.send(f"❌ User {member} not found in ban list.")

# ----- Kick -----
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member.mention} was kicked. Reason: {reason if reason else 'No reason provided'}")

# ----- giverole -----
@bot.command()
@commands.has_permissions(manage_roles=True)
async def giverole(ctx, member: discord.Member, *, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(f"✅ {member.mention} has been given the role **{role.name}**.")

# ----- takerole -----
@bot.command()
@commands.has_permissions(manage_roles=True)
async def takerole(ctx, member: discord.Member, *, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send(f"✅ {member.mention} has had the role **{role.name}** removed.")

# ----- mute -----
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, seconds: int = None, *, reason=None):
    muted_role = discord.utils.get(ctx.guild.roles, name="muted")
    if not muted_role:
        muted_role = await ctx.guild.create_role(name="muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, speak=False, send_messages=False, read_message_history=True, read_messages=False)
    await member.add_roles(muted_role, reason=reason)
    if seconds:
        await ctx.send(f"🔇 {member.mention} has been muted for {seconds} seconds.")
        await asyncio.sleep(seconds)
        await member.remove_roles(muted_role)
        await ctx.send(f"🔈 {member.mention} has been unmuted.")
    else:
        await ctx.send(f"🔇 {member.mention} has been muted.")

# ----- unmute -----
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    muted_role = discord.utils.get(ctx.guild.roles, name="muted")
    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(f"🔈 {member.mention} has been unmuted.")
    else:
        await ctx.send(f"❌ {member.mention} is not muted.")

# ----- announce -----
@bot.command()
@commands.has_permissions(administrator=True)
async def announce(ctx, channel: discord.TextChannel, *, message):
    await channel.send(f"📢 Announcement:\n{message}")
    await ctx.send("✅ Announcement sent.")

# ----- vanity (nickname change) -----
@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def vanity(ctx, member: discord.Member, *, nickname):
    await member.edit(nick=nickname)
    await ctx.send(f"✏️ {member.mention}'s nickname changed to **{nickname}**.")

# ----- warn and warnings storage -----
warnings = {}

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    user_id = str(member.id)
    warnings[user_id] = warnings.get(user_id, 0) + 1
    await ctx.send(f"⚠️ {member.mention} has been warned. Reason: {reason if reason else 'No reason provided'}. Total warnings: {warnings[user_id]}")

@bot.command()
async def warnings(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = str(member.id)
    count = warnings.get(user_id, 0)
    await ctx.send(f"⚠️ {member.mention} has {count} warning(s).")

# ----- roles list -----
@bot.command()
async def roles(ctx):
    roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
    roles_list = ", ".join(roles)
    await ctx.send(f"📋 Roles in this server:\n{roles_list}")

# ----- giveaway -----
@bot.command()
@commands.has_permissions(manage_guild=True)
async def giveaway(ctx, seconds: int, *, prize):
    embed = discord.Embed(title="🎉 Giveaway!", description=f"Prize: {prize}\nTime: {seconds} seconds", color=0x00ff00)
    giveaway_message = await ctx.send(embed=embed)
    await giveaway_message.add_reaction("🎉")

    await asyncio.sleep(seconds)

    message = await ctx.channel.fetch_message(giveaway_message.id)
    users = set()
    for reaction in message.reactions:
        if str(reaction.emoji) == "🎉":
            async for user in reaction.users():
                if not user.bot:
                    users.add(user)
    if users:
        winner = random.choice(list(users))
        await ctx.send(f"🎉 Congratulations {winner.mention}! You won **{prize}**!")
    else:
        await ctx.send("No valid entries, giveaway cancelled.")

# ----- custom help command -----
@bot.command()
async def help(ctx):
    help_text = """
