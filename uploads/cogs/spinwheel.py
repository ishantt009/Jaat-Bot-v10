import discord
from discord.ext import commands
import random
import asyncio
import logging
from utils.permissions import has_mod_permissions

logger = logging.getLogger(__name__)

class SpinWheel(commands.Cog):
    """Spin wheel system for random user selection"""
    
    def __init__(self, bot):
        self.bot = bot
        self.wheels = {}  # Store wheels per guild {guild_id: {channel_id: [users]}}
    
    def get_wheel_key(self, guild_id, channel_id):
        """Get wheel key for guild and channel"""
        return f"{guild_id}_{channel_id}"
    
    def get_wheel(self, guild_id, channel_id):
        """Get wheel for specific guild and channel"""
        key = self.get_wheel_key(guild_id, channel_id)
        if key not in self.wheels:
            self.wheels[key] = []
        return self.wheels[key]
    
    def add_user_to_wheel(self, guild_id, channel_id, user):
        """Add user to wheel"""
        wheel = self.get_wheel(guild_id, channel_id)
        if user not in wheel:
            wheel.append(user)
            return True
        return False
    
    def remove_user_from_wheel(self, guild_id, channel_id, user):
        """Remove user from wheel"""
        wheel = self.get_wheel(guild_id, channel_id)
        if user in wheel:
            wheel.remove(user)
            return True
        return False
    
    def clear_wheel(self, guild_id, channel_id):
        """Clear all users from wheel"""
        key = self.get_wheel_key(guild_id, channel_id)
        if key in self.wheels:
            self.wheels[key] = []
    
    @commands.command(name='wheeladd', aliases=['wadd'])
    @commands.guild_only()
    async def add_to_wheel(self, ctx, *, users):
        """Add users to the spin wheel
        
        Usage: !wheeladd @user1 @user2 user3
        You can mention users or type their names/IDs
        """
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to manage the spin wheel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Parse users from mentions and text
        mentioned_users = ctx.message.mentions
        user_list = []
        
        # Add mentioned users
        for user in mentioned_users:
            if not user.bot:  # Skip bots
                user_list.append(user)
        
        # Parse text for additional users (names/IDs)
        user_text = users
        for mention in ctx.message.mentions:
            user_text = user_text.replace(mention.mention, "")
        
        # Split remaining text and try to find users
        remaining_names = [name.strip() for name in user_text.split() if name.strip()]
        
        for name in remaining_names:
            # Try to find user by ID
            if name.isdigit():
                try:
                    user = await self.bot.fetch_user(int(name))
                    member = ctx.guild.get_member(user.id)
                    if member and not member.bot:
                        user_list.append(member)
                    continue
                except:
                    pass
            
            # Try to find user by name or display name
            member = discord.utils.find(
                lambda m: m.name.lower() == name.lower() or 
                         m.display_name.lower() == name.lower(),
                ctx.guild.members
            )
            if member and not member.bot:
                user_list.append(member)
        
        if not user_list:
            embed = discord.Embed(
                title="❌ No Valid Users",
                description="No valid users found to add to the wheel. Make sure to mention users or use valid usernames/IDs.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Add users to wheel
        added_users = []
        already_in_wheel = []
        
        for user in user_list:
            if self.add_user_to_wheel(ctx.guild.id, ctx.channel.id, user):
                added_users.append(user)
            else:
                already_in_wheel.append(user)
        
        # Create response embed
        embed = discord.Embed(
            title="🎯 Users Added to Wheel",
            color=discord.Color.green()
        )
        
        if added_users:
            embed.add_field(
                name="✅ Added to Wheel",
                value="\n".join([f"• {user.display_name}" for user in added_users]),
                inline=False
            )
        
        if already_in_wheel:
            embed.add_field(
                name="⚠️ Already in Wheel",
                value="\n".join([f"• {user.display_name}" for user in already_in_wheel]),
                inline=False
            )
        
        wheel = self.get_wheel(ctx.guild.id, ctx.channel.id)
        embed.add_field(
            name="📊 Total Participants",
            value=f"{len(wheel)} users in the wheel",
            inline=False
        )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} added {len(added_users)} users to spin wheel in {ctx.guild.name}")
    
    @commands.command(name='wheelremove', aliases=['wremove'])
    @commands.guild_only()
    async def remove_from_wheel(self, ctx, *, users):
        """Remove users from the spin wheel
        
        Usage: !wheelremove @user1 @user2 user3
        """
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to manage the spin wheel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Parse users (similar logic to add command)
        mentioned_users = ctx.message.mentions
        user_list = []
        
        for user in mentioned_users:
            user_list.append(user)
        
        # Parse text for additional users
        user_text = users
        for mention in ctx.message.mentions:
            user_text = user_text.replace(mention.mention, "")
        
        remaining_names = [name.strip() for name in user_text.split() if name.strip()]
        
        for name in remaining_names:
            if name.isdigit():
                try:
                    user = await self.bot.fetch_user(int(name))
                    member = ctx.guild.get_member(user.id)
                    if member:
                        user_list.append(member)
                    continue
                except:
                    pass
            
            member = discord.utils.find(
                lambda m: m.name.lower() == name.lower() or 
                         m.display_name.lower() == name.lower(),
                ctx.guild.members
            )
            if member:
                user_list.append(member)
        
        if not user_list:
            embed = discord.Embed(
                title="❌ No Valid Users",
                description="No valid users found to remove from the wheel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Remove users from wheel
        removed_users = []
        not_in_wheel = []
        
        for user in user_list:
            if self.remove_user_from_wheel(ctx.guild.id, ctx.channel.id, user):
                removed_users.append(user)
            else:
                not_in_wheel.append(user)
        
        # Create response embed
        embed = discord.Embed(
            title="🎯 Users Removed from Wheel",
            color=discord.Color.orange()
        )
        
        if removed_users:
            embed.add_field(
                name="✅ Removed from Wheel",
                value="\n".join([f"• {user.display_name}" for user in removed_users]),
                inline=False
            )
        
        if not_in_wheel:
            embed.add_field(
                name="⚠️ Not in Wheel",
                value="\n".join([f"• {user.display_name}" for user in not_in_wheel]),
                inline=False
            )
        
        wheel = self.get_wheel(ctx.guild.id, ctx.channel.id)
        embed.add_field(
            name="📊 Total Participants",
            value=f"{len(wheel)} users in the wheel",
            inline=False
        )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} removed {len(removed_users)} users from spin wheel in {ctx.guild.name}")
    
    @commands.command(name='wheelclear', aliases=['wclear'])
    @commands.guild_only()
    async def clear_wheel_command(self, ctx):
        """Clear all users from the spin wheel"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to manage the spin wheel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        wheel = self.get_wheel(ctx.guild.id, ctx.channel.id)
        
        if not wheel:
            embed = discord.Embed(
                title="⚠️ Wheel Already Empty",
                description="The spin wheel is already empty.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        
        # Confirmation
        embed = discord.Embed(
            title="⚠️ Clear Wheel Confirmation",
            description=f"Are you sure you want to remove all **{len(wheel)}** users from the wheel?",
            color=discord.Color.orange()
        )
        embed.set_footer(text="React with ✅ to confirm or ❌ to cancel (15 seconds)")
        
        confirmation_msg = await ctx.send(embed=embed)
        await confirmation_msg.add_reaction("✅")
        await confirmation_msg.add_reaction("❌")
        
        def check(reaction, user):
            return (user == ctx.author and 
                   str(reaction.emoji) in ["✅", "❌"] and 
                   reaction.message.id == confirmation_msg.id)
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
            
            if str(reaction.emoji) == "❌":
                embed = discord.Embed(
                    title="❌ Clear Cancelled",
                    description="Wheel clear operation has been cancelled.",
                    color=discord.Color.red()
                )
                await confirmation_msg.edit(embed=embed)
                return
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏰ Timeout",
                description="Wheel clear confirmation timed out.",
                color=discord.Color.red()
            )
            await confirmation_msg.edit(embed=embed)
            return
        
        # Clear the wheel
        self.clear_wheel(ctx.guild.id, ctx.channel.id)
        
        embed = discord.Embed(
            title="✅ Wheel Cleared",
            description="All users have been removed from the spin wheel.",
            color=discord.Color.green()
        )
        await confirmation_msg.edit(embed=embed)
        logger.info(f"{ctx.author} cleared spin wheel in {ctx.guild.name}")
    
    @commands.command(name='wheellist', aliases=['wlist'])
    @commands.guild_only()
    async def list_wheel(self, ctx):
        """Show all users in the current spin wheel"""
        wheel = self.get_wheel(ctx.guild.id, ctx.channel.id)
        
        if not wheel:
            embed = discord.Embed(
                title="🎯 Spin Wheel - Empty",
                description="No users in the wheel. Use `!wheeladd @user` to add participants.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="🎯 Spin Wheel Participants",
            description=f"**{len(wheel)}** users ready to spin!",
            color=discord.Color.blue()
        )
        
        # Show users in chunks of 20
        user_chunks = [wheel[i:i+20] for i in range(0, len(wheel), 20)]
        
        for i, chunk in enumerate(user_chunks):
            field_name = "👥 Participants" if i == 0 else f"👥 Participants (continued {i+1})"
            user_list = "\n".join([f"{idx + (i*20) + 1}. {user.display_name}" for idx, user in enumerate(chunk)])
            embed.add_field(name=field_name, value=user_list, inline=False)
        
        embed.set_footer(text=f"Use !spin to randomly select a winner from {len(wheel)} participants")
        await ctx.send(embed=embed)
    
    @commands.command(name='spin')
    @commands.guild_only()
    async def spin_wheel(self, ctx):
        """Spin the wheel and select a random winner!"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to spin the wheel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        wheel = self.get_wheel(ctx.guild.id, ctx.channel.id)
        
        if not wheel:
            embed = discord.Embed(
                title="❌ Empty Wheel",
                description="The wheel is empty! Add users with `!wheeladd @user` first.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if len(wheel) == 1:
            winner = wheel[0]
            embed = discord.Embed(
                title="🎯 Spin Result",
                description=f"Only one participant, so {winner.mention} wins by default! 🎉",
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed)
            return
        
        # Create spinning animation
        spinning_embed = discord.Embed(
            title="🎯 Spinning the Wheel...",
            description="🎡 The wheel is spinning...",
            color=discord.Color.blue()
        )
        spinning_embed.add_field(
            name="🎯 Participants",
            value=f"{len(wheel)} users in the wheel",
            inline=False
        )
        
        message = await ctx.send(embed=spinning_embed)
        
        # Spinning animation
        spin_messages = [
            "🎡 The wheel is spinning...",
            "🌀 Spinning faster...",
            "⚡ Almost there...",
            "🎯 Slowing down...",
            "🔥 And the winner is..."
        ]
        
        for i, spin_text in enumerate(spin_messages):
            await asyncio.sleep(1)
            spinning_embed.description = spin_text
            try:
                await message.edit(embed=spinning_embed)
            except:
                pass
        
        # Select random winner
        winner = random.choice(wheel)
        
        # Create winner announcement
        winner_embed = discord.Embed(
            title="🎉 WINNER SELECTED! 🎉",
            description=f"🎊 **{winner.display_name}** is the winner! 🎊",
            color=discord.Color.gold()
        )
        
        winner_embed.add_field(
            name="🏆 Winner",
            value=winner.mention,
            inline=True
        )
        
        winner_embed.add_field(
            name="🎯 Selected From",
            value=f"{len(wheel)} participants",
            inline=True
        )
        
        winner_embed.add_field(
            name="🎲 Chance",
            value=f"1 in {len(wheel)} ({(1/len(wheel)*100):.1f}%)",
            inline=True
        )
        
        winner_embed.add_field(
            name="👑 Spun By",
            value=ctx.author.mention,
            inline=True
        )
        
        winner_embed.set_thumbnail(url=winner.avatar.url if winner.avatar else None)
        winner_embed.set_footer(text="Congratulations! 🎉")
        
        await message.edit(embed=winner_embed)
        
        # Send celebration message
        celebration_embed = discord.Embed(
            title="🎊 Congratulations!",
            description=f"{winner.mention} You're the lucky winner! 🎉",
            color=discord.Color.green()
        )
        await ctx.send(embed=celebration_embed)
        
        # Try to DM the winner
        try:
            dm_embed = discord.Embed(
                title="🎉 You Won!",
                description=f"Congratulations! You were selected as the winner in **{ctx.guild.name}**!",
                color=discord.Color.gold()
            )
            dm_embed.add_field(name="Server", value=ctx.guild.name, inline=True)
            dm_embed.add_field(name="Spun By", value=str(ctx.author), inline=True)
            await winner.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # User has DMs disabled
        
        logger.info(f"{ctx.author} spun wheel in {ctx.guild.name}, winner: {winner}")

async def setup(bot):
    await bot.add_cog(SpinWheel(bot))