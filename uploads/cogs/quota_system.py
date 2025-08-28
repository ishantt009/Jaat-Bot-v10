import discord
from discord.ext import commands
from discord import app_commands
import json
import asyncio
from datetime import datetime, timedelta
from utils.permissions import has_mod_permissions
from cogs.embed_builder import add_embed_id

class QuotaData:
    def __init__(self):
        self.staff_quotas = {}  # {user_id: {action: count}}
        self.custom_quotas = {}  # {quota_name: {user_id: count}}
        self.quota_configs = {}  # {quota_name: {config}}
        self.load_data()
    
    def load_data(self):
        """Load quota data from JSON file"""
        try:
            with open('data/quota_data.json', 'r') as f:
                data = json.load(f)
                self.staff_quotas = data.get('staff_quotas', {})
                self.custom_quotas = data.get('custom_quotas', {})
                self.quota_configs = data.get('quota_configs', {})
        except FileNotFoundError:
            self.save_data()
        except:
            pass
    
    def save_data(self):
        """Save quota data to JSON file"""
        try:
            import os
            os.makedirs('data', exist_ok=True)
            with open('data/quota_data.json', 'w') as f:
                json.dump({
                    'staff_quotas': self.staff_quotas,
                    'custom_quotas': self.custom_quotas,
                    'quota_configs': self.quota_configs
                }, f, indent=2)
        except:
            pass
    
    def add_staff_action(self, user_id, action):
        """Add a staff moderation action"""
        user_id = str(user_id)
        if user_id not in self.staff_quotas:
            self.staff_quotas[user_id] = {}
        
        self.staff_quotas[user_id][action] = self.staff_quotas[user_id].get(action, 0) + 1
        self.save_data()
    
    def add_custom_quota(self, quota_name, user_id, amount=1):
        """Add to custom quota"""
        user_id = str(user_id)
        if quota_name not in self.custom_quotas:
            self.custom_quotas[quota_name] = {}
        
        self.custom_quotas[quota_name][user_id] = self.custom_quotas[quota_name].get(user_id, 0) + amount
        self.save_data()
    
    def create_custom_quota(self, quota_name, description, creator_id):
        """Create a new custom quota"""
        self.quota_configs[quota_name] = {
            'description': description,
            'creator_id': str(creator_id),
            'created_at': datetime.now().isoformat()
        }
        self.custom_quotas[quota_name] = {}
        self.save_data()
    
    def get_staff_stats(self, user_id):
        """Get staff statistics for a user"""
        user_id = str(user_id)
        return self.staff_quotas.get(user_id, {})
    
    def get_custom_quota(self, quota_name, user_id=None):
        """Get custom quota data"""
        if quota_name not in self.custom_quotas:
            return None
        
        if user_id:
            return self.custom_quotas[quota_name].get(str(user_id), 0)
        return self.custom_quotas[quota_name]

# Global quota storage
quota_data = QuotaData()

class QuotaSystem(commands.Cog):
    """Staff and custom quota tracking system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.quota_data = quota_data
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Track bans for staff quota"""
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target == user:
                self.quota_data.add_staff_action(entry.user.id, 'bans')
                break
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Track kicks for staff quota"""
        guild = member.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if entry.target == member:
                self.quota_data.add_staff_action(entry.user.id, 'kicks')
                break
    
    # Staff Quota Commands
    @commands.hybrid_command(name='staffstats')
    @app_commands.describe(member="Staff member to view stats for")
    async def staff_stats(self, ctx, member: discord.Member = None):
        """View staff moderation statistics"""
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to view staff stats.",
                color=discord.Color.red()
            )
            add_embed_id(embed)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        target = member if member else ctx.author
        stats = self.quota_data.get_staff_stats(target.id)
        
        embed = discord.Embed(
            title=f"📊 Staff Statistics - {target.display_name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        if not stats:
            embed.description = "No moderation actions recorded yet."
        else:
            total_actions = sum(stats.values())
            embed.description = f"**Total Actions:** {total_actions}"
            
            # Add individual stats
            action_emojis = {
                'bans': '🔨',
                'kicks': '👢',
                'warns': '⚠️',
                'mutes': '🔇',
                'timeouts': '⏰'
            }
            
            for action, count in stats.items():
                emoji = action_emojis.get(action, '📝')
                embed.add_field(
                    name=f"{emoji} {action.title()}",
                    value=f"`{count}`",
                    inline=True
                )
        
        add_embed_id(embed)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='leaderboard')
    @app_commands.describe(action="Specific action to show leaderboard for")
    async def staff_leaderboard(self, ctx, action: str = ""):
        """Show staff moderation leaderboard"""
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to view leaderboard.",
                color=discord.Color.red()
            )
            add_embed_id(embed)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Calculate leaderboard
        leaderboard = {}
        for user_id, stats in self.quota_data.staff_quotas.items():
            if action and action in stats:
                leaderboard[user_id] = stats[action]
            elif not action:
                leaderboard[user_id] = sum(stats.values())
        
        # Sort by count
        sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)[:10]
        
        embed = discord.Embed(
            title=f"🏆 Staff Leaderboard" + (f" - {action.title()}" if action else ""),
            color=discord.Color.gold()
        )
        
        if not sorted_lb:
            embed.description = "No staff actions recorded yet."
        else:
            description = ""
            for i, (user_id, count) in enumerate(sorted_lb, 1):
                try:
                    user = self.bot.get_user(int(user_id))
                    name = user.display_name if user else f"User {user_id}"
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`{i}.`"
                    description += f"{medal} **{name}**: {count}\n"
                except:
                    continue
            embed.description = description
        
        add_embed_id(embed)
        await ctx.send(embed=embed)
    
    # Custom Quota Commands
    @commands.hybrid_command(name='createquota')
    @app_commands.describe(name="Name of the quota", description="Description of what this quota tracks")
    async def create_quota(self, ctx, name: str, *, description: str):
        """Create a custom quota system"""
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to create quotas.",
                color=discord.Color.red()
            )
            add_embed_id(embed)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Clean quota name
        name = name.lower().replace(' ', '_')
        
        if name in self.quota_data.quota_configs:
            embed = discord.Embed(
                title="❌ Quota Exists",
                description=f"A quota named `{name}` already exists.",
                color=discord.Color.red()
            )
            add_embed_id(embed)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        self.quota_data.create_custom_quota(name, description, ctx.author.id)
        
        embed = discord.Embed(
            title="✅ Quota Created",
            description=f"Successfully created quota: **{name}**\n\n**Description:** {description}",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📝 How to Use",
            value=f"`!addquota {name} @user [amount]` - Add to quota\n`!quotastats {name}` - View quota stats",
            inline=False
        )
        
        add_embed_id(embed)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='addquota')
    @app_commands.describe(quota_name="Name of the quota", member="User to add quota to", amount="Amount to add")
    async def add_quota(self, ctx, quota_name: str, member: discord.Member, amount: int = 1):
        """Add points to a custom quota"""
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to manage quotas.",
                color=discord.Color.red()
            )
            add_embed_id(embed)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        quota_name = quota_name.lower().replace(' ', '_')
        
        if quota_name not in self.quota_data.quota_configs:
            embed = discord.Embed(
                title="❌ Quota Not Found",
                description=f"No quota named `{quota_name}` exists.\nUse `!listquotas` to see available quotas.",
                color=discord.Color.red()
            )
            add_embed_id(embed)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        self.quota_data.add_custom_quota(quota_name, member.id, amount)
        
        embed = discord.Embed(
            title="✅ Quota Updated",
            description=f"Added **{amount}** to {member.mention}'s `{quota_name}` quota.",
            color=discord.Color.green()
        )
        
        # Show new total
        new_total = self.quota_data.get_custom_quota(quota_name, member.id)
        embed.add_field(
            name="📊 New Total",
            value=f"{member.display_name}: **{new_total}**",
            inline=False
        )
        
        add_embed_id(embed)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='quotastats')
    @app_commands.describe(quota_name="Name of the quota to view")
    async def quota_stats(self, ctx, quota_name: str):
        """View custom quota statistics"""
        quota_name = quota_name.lower().replace(' ', '_')
        
        if quota_name not in self.quota_data.quota_configs:
            embed = discord.Embed(
                title="❌ Quota Not Found",
                description=f"No quota named `{quota_name}` exists.\nUse `!listquotas` to see available quotas.",
                color=discord.Color.red()
            )
            add_embed_id(embed)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        config = self.quota_data.quota_configs[quota_name]
        quota_data = self.quota_data.get_custom_quota(quota_name)
        
        embed = discord.Embed(
            title=f"📊 Quota Stats - {quota_name.title()}",
            description=config['description'],
            color=discord.Color.blue()
        )
        
        if not quota_data:
            embed.add_field(
                name="📈 Statistics",
                value="No data recorded yet.",
                inline=False
            )
        else:
            # Sort users by quota amount
            sorted_users = sorted(quota_data.items(), key=lambda x: x[1], reverse=True)[:10]
            
            leaderboard = ""
            total = sum(quota_data.values())
            
            for i, (user_id, count) in enumerate(sorted_users, 1):
                try:
                    user = self.bot.get_user(int(user_id))
                    name = user.display_name if user else f"User {user_id}"
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`{i}.`"
                    leaderboard += f"{medal} **{name}**: {count}\n"
                except:
                    continue
            
            embed.add_field(
                name="📈 Top Contributors",
                value=leaderboard or "No data yet",
                inline=False
            )
            
            embed.add_field(
                name="📊 Total",
                value=f"**{total}** points across {len(quota_data)} users",
                inline=True
            )
        
        add_embed_id(embed)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='listquotas')
    async def list_quotas(self, ctx):
        """List all available custom quotas"""
        embed = discord.Embed(
            title="📋 Available Quotas",
            color=discord.Color.blue()
        )
        
        if not self.quota_data.quota_configs:
            embed.description = "No custom quotas created yet.\nUse `!createquota` to create one!"
        else:
            description = ""
            for quota_name, config in self.quota_data.quota_configs.items():
                try:
                    creator = self.bot.get_user(int(config['creator_id']))
                    creator_name = creator.display_name if creator else "Unknown"
                    description += f"**{quota_name.title()}**\n└ {config['description']}\n└ *Created by {creator_name}*\n\n"
                except:
                    description += f"**{quota_name.title()}**\n└ {config['description']}\n\n"
            
            embed.description = description
        
        embed.add_field(
            name="💡 Commands",
            value="`!quotastats <name>` - View quota stats\n`!addquota <name> @user [amount]` - Add to quota",
            inline=False
        )
        
        add_embed_id(embed)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(QuotaSystem(bot))