import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()  # Load env variables from .env

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Needed for member info and actions

bot = commands.Bot(command_prefix='!', intents=intents)

# Ready event
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is ready!")

# Kick command
@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    try:
        await member.kick(reason=reason)
        await ctx.send(f"✅ | Successfully kicked {member.display_name}")
    except Exception as e:
        await ctx.send(f"❌ | Failed to kick: {e}")

# Ban command
@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"✅ | Successfully banned {member.display_name}")
    except Exception as e:
        await ctx.send(f"❌ | Failed to ban: {e}")

# Give role
@bot.command(name='giverole')
@commands.has_permissions(manage_roles=True)
async def giverole(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.add_roles(role)
        await ctx.send(f"✅ | Role '{role.name}' given to {member.display_name}")
    except Exception as e:
        await ctx.send(f"❌ | Failed to give role: {e}")

# Take role
@bot.command(name='takerole')
@commands.has_permissions(manage_roles=True)
async def takerole(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.remove_roles(role)
        await ctx.send(f"✅ | Role '{role.name}' removed from {member.display_name}")
    except Exception as e:
        await ctx.send(f"❌ | Failed to remove role: {e}")

# Mute command (adds 'Muted' role for a duration)
@bot.command(name='mute')
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, time_in_seconds: int, *, reason=None):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not muted_role:
        return await ctx.send("❌ | No role named 'Muted' found. Please create one.")
    try:
        await member.add_roles(muted_role, reason=reason)
        await ctx.send(f"✅ | Muted {member.display_name} for {time_in_seconds} seconds.")
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.timedelta(seconds=time_in_seconds))
        await member.remove_roles(muted_role, reason="Mute time expired")
        await ctx.send(f"✅ | Unmuted {member.display_name} (mute expired).")
    except Exception as e:
        await ctx.send(f"❌ | Failed to mute: {e}")

# Announce command (bot sends a message in current channel)
@bot.command(name='announce')
@commands.has_permissions(manage_messages=True)
async def announce(ctx, *, message):
    try:
        await ctx.send(f"📢 Announcement:\n{message}")
    except Exception as e:
        await ctx.send(f"❌ | Failed to announce: {e}")

# Vanity command (prints server invite link endlessly)
@bot.command(name='vanity')
async def vanity(ctx):
    try:
        invites = await ctx.guild.invites()
        if not invites:
            await ctx.send("❌ | No invites found for this server.")
            return
        invite_link = invites[0].url  # Take first invite link
        # Send the invite repeatedly 5 times for demo (avoid infinite spam)
        for _ in range(5):
            await ctx.send(f"🔗 {invite_link}")
    except Exception as e:
        await ctx.send(f"❌ | Failed to get vanity link: {e}")

# Custom help command (disable default help)
bot.remove_command('help')

@bot.command(name='help')
async def help_command(ctx):
    help_text = """
**Available Commands:**

• `!kick @user [reason]` - Kick a user.
• `!ban @user [reason]` - Ban a user.
• `!giverole @user @role` - Give a role to a user.
• `!takerole @user @role` - Remove a role from a user.
• `!mute @user seconds [reason]` - Mute a user by adding 'Muted' role temporarily.
• `!announce [message]` - Make an announcement in this channel.
• `!vanity` - Display server invite link multiple times.
• `!help` - Show this help message.
"""
    await ctx.send(help_text)

# Run bot with token from environment variable
bot.run(os.getenv('BOT_TOKEN'))

