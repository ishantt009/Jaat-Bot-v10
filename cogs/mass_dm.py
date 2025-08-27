import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
import os
from utils.permissions import has_admin_permissions

logger = logging.getLogger(__name__)

class MassDM(commands.Cog):
    """Mass DM functionality for server administrators"""
    
    def __init__(self, bot):
        self.bot = bot
        self.rate_limit = float(os.getenv('MASS_DM_RATE_LIMIT', '1'))  # Messages per second
    
    @commands.hybrid_command(name='massdm')
    @app_commands.describe(message="The message to send to all members")
    @commands.guild_only()
    async def mass_dm(self, ctx, *, message):
        """Send a DM to all members in the server"""
        # Permission check - only admins can use mass DM
        if not has_admin_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need administrator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Confirmation embed
        embed = discord.Embed(
            title="⚠️ Mass DM Confirmation",
            description=f"Are you sure you want to send this message to **{len(ctx.guild.members)}** members?",
            color=discord.Color.orange()
        )
        embed.add_field(name="Message Preview", value=message[:1000] + ("..." if len(message) > 1000 else ""), inline=False)
        embed.add_field(name="Server", value=ctx.guild.name, inline=True)
        embed.add_field(name="Requested by", value=ctx.author.mention, inline=True)
        embed.set_footer(text="React with ✅ to confirm or ❌ to cancel (30 seconds)")
        
        confirmation_msg = await ctx.send(embed=embed)
        await confirmation_msg.add_reaction("✅")
        await confirmation_msg.add_reaction("❌")
        
        def check(reaction, user):
            return (user == ctx.author and 
                   str(reaction.emoji) in ["✅", "❌"] and 
                   reaction.message.id == confirmation_msg.id)
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                embed = discord.Embed(
                    title="❌ Mass DM Cancelled",
                    description="Mass DM operation has been cancelled.",
                    color=discord.Color.red()
                )
                await confirmation_msg.edit(embed=embed)
                return
            
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏰ Timeout",
                description="Mass DM confirmation timed out.",
                color=discord.Color.red()
            )
            await confirmation_msg.edit(embed=embed)
            return
        
        # Start mass DM process
        await self._send_mass_dm(ctx, confirmation_msg, message, ctx.guild.members)
    
    @commands.hybrid_command(name='massdmrole')
    @app_commands.describe(
        role="The role to send DMs to",
        message="The message to send"
    )
    @commands.guild_only()
    async def mass_dm_role(self, ctx, role: discord.Role, *, message):
        """Send a DM to all members with a specific role"""
        # Permission check - only admins can use mass DM
        if not has_admin_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need administrator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Get members with the role
        role_members = [member for member in ctx.guild.members if role in member.roles]
        
        if not role_members:
            embed = discord.Embed(
                title="❌ No Members Found",
                description=f"No members found with the role **{role.name}**.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Confirmation embed
        embed = discord.Embed(
            title="⚠️ Mass DM Confirmation",
            description=f"Are you sure you want to send this message to **{len(role_members)}** members with the role **{role.name}**?",
            color=discord.Color.orange()
        )
        embed.add_field(name="Message Preview", value=message[:1000] + ("..." if len(message) > 1000 else ""), inline=False)
        embed.add_field(name="Role", value=role.mention, inline=True)
        embed.add_field(name="Server", value=ctx.guild.name, inline=True)
        embed.add_field(name="Requested by", value=ctx.author.mention, inline=True)
        embed.set_footer(text="React with ✅ to confirm or ❌ to cancel (30 seconds)")
        
        confirmation_msg = await ctx.send(embed=embed)
        await confirmation_msg.add_reaction("✅")
        await confirmation_msg.add_reaction("❌")
        
        def check(reaction, user):
            return (user == ctx.author and 
                   str(reaction.emoji) in ["✅", "❌"] and 
                   reaction.message.id == confirmation_msg.id)
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                embed = discord.Embed(
                    title="❌ Mass DM Cancelled",
                    description="Mass DM operation has been cancelled.",
                    color=discord.Color.red()
                )
                await confirmation_msg.edit(embed=embed)
                return
            
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏰ Timeout",
                description="Mass DM confirmation timed out.",
                color=discord.Color.red()
            )
            await confirmation_msg.edit(embed=embed)
            return
        
        # Start mass DM process
        await self._send_mass_dm(ctx, confirmation_msg, message, role_members)
    
    @commands.hybrid_command(name='dmusers')
    @app_commands.describe(
        users="Mention the users to send DMs to (space-separated)",
        message="The message to send"
    )
    @commands.guild_only()
    async def dm_users(self, ctx, users: commands.Greedy[discord.Member], *, message):
        """Send a DM to specific mentioned users"""
        # Permission check - only admins can use mass DM
        if not has_admin_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need administrator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check if users were provided
        if not users:
            embed = discord.Embed(
                title="❌ No Users Specified",
                description="Please mention the users you want to send DMs to.\n\nExample: `!dmusers @user1 @user2 @user3 Your message here`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Filter out bots and duplicates
        valid_users = []
        for user in users:
            if not user.bot and user not in valid_users:
                valid_users.append(user)
        
        if not valid_users:
            embed = discord.Embed(
                title="❌ No Valid Users",
                description="No valid human users found to send DMs to.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Confirmation embed
        user_list = ", ".join([user.mention for user in valid_users[:10]])
        if len(valid_users) > 10:
            user_list += f"\n... and {len(valid_users) - 10} more"
        
        embed = discord.Embed(
            title="⚠️ DM Users Confirmation",
            description=f"Are you sure you want to send this message to **{len(valid_users)}** users?",
            color=discord.Color.orange()
        )
        embed.add_field(name="Message Preview", value=message[:1000] + ("..." if len(message) > 1000 else ""), inline=False)
        embed.add_field(name="Recipients", value=user_list, inline=False)
        embed.add_field(name="Server", value=ctx.guild.name, inline=True)
        embed.add_field(name="Requested by", value=ctx.author.mention, inline=True)
        embed.set_footer(text="React with ✅ to confirm or ❌ to cancel (30 seconds)")
        
        confirmation_msg = await ctx.send(embed=embed)
        await confirmation_msg.add_reaction("✅")
        await confirmation_msg.add_reaction("❌")
        
        def check(reaction, user):
            return (user == ctx.author and 
                   str(reaction.emoji) in ["✅", "❌"] and 
                   reaction.message.id == confirmation_msg.id)
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                embed = discord.Embed(
                    title="❌ DM Users Cancelled",
                    description="DM users operation has been cancelled.",
                    color=discord.Color.red()
                )
                await confirmation_msg.edit(embed=embed)
                return
            
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏰ Timeout",
                description="DM users confirmation timed out.",
                color=discord.Color.red()
            )
            await confirmation_msg.edit(embed=embed)
            return
        
        # Start DM process
        await self._send_mass_dm(ctx, confirmation_msg, message, valid_users)
    
    async def _send_mass_dm(self, ctx, status_msg, message, members):
        """Internal method to handle the mass DM sending process"""
        # Filter out bots
        human_members = [member for member in members if not member.bot]
        total_members = len(human_members)
        
        if total_members == 0:
            embed = discord.Embed(
                title="❌ No Valid Recipients",
                description="No human members found to send DMs to.",
                color=discord.Color.red()
            )
            await status_msg.edit(embed=embed)
            return
        
        # Create the DM embed
        dm_embed = discord.Embed(
            title=f"Message from {ctx.guild.name}",
            description=message,
            color=discord.Color.blue()
        )
        dm_embed.set_footer(text=f"Sent by {ctx.author} • {ctx.guild.name}")
        if ctx.guild.icon:
            dm_embed.set_thumbnail(url=ctx.guild.icon.url)
        
        # Progress tracking
        successful = 0
        failed = 0
        processed = 0
        
        # Update status message
        status_embed = discord.Embed(
            title="📨 Sending Mass DM...",
            description=f"Progress: 0/{total_members}",
            color=discord.Color.blue()
        )
        status_embed.add_field(name="Successful", value="0", inline=True)
        status_embed.add_field(name="Failed", value="0", inline=True)
        status_embed.add_field(name="Remaining", value=str(total_members), inline=True)
        await status_msg.edit(embed=status_embed)
        
        # Send DMs with rate limiting
        for member in human_members:
            try:
                await member.send(embed=dm_embed)
                successful += 1
                logger.info(f"Mass DM sent to {member} from {ctx.guild.name}")
            except discord.Forbidden:
                # User has DMs disabled
                failed += 1
                logger.warning(f"Could not send DM to {member} - DMs disabled")
            except discord.HTTPException as e:
                # Other HTTP errors
                failed += 1
                logger.error(f"Failed to send DM to {member}: {e}")
            except Exception as e:
                # Unexpected errors
                failed += 1
                logger.error(f"Unexpected error sending DM to {member}: {e}")
            
            processed += 1
            
            # Update status every 10 members or on completion
            if processed % 10 == 0 or processed == total_members:
                status_embed = discord.Embed(
                    title="📨 Sending Mass DM...",
                    description=f"Progress: {processed}/{total_members}",
                    color=discord.Color.blue()
                )
                status_embed.add_field(name="Successful", value=str(successful), inline=True)
                status_embed.add_field(name="Failed", value=str(failed), inline=True)
                status_embed.add_field(name="Remaining", value=str(total_members - processed), inline=True)
                
                if processed < total_members:
                    status_embed.set_footer(text="Please wait... Rate limiting is in effect")
                
                try:
                    await status_msg.edit(embed=status_embed)
                except discord.NotFound:
                    # Status message was deleted
                    break
            
            # Rate limiting - wait between sends
            if processed < total_members:
                await asyncio.sleep(1.0 / self.rate_limit)
        
        # Final status update
        final_embed = discord.Embed(
            title="✅ Mass DM Complete!",
            description=f"Mass DM operation completed.",
            color=discord.Color.green()
        )
        final_embed.add_field(name="Total Members", value=str(total_members), inline=True)
        final_embed.add_field(name="Successful", value=str(successful), inline=True)
        final_embed.add_field(name="Failed", value=str(failed), inline=True)
        
        success_rate = (successful / total_members * 100) if total_members > 0 else 0
        final_embed.add_field(name="Success Rate", value=f"{success_rate:.1f}%", inline=False)
        
        final_embed.set_footer(text=f"Requested by {ctx.author}")
        
        await status_msg.edit(embed=final_embed)
        
        # Log the mass DM operation
        logger.info(f"Mass DM completed in {ctx.guild.name} by {ctx.author}: {successful}/{total_members} successful")

async def setup(bot):
    await bot.add_cog(MassDM(bot))
