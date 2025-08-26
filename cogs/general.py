import discord
from discord.ext import commands
import time
import platform
import psutil
import os

class General(commands.Cog):
    """General commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Check bot latency"""
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: {round(self.bot.latency * 1000)}ms",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='hello', aliases=['hi', 'hey'])
    async def hello(self, ctx):
        """Say hello to the bot"""
        embed = discord.Embed(
            title="👋 Hello!",
            description=f"Hello {ctx.author.mention}! I'm here to help moderate your server.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='help')
    async def help_command(self, ctx, *, command_name=None):
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
                f"`{prefix}massrole <role> <message>` - Send DM to role members"
            ]
            embed.add_field(
                name="📨 Mass DM Commands",
                value="\n".join(mass_dm_commands),
                inline=False
            )
            
            embed.set_footer(text="⚠️ Moderation and Mass DM commands require appropriate permissions")
            await ctx.send(embed=embed)
    
    @commands.command(name='info')
    async def bot_info(self, ctx):
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
    
    @commands.command(name='uptime')
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
