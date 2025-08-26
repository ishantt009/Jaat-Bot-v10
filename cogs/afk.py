import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AFK(commands.Cog):
    """AFK system for users to set away status"""
    
    def __init__(self, bot):
        self.bot = bot
        self.afk_file = "afk_users.json"
        self.afk_users = self.load_afk_users()
    
    def load_afk_users(self):
        """Load AFK users from file"""
        try:
            if os.path.exists(self.afk_file):
                with open(self.afk_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load AFK users: {e}")
            return {}
    
    def save_afk_users(self):
        """Save AFK users to file"""
        try:
            with open(self.afk_file, 'w') as f:
                json.dump(self.afk_users, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save AFK users: {e}")
    
    def set_afk(self, guild_id, user_id, reason):
        """Set user as AFK"""
        key = f"{guild_id}_{user_id}"
        self.afk_users[key] = {
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "guild_id": guild_id,
            "user_id": user_id
        }
        self.save_afk_users()
    
    def remove_afk(self, guild_id, user_id):
        """Remove user from AFK"""
        key = f"{guild_id}_{user_id}"
        if key in self.afk_users:
            afk_data = self.afk_users[key]
            del self.afk_users[key]
            self.save_afk_users()
            return afk_data
        return None
    
    def get_afk(self, guild_id, user_id):
        """Check if user is AFK"""
        key = f"{guild_id}_{user_id}"
        return self.afk_users.get(key)
    
    @commands.hybrid_command(name='afk')
    @app_commands.describe(reason="Reason for being AFK")
    @commands.guild_only()
    async def set_afk_status(self, ctx, *, reason: str = "No reason provided"):
        """Set yourself as AFK with a reason"""
        self.set_afk(ctx.guild.id, ctx.author.id, reason)
        
        embed = discord.Embed(
            title="😴 AFK Status Set",
            description=f"**{ctx.author.display_name}** is now AFK",
            color=discord.Color.blue()
        )
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.add_field(name="⏰ Since", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} set AFK in {ctx.guild.name}: {reason}")
    
    @commands.hybrid_command(name='unafk')
    @commands.guild_only()
    async def remove_afk_status(self, ctx):
        """Remove your AFK status"""
        afk_data = self.remove_afk(ctx.guild.id, ctx.author.id)
        
        if afk_data:
            afk_time = datetime.fromisoformat(afk_data["timestamp"])
            duration = datetime.now() - afk_time
            
            embed = discord.Embed(
                title="👋 Welcome Back!",
                description=f"**{ctx.author.display_name}** is no longer AFK",
                color=discord.Color.green()
            )
            embed.add_field(name="📝 Was AFK for", value=afk_data["reason"], inline=False)
            embed.add_field(name="⏰ Duration", value=f"{self.format_duration(duration)}", inline=True)
            
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} removed AFK in {ctx.guild.name}")
        else:
            embed = discord.Embed(
                title="ℹ️ Not AFK",
                description="You are not currently set as AFK.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name='afklist')
    @commands.guild_only()
    async def list_afk_users(self, ctx):
        """List all AFK users in the server"""
        guild_afk_users = []
        
        for key, afk_data in self.afk_users.items():
            if afk_data["guild_id"] == ctx.guild.id:
                user = ctx.guild.get_member(afk_data["user_id"])
                if user:  # User still in server
                    guild_afk_users.append((user, afk_data))
        
        if not guild_afk_users:
            embed = discord.Embed(
                title="😴 AFK Users",
                description="No users are currently AFK in this server.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="😴 AFK Users",
            description=f"{len(guild_afk_users)} user{'s' if len(guild_afk_users) != 1 else ''} currently AFK",
            color=discord.Color.blue()
        )
        
        for user, afk_data in guild_afk_users[:10]:  # Limit to 10 users
            afk_time = datetime.fromisoformat(afk_data["timestamp"])
            duration = datetime.now() - afk_time
            
            embed.add_field(
                name=f"😴 {user.display_name}",
                value=f"**Reason:** {afk_data['reason']}\n**Since:** {self.format_duration(duration)} ago",
                inline=True
            )
        
        if len(guild_afk_users) > 10:
            embed.set_footer(text=f"Showing 10 out of {len(guild_afk_users)} AFK users")
        
        await ctx.send(embed=embed)
    
    def format_duration(self, duration):
        """Format duration into readable string"""
        total_seconds = int(duration.total_seconds())
        
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return "Just now"
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check for AFK users when they send messages or are mentioned"""
        if message.author.bot or not message.guild:
            return
        
        # Check if author is AFK and remove them
        afk_data = self.get_afk(message.guild.id, message.author.id)
        if afk_data:
            self.remove_afk(message.guild.id, message.author.id)
            
            afk_time = datetime.fromisoformat(afk_data["timestamp"])
            duration = datetime.now() - afk_time
            
            embed = discord.Embed(
                title="👋 Welcome Back!",
                description=f"**{message.author.display_name}** is no longer AFK",
                color=discord.Color.green()
            )
            embed.add_field(name="📝 Was AFK for", value=afk_data["reason"], inline=False)
            embed.add_field(name="⏰ Duration", value=f"{self.format_duration(duration)}", inline=True)
            
            try:
                await message.channel.send(embed=embed, delete_after=10)
            except:
                pass
        
        # Check if any mentioned users are AFK
        mentioned_afk = []
        for mentioned_user in message.mentions:
            if mentioned_user.bot:
                continue
            
            afk_data = self.get_afk(message.guild.id, mentioned_user.id)
            if afk_data:
                afk_time = datetime.fromisoformat(afk_data["timestamp"])
                duration = datetime.now() - afk_time
                mentioned_afk.append((mentioned_user, afk_data, duration))
        
        if mentioned_afk:
            embed = discord.Embed(
                title="😴 AFK Users Mentioned",
                color=discord.Color.orange()
            )
            
            for user, afk_data, duration in mentioned_afk[:5]:  # Limit to 5 mentions
                embed.add_field(
                    name=f"😴 {user.display_name}",
                    value=f"**Reason:** {afk_data['reason']}\n**Since:** {self.format_duration(duration)} ago",
                    inline=True
                )
            
            try:
                await message.channel.send(embed=embed, delete_after=15)
            except:
                pass

async def setup(bot):
    await bot.add_cog(AFK(bot))