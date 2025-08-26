import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from datetime import datetime
from utils.permissions import has_mod_permissions

logger = logging.getLogger(__name__)

class Warnings(commands.Cog):
    """Warning system for user moderation"""
    
    def __init__(self, bot):
        self.bot = bot
        self.warnings_file = "warnings.json"
        self.warnings = self.load_warnings()
    
    def load_warnings(self):
        """Load warnings from file"""
        try:
            if os.path.exists(self.warnings_file):
                with open(self.warnings_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load warnings: {e}")
            return {}
    
    def save_warnings(self):
        """Save warnings to file"""
        try:
            with open(self.warnings_file, 'w') as f:
                json.dump(self.warnings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save warnings: {e}")
    
    def get_user_warnings(self, guild_id, user_id):
        """Get warnings for a specific user"""
        guild_key = str(guild_id)
        user_key = str(user_id)
        
        if guild_key not in self.warnings:
            self.warnings[guild_key] = {}
        
        if user_key not in self.warnings[guild_key]:
            self.warnings[guild_key][user_key] = []
        
        return self.warnings[guild_key][user_key]
    
    def add_warning(self, guild_id, user_id, moderator_id, reason):
        """Add a warning to a user"""
        warnings = self.get_user_warnings(guild_id, user_id)
        
        warning = {
            "id": len(warnings) + 1,
            "reason": reason,
            "moderator_id": moderator_id,
            "timestamp": datetime.now().isoformat(),
            "active": True
        }
        
        warnings.append(warning)
        self.save_warnings()
        return warning["id"]
    
    def remove_warning(self, guild_id, user_id, warning_id):
        """Remove a specific warning"""
        warnings = self.get_user_warnings(guild_id, user_id)
        
        for warning in warnings:
            if warning["id"] == warning_id and warning["active"]:
                warning["active"] = False
                self.save_warnings()
                return True
        return False
    
    def clear_warnings(self, guild_id, user_id):
        """Clear all warnings for a user"""
        warnings = self.get_user_warnings(guild_id, user_id)
        
        cleared_count = 0
        for warning in warnings:
            if warning["active"]:
                warning["active"] = False
                cleared_count += 1
        
        self.save_warnings()
        return cleared_count
    
    @commands.hybrid_command(name='warn')
    @app_commands.describe(
        user="The user to warn",
        reason="Reason for the warning"
    )
    @commands.guild_only()
    async def warn_user(self, ctx, user: discord.Member, *, reason: str = "No reason provided"):
        """Warn a user for breaking rules"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to warn users.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Can't warn yourself
        if user == ctx.author:
            embed = discord.Embed(
                title="❌ Cannot Warn Yourself",
                description="You cannot warn yourself.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Can't warn bots
        if user.bot:
            embed = discord.Embed(
                title="❌ Cannot Warn Bots",
                description="You cannot warn bots.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Check role hierarchy
        if user.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Role Hierarchy Error",
                description="You cannot warn someone with a higher or equal role.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Add warning
        warning_id = self.add_warning(ctx.guild.id, user.id, ctx.author.id, reason)
        user_warnings = self.get_user_warnings(ctx.guild.id, user.id)
        active_warnings = [w for w in user_warnings if w["active"]]
        
        # Create warning embed
        embed = discord.Embed(
            title="⚠️ User Warned",
            description=f"**{user.display_name}** has been warned.",
            color=discord.Color.orange()
        )
        
        embed.add_field(name="👤 User", value=user.mention, inline=True)
        embed.add_field(name="👮 Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="🆔 Warning ID", value=f"#{warning_id}", inline=True)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.add_field(name="📊 Total Warnings", value=f"{len(active_warnings)} warning{'s' if len(active_warnings) != 1 else ''}", inline=True)
        
        await ctx.send(embed=embed)
        
        # Try to DM the user
        try:
            dm_embed = discord.Embed(
                title="⚠️ You have been warned",
                description=f"You received a warning in **{ctx.guild.name}**",
                color=discord.Color.orange()
            )
            dm_embed.add_field(name="📝 Reason", value=reason, inline=False)
            dm_embed.add_field(name="👮 Moderator", value=str(ctx.author), inline=True)
            dm_embed.add_field(name="📊 Total Warnings", value=f"{len(active_warnings)}", inline=True)
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # User has DMs disabled
        
        logger.info(f"{ctx.author} warned {user} in {ctx.guild.name}: {reason}")
    
    @commands.hybrid_command(name='unwarn')
    @app_commands.describe(
        user="The user to remove warning from",
        warning_id="ID of the warning to remove"
    )
    @commands.guild_only()
    async def unwarn_user(self, ctx, user: discord.Member, warning_id: int):
        """Remove a specific warning from a user"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to remove warnings.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Remove warning
        if self.remove_warning(ctx.guild.id, user.id, warning_id):
            user_warnings = self.get_user_warnings(ctx.guild.id, user.id)
            active_warnings = [w for w in user_warnings if w["active"]]
            
            embed = discord.Embed(
                title="✅ Warning Removed",
                description=f"Warning #{warning_id} has been removed from **{user.display_name}**.",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 User", value=user.mention, inline=True)
            embed.add_field(name="👮 Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="📊 Remaining Warnings", value=f"{len(active_warnings)}", inline=True)
            
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} removed warning #{warning_id} from {user} in {ctx.guild.name}")
        else:
            embed = discord.Embed(
                title="❌ Warning Not Found",
                description=f"Warning #{warning_id} not found for **{user.display_name}**.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name='warnings')
    @app_commands.describe(user="The user to check warnings for")
    @commands.guild_only()
    async def check_warnings(self, ctx, user: discord.Member = None):
        """Check warnings for a user (or yourself)"""
        if user is None:
            user = ctx.author
        
        # Only moderators can check other users' warnings
        if user != ctx.author and not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You can only check your own warnings.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        user_warnings = self.get_user_warnings(ctx.guild.id, user.id)
        active_warnings = [w for w in user_warnings if w["active"]]
        
        if not active_warnings:
            embed = discord.Embed(
                title="✅ No Warnings",
                description=f"**{user.display_name}** has no active warnings.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="⚠️ User Warnings",
            description=f"**{user.display_name}** has {len(active_warnings)} active warning{'s' if len(active_warnings) != 1 else ''}",
            color=discord.Color.orange()
        )
        
        # Show up to 10 most recent warnings
        for warning in active_warnings[-10:]:
            try:
                moderator = self.bot.get_user(warning["moderator_id"]) or "Unknown Moderator"
                timestamp = datetime.fromisoformat(warning["timestamp"]).strftime("%Y-%m-%d %H:%M")
                
                embed.add_field(
                    name=f"Warning #{warning['id']} - {timestamp}",
                    value=f"**Reason:** {warning['reason']}\n**Moderator:** {moderator}",
                    inline=False
                )
            except:
                continue
        
        if len(active_warnings) > 10:
            embed.set_footer(text=f"Showing 10 most recent warnings out of {len(active_warnings)} total")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='clearwarnings')
    @app_commands.describe(user="The user to clear warnings for")
    @commands.guild_only()
    async def clear_user_warnings(self, ctx, user: discord.Member):
        """Clear all warnings for a user"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to clear warnings.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        cleared_count = self.clear_warnings(ctx.guild.id, user.id)
        
        if cleared_count > 0:
            embed = discord.Embed(
                title="✅ Warnings Cleared",
                description=f"Cleared {cleared_count} warning{'s' if cleared_count != 1 else ''} for **{user.display_name}**.",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 User", value=user.mention, inline=True)
            embed.add_field(name="👮 Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} cleared {cleared_count} warnings for {user} in {ctx.guild.name}")
        else:
            embed = discord.Embed(
                title="ℹ️ No Warnings to Clear",
                description=f"**{user.display_name}** has no active warnings to clear.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Warnings(bot))