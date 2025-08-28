import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from utils.permissions import has_mod_permissions

logger = logging.getLogger(__name__)

class Roles(commands.Cog):
    """Role management commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name='addrole')
    @app_commands.describe(
        user="The user to give the role to",
        role="The role to add"
    )
    @commands.guild_only()
    async def add_role(self, ctx, user: discord.Member, role: discord.Role):
        """Add a role to a user"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to manage roles.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Check if bot can manage the role
        if role >= ctx.guild.me.top_role:
            embed = discord.Embed(
                title="❌ Role Too High",
                description="I cannot manage this role as it's higher than or equal to my highest role.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Check role hierarchy for user
        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Role Hierarchy Error",
                description="You cannot assign a role higher than or equal to your highest role.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Check if user already has the role
        if role in user.roles:
            embed = discord.Embed(
                title="⚠️ Role Already Assigned",
                description=f"**{user.display_name}** already has the role **{role.name}**.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        try:
            await user.add_roles(role, reason=f"Role added by {ctx.author}")
            
            embed = discord.Embed(
                title="✅ Role Added",
                description=f"Successfully added **{role.name}** to **{user.display_name}**.",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 User", value=user.mention, inline=True)
            embed.add_field(name="🎭 Role", value=role.mention, inline=True)
            embed.add_field(name="👮 Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} added role {role.name} to {user} in {ctx.guild.name}")
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="I don't have permission to manage this role.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name='removerole')
    @app_commands.describe(
        user="The user to remove the role from",
        role="The role to remove"
    )
    @commands.guild_only()
    async def remove_role(self, ctx, user: discord.Member, role: discord.Role):
        """Remove a role from a user"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to manage roles.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Check if bot can manage the role
        if role >= ctx.guild.me.top_role:
            embed = discord.Embed(
                title="❌ Role Too High",
                description="I cannot manage this role as it's higher than or equal to my highest role.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Check role hierarchy for user
        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Role Hierarchy Error",
                description="You cannot remove a role higher than or equal to your highest role.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Check if user has the role
        if role not in user.roles:
            embed = discord.Embed(
                title="⚠️ Role Not Found",
                description=f"**{user.display_name}** doesn't have the role **{role.name}**.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        try:
            await user.remove_roles(role, reason=f"Role removed by {ctx.author}")
            
            embed = discord.Embed(
                title="✅ Role Removed",
                description=f"Successfully removed **{role.name}** from **{user.display_name}**.",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 User", value=user.mention, inline=True)
            embed.add_field(name="🎭 Role", value=role.mention, inline=True)
            embed.add_field(name="👮 Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} removed role {role.name} from {user} in {ctx.guild.name}")
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="I don't have permission to manage this role.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name='massrole')
    @app_commands.describe(
        role="The role to assign/remove",
        action="Whether to add or remove the role",
        target="Target group (all, humans, bots, or role)"
    )
    @commands.guild_only()
    async def mass_role(self, ctx, role: discord.Role, action: str, target: str = "humans"):
        """Add or remove a role from multiple users
        
        Actions: add, remove
        Targets: all, humans, bots, @role
        """
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to manage roles.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Validate action
        if action.lower() not in ['add', 'remove']:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="Action must be either 'add' or 'remove'.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Check if bot can manage the role
        if role >= ctx.guild.me.top_role:
            embed = discord.Embed(
                title="❌ Role Too High",
                description="I cannot manage this role as it's higher than or equal to my highest role.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Check role hierarchy
        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Role Hierarchy Error",
                description="You cannot manage a role higher than or equal to your highest role.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Determine target members
        target_members = []
        target_role = None
        
        if target.lower() == "all":
            target_members = list(ctx.guild.members)
        elif target.lower() == "humans":
            target_members = [m for m in ctx.guild.members if not m.bot]
        elif target.lower() == "bots":
            target_members = [m for m in ctx.guild.members if m.bot]
        else:
            # Try to parse as role mention or name
            try:
                if target.startswith('<@&') and target.endswith('>'):
                    role_id = int(target[3:-1])
                    target_role = ctx.guild.get_role(role_id)
                else:
                    target_role = discord.utils.get(ctx.guild.roles, name=target)
                
                if target_role:
                    target_members = [m for m in ctx.guild.members if target_role in m.roles]
                else:
                    embed = discord.Embed(
                        title="❌ Invalid Target",
                        description="Target must be 'all', 'humans', 'bots', or a valid role.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed, ephemeral=True)
                    return
            except:
                embed = discord.Embed(
                    title="❌ Invalid Target",
                    description="Target must be 'all', 'humans', 'bots', or a valid role.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed, ephemeral=True)
                return
        
        # Filter members based on action
        if action.lower() == "add":
            target_members = [m for m in target_members if role not in m.roles]
            action_verb = "add"
            action_past = "added"
        else:
            target_members = [m for m in target_members if role in m.roles]
            action_verb = "remove"
            action_past = "removed"
        
        if not target_members:
            embed = discord.Embed(
                title="ℹ️ No Members to Update",
                description=f"No members found to {action_verb} the role {'to' if action.lower() == 'add' else 'from'}.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        # Confirmation
        target_desc = target_role.name if target_role else target.lower()
        embed = discord.Embed(
            title="⚠️ Mass Role Confirmation",
            description=f"Are you sure you want to {action_verb} **{role.name}** {'to' if action.lower() == 'add' else 'from'} **{len(target_members)}** members in **{target_desc}**?",
            color=discord.Color.orange()
        )
        embed.add_field(name="🎭 Role", value=role.mention, inline=True)
        embed.add_field(name="🎯 Target", value=target_desc, inline=True)
        embed.add_field(name="👥 Members", value=f"{len(target_members)}", inline=True)
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
                    title="❌ Mass Role Cancelled",
                    description="Mass role operation has been cancelled.",
                    color=discord.Color.red()
                )
                await confirmation_msg.edit(embed=embed)
                return
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏰ Timeout",
                description="Mass role confirmation timed out.",
                color=discord.Color.red()
            )
            await confirmation_msg.edit(embed=embed)
            return
        
        # Perform mass role operation
        success_count = 0
        failed_count = 0
        
        # Update status message
        status_embed = discord.Embed(
            title=f"🔄 Mass Role {action_verb.title()}ing...",
            description=f"Progress: 0/{len(target_members)}",
            color=discord.Color.blue()
        )
        status_embed.add_field(name="✅ Successful", value="0", inline=True)
        status_embed.add_field(name="❌ Failed", value="0", inline=True)
        status_embed.add_field(name="⏳ Remaining", value=str(len(target_members)), inline=True)
        await confirmation_msg.edit(embed=status_embed)
        
        for i, member in enumerate(target_members):
            try:
                if action.lower() == "add":
                    await member.add_roles(role, reason=f"Mass role added by {ctx.author}")
                else:
                    await member.remove_roles(role, reason=f"Mass role removed by {ctx.author}")
                success_count += 1
            except discord.Forbidden:
                failed_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to {action_verb} role for {member}: {e}")
            
            # Update status every 10 members or on completion
            if (i + 1) % 10 == 0 or (i + 1) == len(target_members):
                status_embed = discord.Embed(
                    title=f"🔄 Mass Role {action_verb.title()}ing...",
                    description=f"Progress: {i + 1}/{len(target_members)}",
                    color=discord.Color.blue()
                )
                status_embed.add_field(name="✅ Successful", value=str(success_count), inline=True)
                status_embed.add_field(name="❌ Failed", value=str(failed_count), inline=True)
                status_embed.add_field(name="⏳ Remaining", value=str(len(target_members) - (i + 1)), inline=True)
                
                try:
                    await confirmation_msg.edit(embed=status_embed)
                except:
                    pass
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        # Final status
        final_embed = discord.Embed(
            title=f"✅ Mass Role {action_past.title()}!",
            description=f"Mass role operation completed.",
            color=discord.Color.green()
        )
        final_embed.add_field(name="🎭 Role", value=role.mention, inline=True)
        final_embed.add_field(name="🎯 Target", value=target_desc, inline=True)
        final_embed.add_field(name="👮 Moderator", value=ctx.author.mention, inline=True)
        final_embed.add_field(name="✅ Successful", value=str(success_count), inline=True)
        final_embed.add_field(name="❌ Failed", value=str(failed_count), inline=True)
        final_embed.add_field(name="📊 Success Rate", value=f"{(success_count/len(target_members)*100):.1f}%", inline=True)
        
        await confirmation_msg.edit(embed=final_embed)
        logger.info(f"{ctx.author} mass {action_past} role {role.name} for {success_count}/{len(target_members)} members in {ctx.guild.name}")

async def setup(bot):
    await bot.add_cog(Roles(bot))