import discord
from discord.ext import commands
from discord import app_commands
import time
import platform
import psutil
import os

class General(commands.Cog):
    """General commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
    
    @commands.hybrid_command(name='ping')
    async def ping(self, ctx):
        """Check bot latency"""
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: {round(self.bot.latency * 1000)}ms",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='hello', aliases=['hi', 'hey'])
    async def hello(self, ctx):
        """Say hello to the bot"""
        embed = discord.Embed(
            title="👋 Hello!",
            description=f"Hello {ctx.author.mention}! I'm here to help moderate your server.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='help')
    @app_commands.describe(command_name="Name of the command to get help for")
    async def help_command(self, ctx, command_name: str = None):
        """Custom help command"""
        prefix = os.getenv('COMMAND_PREFIX', '!')
        
        if command_name:
            # Show help for specific command
            command = self.bot.get_command(command_name)
            if command:
                embed = discord.Embed(
                    title=f"Help: {prefix}{command.name}",
                    description=command.help or "No description available",
                    color=discord.Color.blue()
                )
                if command.aliases:
                    embed.add_field(
                        name="Aliases",
                        value=", ".join([f"`{prefix}{alias}`" for alias in command.aliases]),
                        inline=False
                    )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Command Not Found",
                    description=f"No command named `{command_name}` found.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
        else:
            # Show general help
            embed = discord.Embed(
                title="🤖 Bot Help",
                description=f"Here are all available commands. Use `{prefix}help <command>` for detailed help.",
                color=discord.Color.blue()
            )
            
            # General commands
            general_commands = [
                f"`{prefix}ping` - Check bot latency",
                f"`{prefix}hello` - Say hello to the bot",
                f"`{prefix}info` - Show bot information",
                f"`{prefix}uptime` - Show bot uptime"
            ]
            embed.add_field(
                name="📋 General Commands",
                value="\n".join(general_commands),
                inline=False
            )
            
            # Moderation commands
            mod_commands = [
                f"`{prefix}kick <user> [reason]` - Kick a user",
                f"`{prefix}ban <user> [reason]` - Ban a user",
                f"`{prefix}unban <user>` - Unban a user",
                f"`{prefix}mute <user> [reason]` - Mute a user",
                f"`{prefix}unmute <user>` - Unmute a user"
            ]
            embed.add_field(
                name="🔨 Moderation Commands",
                value="\n".join(mod_commands),
                inline=False
            )
            
            # Mass DM commands
            mass_dm_commands = [
                f"`{prefix}massdm <message>` - Send DM to all members",
                f"`{prefix}massdmrole <role> <message>` - Send DM to role members"
            ]
            embed.add_field(
                name="📨 Mass DM Commands",
                value="\n".join(mass_dm_commands),
                inline=False
            )
            
            # Giveaway commands
            giveaway_commands = [
                f"`{prefix}gstart <duration> <winners> <prize>` - Start a giveaway",
                f"`{prefix}gend <message_id>` - End a giveaway early",
                f"`{prefix}greroll <message_id>` - Reroll giveaway winners",
                f"`{prefix}glist` - List active giveaways"
            ]
            embed.add_field(
                name="🎉 Giveaway Commands",
                value="\n".join(giveaway_commands),
                inline=False
            )
            
            # Spin Wheel commands
            wheel_commands = [
                f"`{prefix}wheeladd @users` - Add users to spin wheel",
                f"`{prefix}wheelremove @users` - Remove users from wheel",
                f"`{prefix}wheellist` - Show all users in wheel",
                f"`{prefix}spin` - Spin the wheel and select winner!",
                f"`{prefix}wheelclear` - Clear all users from wheel"
            ]
            embed.add_field(
                name="🎯 Spin Wheel Commands",
                value="\n".join(wheel_commands),
                inline=False
            )
            
            # Warning commands
            warning_commands = [
                f"`{prefix}warn @user [reason]` - Warn a user",
                f"`{prefix}unwarn @user <id>` - Remove specific warning",
                f"`{prefix}warnings [@user]` - Check warnings",
                f"`{prefix}clearwarnings @user` - Clear all warnings"
            ]
            embed.add_field(
                name="⚠️ Warning Commands",
                value="\n".join(warning_commands),
                inline=False
            )
            
            # AFK commands
            afk_commands = [
                f"`{prefix}afk [reason]` - Set yourself as AFK",
                f"`{prefix}unafk` - Remove AFK status",
                f"`{prefix}afklist` - List all AFK users"
            ]
            embed.add_field(
                name="😴 AFK Commands",
                value="\n".join(afk_commands),
                inline=False
            )
            
            # Role commands
            role_commands = [
                f"`{prefix}addrole @user @role` - Add role to user",
                f"`{prefix}removerole @user @role` - Remove role from user",
                f"`{prefix}massrole @role add/remove target` - Mass role management"
            ]
            embed.add_field(
                name="🎭 Role Commands",
                value="\n".join(role_commands),
                inline=False
            )
            
            # Settings commands
            settings_commands = [
                f"`{prefix}setprefix <new_prefix>` - Change command prefix",
                f"`{prefix}prefix` - Show current prefix"
            ]
            embed.add_field(
                name="⚙️ Settings Commands",
                value="\n".join(settings_commands),
                inline=False
            )
            
            embed.add_field(
                name="💡 Slash Commands",
                value="All commands also work as slash commands! Type `/` to see them.",
                inline=False
            )
            
            embed.set_footer(text="⚠️ Most commands require appropriate permissions • All commands work with both prefix and slash commands")
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='info')
    async def info_command(self, ctx):
        """Show bot information"""
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📊 Statistics",
            value=f"Servers: {len(self.bot.guilds)}\nUsers: {len(self.bot.users)}",
            inline=True
        )
        
        embed.add_field(
            name="🖥️ System",
            value=f"Python: {platform.python_version()}\nDiscord.py: {discord.__version__}",
            inline=True
        )
        
        # Memory usage
        memory_usage = psutil.virtual_memory().percent
        embed.add_field(
            name="💾 Memory Usage",
            value=f"{memory_usage:.1f}%",
            inline=True
        )
        
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed.set_footer(text=f"Bot ID: {self.bot.user.id}")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='uptime')
    async def uptime(self, ctx):
        """Show bot uptime"""
        current_time = time.time()
        uptime_seconds = current_time - self.start_time
        
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        
        embed = discord.Embed(
            title="⏰ Bot Uptime",
            description=f"I've been running for: **{uptime_str}**",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
