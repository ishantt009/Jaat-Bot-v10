import discord
from discord.ext import commands
from discord import app_commands
import time
import platform
import os
from cogs.embed_builder import add_embed_id

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
        add_embed_id(embed)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='hello', aliases=['hi', 'hey'])
    async def hello(self, ctx):
        """Say hello to the bot"""
        embed = discord.Embed(
            title="👋 Hello!",
            description=f"Hello {ctx.author.mention}! I'm here to help moderate your server.",
            color=discord.Color.blue()
        )
        add_embed_id(embed)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='help')
    @app_commands.describe(command_name="Name of the command to get help for")
    async def help_command(self, ctx, command_name: str | None = None):
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
                add_embed_id(embed)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Command Not Found",
                    description=f"No command named `{command_name}` found.",
                    color=discord.Color.red()
                )
                add_embed_id(embed)
                await ctx.send(embed=embed)
        else:
            # Show all commands in one compact embed
            embed = discord.Embed(
                title="🤖 Bot Help",
                description=f"All commands • Use `{prefix}help <command>` for details • All work as slash commands too!",
                color=discord.Color.blue()
            )
            
            # Basic & Settings
            basic_commands = [
                f"`{prefix}ping`, `{prefix}hello`, `{prefix}info`, `{prefix}uptime`",
                f"`{prefix}prefix`, `{prefix}setprefix <new>`"
            ]
            embed.add_field(
                name="📋 Basic & Settings",
                value="\n".join(basic_commands),
                inline=True
            )
            
            # Moderation
            mod_commands = [
                f"`{prefix}kick`, `{prefix}ban`, `{prefix}unban`",
                f"`{prefix}mute`, `{prefix}unmute`"
            ]
            embed.add_field(
                name="🔨 Moderation",
                value="\n".join(mod_commands),
                inline=True
            )
            
            # Warnings
            warning_commands = [
                f"`{prefix}warn @user [reason]`",
                f"`{prefix}unwarn @user <id>`",
                f"`{prefix}warnings`, `{prefix}clearwarnings`"
            ]
            embed.add_field(
                name="⚠️ Warnings",
                value="\n".join(warning_commands),
                inline=True
            )
            
            # Roles
            role_commands = [
                f"`{prefix}addrole @user @role`",
                f"`{prefix}removerole @user @role`",
                f"`{prefix}massrole @role add/remove target`"
            ]
            embed.add_field(
                name="🎭 Roles",
                value="\n".join(role_commands),
                inline=True
            )
            
            # AFK
            afk_commands = [
                f"`{prefix}afk [reason]`, `{prefix}unafk`",
                f"`{prefix}afklist`"
            ]
            embed.add_field(
                name="😴 AFK",
                value="\n".join(afk_commands),
                inline=True
            )
            
            # Mass DM
            mass_dm_commands = [
                f"`{prefix}massdm <message>`",
                f"`{prefix}massdmrole @role <msg>`",
                f"`{prefix}dmusers @user1 @user2 <msg>`"
            ]
            embed.add_field(
                name="📨 Mass DM",
                value="\n".join(mass_dm_commands),
                inline=True
            )
            
            # Giveaways
            giveaway_commands = [
                f"`{prefix}gstart <time> <winners> <prize>`",
                f"`{prefix}gend`, `{prefix}greroll`, `{prefix}glist`"
            ]
            embed.add_field(
                name="🎉 Giveaways",
                value="\n".join(giveaway_commands),
                inline=True
            )
            
            # Spin Wheel
            wheel_commands = [
                f"`{prefix}wheeladd @users`, `{prefix}wheelremove`",
                f"`{prefix}spin`, `{prefix}wheellist`, `{prefix}wheelclear`"
            ]
            embed.add_field(
                name="🎯 Spin Wheel",
                value="\n".join(wheel_commands),
                inline=True
            )
            
            # Embed Builder
            embed_commands = [
                f"`{prefix}embed` - Interactive embed builder",
                f"`{prefix}embeds` - List your saved embeds",
                f"`{prefix}viewembed <id>` - View saved embed",
                f"`{prefix}say <msg/embed:id>` - Send as bot",
                f"`{prefix}saychannel #ch <msg/embed:id>`",
                f"`{prefix}dm <user> <msg>` - Send DM to user"
            ]
            embed.add_field(
                name="🎨 Embed Builder & IDs",
                value="\n".join(embed_commands),
                inline=True
            )
            
            # AI Reply System
            ai_commands = [
                f"`{prefix}ai-enable`, `{prefix}ai-disable`",
                f"`{prefix}ai-status`, `{prefix}ai-settings`",
                "Auto AI replies in enabled channels"
            ]
            embed.add_field(
                name="🤖 AI Reply System",
                value="\n".join(ai_commands),
                inline=True
            )
            
            # Sensitive Information (Slash Commands Only)
            sensitive_commands = [
                "`/sensitive <message>` - Send private info to owner",
                "`/sensitive-help` - Learn about the system",
                "**Owner Config:** `/sensitive-config-dm`",
                "`/sensitive-config-channel` `/sensitive-config-status`"
            ]
            embed.add_field(
                name="🔒 Sensitive Information (Slash Only)",
                value="\n".join(sensitive_commands),
                inline=True
            )
            
            embed.add_field(
                name="💡 Tip",
                value="Most commands require mod permissions\nType `/` to see slash commands",
                inline=True
            )
            
            add_embed_id(embed)
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
        
        embed.add_field(
            name="⏰ Uptime",
            value=f"{int((time.time() - self.start_time) // 86400)}d {int(((time.time() - self.start_time) % 86400) // 3600)}h",
            inline=True
        )
        
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed.set_footer(text=f"Bot ID: {self.bot.user.id}")
        
        add_embed_id(embed)
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
        
        add_embed_id(embed)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
