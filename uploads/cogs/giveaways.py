import discord
from discord.ext import commands, tasks
import asyncio
import logging
import json
import os
import random
from datetime import datetime, timedelta
from utils.permissions import has_mod_permissions

logger = logging.getLogger(__name__)

class Giveaways(commands.Cog):
    """Giveaway system with react-to-win functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.giveaways = {}  # Store active giveaways {message_id: giveaway_data}
        self.giveaway_file = "giveaways.json"
        self.load_giveaways()
        self.check_giveaways.start()
    
    async def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.check_giveaways.cancel()
        self.save_giveaways()
    
    def load_giveaways(self):
        """Load active giveaways from file"""
        try:
            if os.path.exists(self.giveaway_file):
                with open(self.giveaway_file, 'r') as f:
                    data = json.load(f)
                    # Convert string keys back to int and datetime strings back to datetime objects
                    for msg_id, giveaway in data.items():
                        giveaway['end_time'] = datetime.fromisoformat(giveaway['end_time'])
                        self.giveaways[int(msg_id)] = giveaway
                logger.info(f"Loaded {len(self.giveaways)} active giveaways")
        except Exception as e:
            logger.error(f"Failed to load giveaways: {e}")
    
    def save_giveaways(self):
        """Save active giveaways to file"""
        try:
            # Convert datetime objects to strings for JSON serialization
            data = {}
            for msg_id, giveaway in self.giveaways.items():
                giveaway_copy = giveaway.copy()
                giveaway_copy['end_time'] = giveaway['end_time'].isoformat()
                data[str(msg_id)] = giveaway_copy
            
            with open(self.giveaway_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save giveaways: {e}")
    
    def parse_duration(self, duration_str):
        """Parse duration string like '1h', '30m', '2d' into timedelta"""
        duration_str = duration_str.lower().strip()
        
        # Extract number and unit
        if duration_str[-1] == 's':
            return timedelta(seconds=int(duration_str[:-1]))
        elif duration_str[-1] == 'm':
            return timedelta(minutes=int(duration_str[:-1]))
        elif duration_str[-1] == 'h':
            return timedelta(hours=int(duration_str[:-1]))
        elif duration_str[-1] == 'd':
            return timedelta(days=int(duration_str[:-1]))
        elif duration_str[-1] == 'w':
            return timedelta(weeks=int(duration_str[:-1]))
        else:
            # Default to minutes if no unit specified
            return timedelta(minutes=int(duration_str))
    
    def format_time_left(self, end_time):
        """Format time left until giveaway ends"""
        now = datetime.now()
        if end_time <= now:
            return "Ended"
        
        time_left = end_time - now
        days = time_left.days
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    @commands.command(name='gstart', aliases=['giveaway'])
    @commands.guild_only()
    async def start_giveaway(self, ctx, duration, winners: int, *, prize):
        """Start a new giveaway
        
        Usage: !gstart <duration> <winners> <prize>
        Example: !gstart 1h 3 Discord Nitro
        Duration formats: 30s, 5m, 2h, 1d, 1w
        """
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to start giveaways.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Validate winners count
        if winners < 1:
            embed = discord.Embed(
                title="❌ Invalid Winner Count",
                description="Number of winners must be at least 1.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if winners > 20:
            embed = discord.Embed(
                title="❌ Invalid Winner Count",
                description="Number of winners cannot exceed 20.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Parse duration
        try:
            duration_delta = self.parse_duration(duration)
            if duration_delta.total_seconds() < 10:
                raise ValueError("Duration too short")
            if duration_delta.total_seconds() > 604800:  # 1 week
                raise ValueError("Duration too long")
        except (ValueError, IndexError):
            embed = discord.Embed(
                title="❌ Invalid Duration",
                description="Please use a valid duration format: 30s, 5m, 2h, 1d, 1w\nMinimum: 10 seconds, Maximum: 1 week",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Calculate end time
        end_time = datetime.now() + duration_delta
        
        # Create giveaway embed
        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"**{prize}**",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="📝 Prize",
            value=prize,
            inline=True
        )
        
        embed.add_field(
            name="🏆 Winners",
            value=f"{winners} winner{'s' if winners > 1 else ''}",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Time Left",
            value=self.format_time_left(end_time),
            inline=True
        )
        
        embed.add_field(
            name="👑 Host",
            value=ctx.author.mention,
            inline=True
        )
        
        embed.add_field(
            name="🎯 Participants",
            value="0",
            inline=True
        )
        
        embed.add_field(
            name="📅 Ends At",
            value=f"<t:{int(end_time.timestamp())}:F>",
            inline=True
        )
        
        embed.set_footer(text="React with 🎉 to enter the giveaway!")
        embed.timestamp = end_time
        
        # Send the giveaway message
        giveaway_msg = await ctx.send(embed=embed)
        await giveaway_msg.add_reaction("🎉")
        
        # Store giveaway data
        self.giveaways[giveaway_msg.id] = {
            'channel_id': ctx.channel.id,
            'guild_id': ctx.guild.id,
            'host_id': ctx.author.id,
            'prize': prize,
            'winners': winners,
            'end_time': end_time,
            'participants': [],
            'ended': False
        }
        
        # Save to file
        self.save_giveaways()
        
        # Delete the command message
        try:
            await ctx.message.delete()
        except:
            pass
        
        logger.info(f"Giveaway started by {ctx.author} in {ctx.guild.name}: {prize}")
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle reaction additions for giveaway participation"""
        # Ignore bot reactions
        if user.bot:
            return
        
        # Check if this is a giveaway message
        if reaction.message.id not in self.giveaways:
            return
        
        # Check if it's the correct emoji
        if str(reaction.emoji) != "🎉":
            return
        
        giveaway = self.giveaways[reaction.message.id]
        
        # Check if giveaway has ended
        if giveaway['ended'] or datetime.now() >= giveaway['end_time']:
            return
        
        # Add user to participants if not already there
        if user.id not in giveaway['participants']:
            giveaway['participants'].append(user.id)
            self.save_giveaways()
            
            # Update the embed with new participant count
            await self.update_giveaway_embed(reaction.message, giveaway)
    
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """Handle reaction removals for giveaway participation"""
        # Ignore bot reactions
        if user.bot:
            return
        
        # Check if this is a giveaway message
        if reaction.message.id not in self.giveaways:
            return
        
        # Check if it's the correct emoji
        if str(reaction.emoji) != "🎉":
            return
        
        giveaway = self.giveaways[reaction.message.id]
        
        # Check if giveaway has ended
        if giveaway['ended']:
            return
        
        # Remove user from participants
        if user.id in giveaway['participants']:
            giveaway['participants'].remove(user.id)
            self.save_giveaways()
            
            # Update the embed with new participant count
            await self.update_giveaway_embed(reaction.message, giveaway)
    
    async def update_giveaway_embed(self, message, giveaway):
        """Update the giveaway embed with current information"""
        try:
            embed = message.embeds[0]
            
            # Update participant count
            for i, field in enumerate(embed.fields):
                if field.name == "🎯 Participants":
                    embed.set_field_at(i, name="🎯 Participants", value=str(len(giveaway['participants'])), inline=True)
                elif field.name == "⏰ Time Left":
                    embed.set_field_at(i, name="⏰ Time Left", value=self.format_time_left(giveaway['end_time']), inline=True)
            
            await message.edit(embed=embed)
        except Exception as e:
            logger.error(f"Failed to update giveaway embed: {e}")
    
    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        """Check for ended giveaways and process them"""
        now = datetime.now()
        ended_giveaways = []
        
        for msg_id, giveaway in self.giveaways.items():
            if not giveaway['ended'] and now >= giveaway['end_time']:
                ended_giveaways.append(msg_id)
        
        for msg_id in ended_giveaways:
            await self.end_giveaway(msg_id)
    
    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        """Wait until bot is ready before starting the task"""
        await self.bot.wait_until_ready()
    
    async def end_giveaway(self, message_id):
        """End a giveaway and select winners"""
        if message_id not in self.giveaways:
            return
        
        giveaway = self.giveaways[message_id]
        giveaway['ended'] = True
        
        try:
            # Get the channel and message
            channel = self.bot.get_channel(giveaway['channel_id'])
            if not channel:
                logger.error(f"Could not find channel for giveaway {message_id}")
                return
            
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                logger.error(f"Could not find message for giveaway {message_id}")
                del self.giveaways[message_id]
                self.save_giveaways()
                return
            
            # Get valid participants (users still in the server)
            guild = channel.guild
            valid_participants = []
            for user_id in giveaway['participants']:
                member = guild.get_member(user_id)
                if member:
                    valid_participants.append(member)
            
            # Create ended embed
            embed = discord.Embed(
                title="🎉 GIVEAWAY ENDED 🎉",
                description=f"**{giveaway['prize']}**",
                color=discord.Color.red()
            )
            
            # Select winners
            winners_list = []
            if len(valid_participants) == 0:
                winner_text = "No valid participants"
            elif len(valid_participants) < giveaway['winners']:
                # Not enough participants, everyone wins
                winners_list = valid_participants
                winner_text = "Everyone wins! (Not enough participants)"
            else:
                # Select random winners
                winners_list = random.sample(valid_participants, giveaway['winners'])
                winner_text = "\n".join([f"🎊 {winner.mention}" for winner in winners_list])
            
            embed.add_field(
                name="🏆 Winners",
                value=winner_text,
                inline=False
            )
            
            embed.add_field(
                name="📝 Prize",
                value=giveaway['prize'],
                inline=True
            )
            
            embed.add_field(
                name="👑 Host",
                value=f"<@{giveaway['host_id']}>",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Total Participants",
                value=str(len(giveaway['participants'])),
                inline=True
            )
            
            embed.set_footer(text="Giveaway has ended!")
            embed.timestamp = datetime.now()
            
            # Update the message
            await message.edit(embed=embed)
            
            # Announce winners
            if winners_list:
                winner_mentions = " ".join([winner.mention for winner in winners_list])
                congrats_embed = discord.Embed(
                    title="🎊 Congratulations!",
                    description=f"{winner_mentions}\n\nYou won **{giveaway['prize']}**!",
                    color=discord.Color.green()
                )
                await channel.send(embed=congrats_embed)
                
                # Try to DM winners
                for winner in winners_list:
                    try:
                        dm_embed = discord.Embed(
                            title="🎉 You Won a Giveaway!",
                            description=f"Congratulations! You won **{giveaway['prize']}** in {guild.name}!",
                            color=discord.Color.green()
                        )
                        dm_embed.add_field(name="Server", value=guild.name, inline=True)
                        dm_embed.add_field(name="Host", value=f"<@{giveaway['host_id']}>", inline=True)
                        await winner.send(embed=dm_embed)
                    except discord.Forbidden:
                        pass  # User has DMs disabled
            
            logger.info(f"Giveaway ended: {giveaway['prize']} - {len(winners_list)} winners")
            
        except Exception as e:
            logger.error(f"Error ending giveaway {message_id}: {e}")
        
        # Clean up
        del self.giveaways[message_id]
        self.save_giveaways()
    
    @commands.command(name='gend')
    @commands.guild_only()
    async def end_giveaway_early(self, ctx, message_id: int):
        """End a giveaway early
        
        Usage: !gend <message_id>
        """
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to end giveaways.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if message_id not in self.giveaways:
            embed = discord.Embed(
                title="❌ Giveaway Not Found",
                description="No active giveaway found with that message ID.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        giveaway = self.giveaways[message_id]
        
        # Check if user is host or has admin permissions
        if (ctx.author.id != giveaway['host_id'] and 
            not ctx.author.guild_permissions.administrator and 
            ctx.author != ctx.guild.owner):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only the giveaway host or administrators can end this giveaway.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # End the giveaway
        await self.end_giveaway(message_id)
        
        embed = discord.Embed(
            title="✅ Giveaway Ended",
            description="The giveaway has been ended early.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='greroll')
    @commands.guild_only()
    async def reroll_giveaway(self, ctx, message_id: int):
        """Reroll winners for an ended giveaway
        
        Usage: !greroll <message_id>
        """
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to reroll giveaways.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Try to find the message
            message = None
            for channel in ctx.guild.text_channels:
                try:
                    message = await channel.fetch_message(message_id)
                    break
                except discord.NotFound:
                    continue
                except discord.Forbidden:
                    continue
            
            if not message or not message.embeds:
                embed = discord.Embed(
                    title="❌ Message Not Found",
                    description="Could not find a giveaway message with that ID.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Check if it's a giveaway message
            embed_obj = message.embeds[0]
            if "GIVEAWAY" not in embed_obj.title:
                embed = discord.Embed(
                    title="❌ Not a Giveaway",
                    description="That message is not a giveaway.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Get participants from reactions
            participants = []
            for reaction in message.reactions:
                if str(reaction.emoji) == "🎉":
                    async for user in reaction.users():
                        if not user.bot and user.id != self.bot.user.id:
                            member = ctx.guild.get_member(user.id)
                            if member:
                                participants.append(member)
                    break
            
            if not participants:
                embed = discord.Embed(
                    title="❌ No Participants",
                    description="No valid participants found for this giveaway.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Extract prize and winner count from embed
            prize = embed_obj.description.replace("**", "")
            winners_field = next((field for field in embed_obj.fields if "Winners" in field.name), None)
            if winners_field:
                winner_count = int(winners_field.value.split()[0])
            else:
                winner_count = 1
            
            # Select new winners
            if len(participants) < winner_count:
                new_winners = participants
                winner_text = "Everyone wins! (Not enough participants)"
            else:
                new_winners = random.sample(participants, winner_count)
                winner_text = "\n".join([f"🎊 {winner.mention}" for winner in new_winners])
            
            # Update embed
            new_embed = discord.Embed(
                title="🔄 GIVEAWAY REROLLED 🔄",
                description=f"**{prize}**",
                color=discord.Color.purple()
            )
            
            new_embed.add_field(
                name="🏆 New Winners",
                value=winner_text,
                inline=False
            )
            
            new_embed.add_field(
                name="📝 Prize",
                value=prize,
                inline=True
            )
            
            new_embed.add_field(
                name="🎯 Total Participants",
                value=str(len(participants)),
                inline=True
            )
            
            new_embed.set_footer(text="Giveaway has been rerolled!")
            new_embed.timestamp = datetime.now()
            
            await message.edit(embed=new_embed)
            
            # Announce new winners
            if new_winners:
                winner_mentions = " ".join([winner.mention for winner in new_winners])
                congrats_embed = discord.Embed(
                    title="🔄 New Winners Selected!",
                    description=f"{winner_mentions}\n\nYou won **{prize}** (Rerolled)!",
                    color=discord.Color.purple()
                )
                await message.channel.send(embed=congrats_embed)
            
            confirm_embed = discord.Embed(
                title="✅ Giveaway Rerolled",
                description="New winners have been selected!",
                color=discord.Color.green()
            )
            await ctx.send(embed=confirm_embed)
            
            logger.info(f"Giveaway rerolled by {ctx.author}: {prize}")
            
        except Exception as e:
            logger.error(f"Error rerolling giveaway: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while rerolling the giveaway.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='glist')
    @commands.guild_only()
    async def list_giveaways(self, ctx):
        """List all active giveaways in the server"""
        guild_giveaways = [
            (msg_id, giveaway) for msg_id, giveaway in self.giveaways.items()
            if giveaway['guild_id'] == ctx.guild.id and not giveaway['ended']
        ]
        
        if not guild_giveaways:
            embed = discord.Embed(
                title="📋 Active Giveaways",
                description="No active giveaways in this server.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="📋 Active Giveaways",
            description=f"Found {len(guild_giveaways)} active giveaway{'s' if len(guild_giveaways) > 1 else ''}",
            color=discord.Color.blue()
        )
        
        for msg_id, giveaway in guild_giveaways[:10]:  # Limit to 10 giveaways
            channel = self.bot.get_channel(giveaway['channel_id'])
            channel_name = channel.name if channel else "Unknown Channel"
            
            embed.add_field(
                name=f"🎁 {giveaway['prize'][:50]}{'...' if len(giveaway['prize']) > 50 else ''}",
                value=f"**Channel:** #{channel_name}\n"
                      f"**Time Left:** {self.format_time_left(giveaway['end_time'])}\n"
                      f"**Participants:** {len(giveaway['participants'])}\n"
                      f"**Message ID:** {msg_id}",
                inline=True
            )
        
        if len(guild_giveaways) > 10:
            embed.set_footer(text=f"Showing first 10 of {len(guild_giveaways)} giveaways")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Giveaways(bot))