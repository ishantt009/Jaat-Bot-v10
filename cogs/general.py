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
        # Get the correct prefix for this server
        try:
            settings_cog = self.bot.get_cog('Settings')
            if settings_cog and ctx.guild:
                prefix = settings_cog.get_prefix(ctx.guild.id)
            else:
                prefix = os.getenv('COMMAND_PREFIX', '!')
        except:
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
            # Show general help - split into multiple embeds to avoid character limits
            
            # Main help embed
            embed1 = discord.Embed(
                title="🤖 Bot Help",
                description=f"Here are all available commands. Use `{prefix}help <command>` for detailed help.\n💡 All commands work as slash commands too! Type `/` to see them.",
                color=discord.Color.blue()
            )
            
            # Basic commands
            basic_commands = [
                f"`{prefix}ping` - Check latency",
                f"`{prefix}hello` - Say hello",
                f"`{prefix}info` - Bot information",
                f"`{prefix}uptime` - Bot uptime",
                f"`{prefix}prefix` - Show current prefix",
                f"`{prefix}setprefix <new>` - Change prefix"
            ]
            embed1.add_field(
                name="📋 Basic Commands",
                value="\n".join(basic_commands),
                inline=True
            )
            
            # Moderation commands
            mod_commands = [
                f"`{prefix}kick @user [reason]`",
                f"`{prefix}ban @user [reason]`", 
                f"`{prefix}unban <user>`",
                f"`{prefix}mute @user [reason]`",
                f"`{prefix}unmute @user`"
            ]
            embed1.add_field(
                name="🔨 Moderation",
                value="\n".join(mod_commands),
                inline=True
            )
            
            # Warning system
            warning_commands = [
                f"`{prefix}warn @user [reason]`",
                f"`{prefix}unwarn @user <id>`",
                f"`{prefix}warnings [@user]`",
                f"`{prefix}clearwarnings @user`"
            ]
            embed1.add_field(
                name="⚠️ Warnings",
                value="\n".join(warning_commands),
                inline=True
            )
            
            await ctx.send(embed=embed1)
            
            # Second embed for advanced features
            embed2 = discord.Embed(
                title="🤖 Advanced Features",
                color=discord.Color.blue()
            )
            
            # Role management
            role_commands = [
                f"`{prefix}addrole @user @role`",
                f"`{prefix}removerole @user @role`",
                f"`{prefix}massrole @role add/remove target`"
            ]
            embed2.add_field(
                name="🎭 Role Management",
                value="\n".join(role_commands),
                inline=True
            )
            
            # AFK system
            afk_commands = [
                f"`{prefix}afk [reason]` - Set AFK",
                f"`{prefix}unafk` - Remove AFK",
                f"`{prefix}afklist` - List AFK users"
            ]
            embed2.add_field(
                name="😴 AFK System",
                value="\n".join(afk_commands),
                inline=True
            )
            
            # Mass DM
            mass_dm_commands = [
                f"`{prefix}massdm <message>`",
                f"`{prefix}massdmrole @role <msg>`"
            ]
            embed2.add_field(
                name="📨 Mass DM",
                value="\n".join(mass_dm_commands),
                inline=True
            )
            
            await ctx.send(embed=embed2)
            
            # Third embed for fun features
            embed3 = discord.Embed(
                title="🎉 Fun Features",
                color=discord.Color.blue()
            )
            
            # Giveaways
            giveaway_commands = [
                f"`{prefix}gstart <time> <winners> <prize>`",
                f"`{prefix}gend <msg_id>` - End early",
                f"`{prefix}greroll <msg_id>` - Reroll",
                f"`{prefix}glist` - List active"
            ]
            embed3.add_field(
                name="🎉 Giveaways",
                value="\n".join(giveaway_commands),
                inline=True
            )
            
            # Spin Wheel
            wheel_commands = [
                f"`{prefix}wheeladd @users`",
                f"`{prefix}wheelremove @users`",
                f"`{prefix}wheellist` - Show wheel",
                f"`{prefix}spin` - Spin it!",
                f"`{prefix}wheelclear` - Clear all"
            ]
            embed3.add_field(
                name="🎯 Spin Wheel",
                value="\n".join(wheel_commands),
                inline=True
            )
            
            embed3.add_field(
                name="🔗 Links & Support",
                value="Need help? Use `/help` for slash commands\nMost commands require mod permissions",
                inline=True
            )
            
            await ctx.send(embed=embed3)
    
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
