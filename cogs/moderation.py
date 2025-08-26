import discord
from discord.ext import commands
import logging
from utils.permissions import has_mod_permissions, has_admin_permissions

logger = logging.getLogger(__name__)

class Moderation(commands.Cog):
    """Moderation commands for server management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.muted_role_name = "Muted"
    
    async def get_or_create_muted_role(self, guild):
        """Get or create the muted role"""
        muted_role = discord.utils.get(guild.roles, name=self.muted_role_name)
        
        if not muted_role:
            try:
                muted_role = await guild.create_role(
                    name=self.muted_role_name,
                    color=discord.Color.dark_gray(),
                    reason="Created muted role for moderation"
                )
                
                # Set permissions for all channels
                for channel in guild.channels:
                    try:
                        if isinstance(channel, discord.TextChannel):
                            await channel.set_permissions(
                                muted_role,
                                send_messages=False,
                                add_reactions=False,
                                speak=False
                            )
                        elif isinstance(channel, discord.VoiceChannel):
                            await channel.set_permissions(
                                muted_role,
                                speak=False,
                                use_voice_activation=False
                            )
                    except discord.Forbidden:
                        logger.warning(f"Could not set permissions for {channel.name}")
                
                logger.info(f"Created muted role in {guild.name}")
            except discord.Forbidden:
                logger.error(f"Missing permissions to create muted role in {guild.name}")
                return None
        
        return muted_role
    
    @commands.command(name='kick')
    @commands.guild_only()
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member from the server"""
        # Permission checks
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check if bot can kick the member
        if not ctx.guild.me.guild_permissions.kick_members:
            embed = discord.Embed(
                title="❌ Bot Missing Permissions",
                description="I don't have permission to kick members.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check role hierarchy
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Role Hierarchy Error",
                description="You cannot kick someone with a higher or equal role.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            embed = discord.Embed(
                title="❌ Role Hierarchy Error",
                description="I cannot kick someone with a higher or equal role than mine.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Cannot kick bot owner or yourself
        if member == ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Cannot Kick Owner",
                description="Cannot kick the server owner.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if member == ctx.author:
            embed = discord.Embed(
                title="❌ Cannot Kick Yourself",
                description="You cannot kick yourself.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Try to DM the user before kicking
            try:
                dm_embed = discord.Embed(
                    title="You have been kicked",
                    description=f"You were kicked from **{ctx.guild.name}**",
                    color=discord.Color.orange()
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Kick the member
            await member.kick(reason=f"Kicked by {ctx.author}: {reason}")
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ Member Kicked",
                description=f"**{member}** has been kicked from the server.",
                color=discord.Color.green()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
            
            logger.info(f"{ctx.author} kicked {member} from {ctx.guild.name}: {reason}")
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Failed to Kick",
                description="Failed to kick the member. Check my permissions.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='ban')
    @commands.guild_only()
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a member from the server"""
        # Permission checks
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check if bot can ban the member
        if not ctx.guild.me.guild_permissions.ban_members:
            embed = discord.Embed(
                title="❌ Bot Missing Permissions",
                description="I don't have permission to ban members.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check role hierarchy
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Role Hierarchy Error",
                description="You cannot ban someone with a higher or equal role.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            embed = discord.Embed(
                title="❌ Role Hierarchy Error",
                description="I cannot ban someone with a higher or equal role than mine.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Cannot ban bot owner or yourself
        if member == ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Cannot Ban Owner",
                description="Cannot ban the server owner.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if member == ctx.author:
            embed = discord.Embed(
                title="❌ Cannot Ban Yourself",
                description="You cannot ban yourself.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Try to DM the user before banning
            try:
                dm_embed = discord.Embed(
                    title="You have been banned",
                    description=f"You were banned from **{ctx.guild.name}**",
                    color=discord.Color.red()
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Ban the member
            await member.ban(reason=f"Banned by {ctx.author}: {reason}", delete_message_days=0)
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ Member Banned",
                description=f"**{member}** has been banned from the server.",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
            
            logger.info(f"{ctx.author} banned {member} from {ctx.guild.name}: {reason}")
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Failed to Ban",
                description="Failed to ban the member. Check my permissions.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='unban')
    @commands.guild_only()
    async def unban(self, ctx, *, user):
        """Unban a user from the server"""
        # Permission checks
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check if bot can unban
        if not ctx.guild.me.guild_permissions.ban_members:
            embed = discord.Embed(
                title="❌ Bot Missing Permissions",
                description="I don't have permission to unban members.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            banned_users = [entry async for entry in ctx.guild.bans()]
            
            # Try to find user by ID or username#discriminator
            user_to_unban = None
            if user.isdigit():
                # User ID provided
                user_to_unban = discord.utils.get(banned_users, user__id=int(user))
            else:
                # Username provided
                user_to_unban = discord.utils.get(banned_users, user__name=user)
                if not user_to_unban:
                    # Try with display name
                    user_to_unban = discord.utils.get(banned_users, user__display_name=user)
            
            if user_to_unban:
                await ctx.guild.unban(user_to_unban.user, reason=f"Unbanned by {ctx.author}")
                
                embed = discord.Embed(
                    title="✅ Member Unbanned",
                    description=f"**{user_to_unban.user}** has been unbanned.",
                    color=discord.Color.green()
                )
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                await ctx.send(embed=embed)
                
                logger.info(f"{ctx.author} unbanned {user_to_unban.user} from {ctx.guild.name}")
            else:
                embed = discord.Embed(
                    title="❌ User Not Found",
                    description=f"Could not find a banned user matching: {user}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Failed to Unban",
                description="Failed to unban the user. Check my permissions.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='mute')
    @commands.guild_only()
    async def mute(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Mute a member in the server"""
        # Permission checks
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check if bot can manage roles
        if not ctx.guild.me.guild_permissions.manage_roles:
            embed = discord.Embed(
                title="❌ Bot Missing Permissions",
                description="I don't have permission to manage roles.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Get or create muted role
        muted_role = await self.get_or_create_muted_role(ctx.guild)
        if not muted_role:
            embed = discord.Embed(
                title="❌ Failed to Create Muted Role",
                description="Could not create or find the muted role.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check if user is already muted
        if muted_role in member.roles:
            embed = discord.Embed(
                title="❌ Already Muted",
                description=f"**{member}** is already muted.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check role hierarchy
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Role Hierarchy Error",
                description="You cannot mute someone with a higher or equal role.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            await member.add_roles(muted_role, reason=f"Muted by {ctx.author}: {reason}")
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title="You have been muted",
                    description=f"You were muted in **{ctx.guild.name}**",
                    color=discord.Color.orange()
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ Member Muted",
                description=f"**{member}** has been muted.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
            
            logger.info(f"{ctx.author} muted {member} in {ctx.guild.name}: {reason}")
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Failed to Mute",
                description="Failed to mute the member. Check my permissions and role hierarchy.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='unmute')
    @commands.guild_only()
    async def unmute(self, ctx, member: discord.Member):
        """Unmute a member in the server"""
        # Permission checks
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Get muted role
        muted_role = discord.utils.get(ctx.guild.roles, name=self.muted_role_name)
        if not muted_role:
            embed = discord.Embed(
                title="❌ Muted Role Not Found",
                description="Could not find the muted role.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check if user is muted
        if muted_role not in member.roles:
            embed = discord.Embed(
                title="❌ Not Muted",
                description=f"**{member}** is not muted.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            await member.remove_roles(muted_role, reason=f"Unmuted by {ctx.author}")
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title="You have been unmuted",
                    description=f"You were unmuted in **{ctx.guild.name}**",
                    color=discord.Color.green()
                )
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ Member Unmuted",
                description=f"**{member}** has been unmuted.",
                color=discord.Color.green()
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
            
            logger.info(f"{ctx.author} unmuted {member} in {ctx.guild.name}")
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Failed to Unmute",
                description="Failed to unmute the member. Check my permissions.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
