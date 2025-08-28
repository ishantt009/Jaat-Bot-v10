import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from utils.permissions import has_mod_permissions

logger = logging.getLogger(__name__)

class Settings(commands.Cog):
    """Server settings and configuration"""
    
    def __init__(self, bot):
        self.bot = bot
        self.settings_file = "server_settings.json"
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load server settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return {}
    
    def save_settings(self):
        """Save server settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def get_prefix(self, guild_id):
        """Get prefix for a guild"""
        guild_key = str(guild_id)
        if guild_key in self.settings and "prefix" in self.settings[guild_key]:
            return self.settings[guild_key]["prefix"]
        return os.getenv('COMMAND_PREFIX', '!')
    
    def set_prefix(self, guild_id, prefix):
        """Set prefix for a guild"""
        guild_key = str(guild_id)
        if guild_key not in self.settings:
            self.settings[guild_key] = {}
        self.settings[guild_key]["prefix"] = prefix
        self.save_settings()
        
        # Update bot's command prefix
        async def get_prefix(bot, message):
            if not message.guild:
                return os.getenv('COMMAND_PREFIX', '!')
            return self.get_prefix(message.guild.id)
        
        self.bot.command_prefix = get_prefix
    
    @commands.hybrid_command(name='setprefix')
    @app_commands.describe(prefix="New command prefix for the server")
    @commands.guild_only()
    async def set_prefix_command(self, ctx, prefix: str):
        """Change the command prefix for this server"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to change the prefix.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Validate prefix
        if len(prefix) > 5:
            embed = discord.Embed(
                title="❌ Invalid Prefix",
                description="Prefix cannot be longer than 5 characters.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        if not prefix or prefix.isspace():
            embed = discord.Embed(
                title="❌ Invalid Prefix",
                description="Prefix cannot be empty or just whitespace.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Reserved prefixes
        reserved = ['/', '\\', '@', '#']
        if any(char in prefix for char in reserved):
            embed = discord.Embed(
                title="❌ Invalid Prefix",
                description="Prefix cannot contain `/`, `\\`, `@`, or `#` characters.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        old_prefix = self.get_prefix(ctx.guild.id)
        self.set_prefix(ctx.guild.id, prefix)
        
        embed = discord.Embed(
            title="✅ Prefix Changed",
            description=f"Command prefix has been changed from `{old_prefix}` to `{prefix}`",
            color=discord.Color.green()
        )
        embed.add_field(name="📝 New Prefix", value=f"`{prefix}`", inline=True)
        embed.add_field(name="👮 Changed By", value=ctx.author.mention, inline=True)
        embed.add_field(name="📋 Example", value=f"`{prefix}help`", inline=True)
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} changed prefix from '{old_prefix}' to '{prefix}' in {ctx.guild.name}")
    
    @commands.hybrid_command(name='prefix')
    @commands.guild_only()
    async def show_prefix(self, ctx):
        """Show the current command prefix"""
        current_prefix = self.get_prefix(ctx.guild.id)
        
        embed = discord.Embed(
            title="📋 Current Prefix",
            description=f"The command prefix for this server is: `{current_prefix}`",
            color=discord.Color.blue()
        )
        embed.add_field(name="📝 Usage", value=f"`{current_prefix}help`", inline=True)
        embed.add_field(name="🔧 Change", value=f"`{current_prefix}setprefix <new_prefix>`", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    cog = Settings(bot)
    
    # Set up dynamic prefix
    async def get_prefix(bot, message):
        if not message.guild:
            return os.getenv('COMMAND_PREFIX', '!')
        return cog.get_prefix(message.guild.id)
    
    bot.command_prefix = get_prefix
    await bot.add_cog(cog)