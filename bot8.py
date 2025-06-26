import discord
from discord.ext import commands, tasks
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# In-memory warning storage {guild_id: {user_id: warn_count}}
warnings = {}

def format_box(text):
    return f"```yaml\n{text}\n```"

# --- Ban command ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.ban(reason=reason)
        await ctx.send(format_box(f"✅ {member} has been banned.\nReason: {reason or 'No reason provided.'}"))
    except Exception as e:
        await ctx.send(format_box(f"❌ Failed to ban {member}.\nError: {e}"))

# --- Unban command ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')
    for ban_entry in banned_users:
        user = ban_entry.user
        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(format_box(f"✅ {user} has been unbanned."))
            return
    await ctx.send(format_box(f"❌ User {member} not found in banned list."))

# --- Kick command ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    try:
        await member.kick(reason=reason)
        await ctx.send(format_box(f"✅ {member} has been kicked.\nReason: {reason or 'No reason provided.'}"))
    except Exception as e:
        await ctx.send(format_box(f"❌ Failed to kick {member}.\nError: {e}"))

# --- Role Give ---
@bot.command(aliases=['rolegive'])
@commands.has_permissions(manage_roles=True)
async def give_role(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.add_roles(role)
        await ctx.send(format_box(f"✅ Given role **{role.name}** to {member}."))
    except Exception as e:
        await ctx.send(format_box(f"❌ Could not give role.\nError: {e}"))

# --- Role Take ---
@bot.command(aliases=['roletake'])
@commands.has_permissions(manage_roles=True)
async def take_role(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.remove_roles(role)
        await ctx.send(format_box(f"✅ Removed role **{role.name}** from {member}."))
    except Exception as e:
        await ctx.send(format_box(f"❌ Could not remove role.\nError: {e}"))

# --- Mute command with timed mute ---
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, time: int = 0, *, reason=None):
    muted_role = discord.utils.get(ctx.guild.roles, name="muted")
    if not muted_role:
        # Create muted role if not exists
        muted_role = await ctx.guild.create_role(name="muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, speak=False, send_messages=False, read_message_history=True, read_messages=False)
    try:
        await member.add_roles(muted_role, reason=reason)
        if time > 0:
            await ctx.send(format_box(f"🔇 {member} muted for {time} seconds.\nReason: {reason or 'No reason provided.'}"))
            await asyncio.sleep(time)
            if muted_role in member.roles:
                await member.remove_roles(muted_role)
                await ctx.send(format_box(f"🔈 {member} has been unmuted after {time} seconds."))
        else:
            await ctx.send(format_box(f"🔇 {member} has been muted indefinitely.\nReason: {reason or 'No reason provided.'}"))
    except Exception as e:
        await ctx.send(format_box(f"❌ Failed to mute.\nError: {e}"))

# --- Unmute ---
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    muted_role = discord.utils.get(ctx.guild.roles, name="muted")
    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(format_box(f"🔈 {member} has been unmuted."))
    else:
        await ctx.send(format_box(f"❌ {member} is not muted."))

# --- Announce ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def announce(ctx, channel: discord.TextChannel, *, message):
    try:
        await channel.send(message)
        await ctx.send(format_box(f"📢 Announcement sent to {channel.mention}."))
    except Exception as e:
        await ctx.send(format_box(f"❌ Failed to send announcement.\nError: {e}"))

# --- Vanity (Nickname) ---
@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def vanity(ctx, member: discord.Member, *, nickname):
    try:
        await member.edit(nick=nickname)
        await ctx.send(format_box(f"✏️ Changed nickname of {member} to **{nickname}**."))
    except Exception as e:
        await ctx.send(format_box(f"❌ Could not change nickname.\nError: {e}"))

# --- Warn command ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    guild_id = ctx.guild.id
    user_id = member.id
    if guild_id not in warnings:
        warnings[guild_id] = {}
    warnings[guild_id][user_id] = warnings[guild_id].get(user_id, 0) + 1
    await ctx.send(format_box(f"⚠️ {member} has been warned.\nReason: {reason or 'No reason provided.'}\nTotal warnings: {warnings[guild_id][user_id]}"))

# --- Warnings count ---
@bot.command()
async def warnings(ctx, member: discord.Member = None):
    member = member or ctx.author
    guild_id = ctx.guild.id
    user_id = member.id
    count = warnings.get(guild_id, {}).get(user_id, 0)
    await ctx.send(format_box(f"📋 {member} has {count} warning(s)."))

# --- Roles list ---
@bot.command()
async def roles(ctx):
    roles_list = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
    roles_text = '\n'.join(roles_list) if roles_list else "No roles found."
    await ctx.send(format_box(f"🎭 Roles in this server:\n{roles_text}"))

# --- Giveaway (simple) ---
import random
@bot.command()
@commands.has_permissions(manage_messages=True)
async def giveaway(ctx, time: int, *, prize):
    await ctx.send(format_box(f"🎉 Giveaway started for: **{prize}**\nDuration: {time} seconds. React with 🎉 to enter!"))
    giveaway_message = await ctx.send(f"🎉 **Giveaway:** {prize}\nReact with 🎉 to enter!")
    await giveaway_message.add_reaction("🎉")
    
    await asyncio.sleep(time)
    
    new_msg = await ctx.channel.fetch_message(giveaway_message.id)
    users = set()
    for reaction in new_msg.reactions:
        if reaction.emoji == "🎉":
            async for user in reaction.users():
                if user != bot.user:
                    users.add(user)
    if users:
        winner = random.choice(list(users))
        await ctx.send(format_box(f"🏆 Congratulations {winner.mention}! You won **{prize}**!"))
    else:
        await ctx.send(format_box("😕 No one participated in the giveaway."))

# --- Custom help command ---
@bot.command()
async def help(ctx):
    help_text = """
**Available Commands:**

• `!ban <member> [reason]` - Ban a member.
• `!unban <user#1234>` - Unban a user.
• `!kick <member> [reason]` - Kick a member.
• `!give_role <member> <role>` - Give role to member.
• `!take_role <member> <role>` - Remove role from member.
• `!mute <member> [seconds] [reason]` - Mute a member with 'muted' role.
• `!unmute <member>` - Unmute a member.
• `!announce <#channel> <message>` - Send announcement.
• `!vanity <member> <nickname>` - Change nickname.
• `!warn <member> [reason]` - Warn a member.
• `!warnings [member]` - Show warnings count.
• `!roles` - List all roles.
• `!giveaway <seconds> <prize>` - Start a giveaway.

Use commands responsibly!
"""
    await ctx.send(format_box(help_text))

# Run your bot
import os

bot.run(os.getenv("BOT_TOKEN"))

