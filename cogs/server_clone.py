import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional, Dict, List
import asyncio

logger = logging.getLogger(__name__)

class ServerClone(commands.Cog):
    """Cog for copying server channels and permissions between servers"""
    
    def __init__(self, bot):
        self.bot = bot
        
    async def map_overwrites(
        self, 
        source_overwrites: Dict, 
        target_guild: discord.Guild,
        role_mapping: Optional[Dict[str, discord.Role]] = None
    ) -> Dict:
        """
        Map permission overwrites from source to target guild
        
        Args:
            source_overwrites: Original overwrites from source channel
            target_guild: Target guild to map to
            role_mapping: Optional pre-built role name to role object mapping (case-insensitive)
            
        Returns:
            Dictionary of mapped overwrites for target guild
        """
        new_overwrites = {}
        
        # Build role mapping if not provided (case-insensitive)
        if role_mapping is None:
            role_mapping = {role.name.lower(): role for role in target_guild.roles}
        
        for entity, overwrite in source_overwrites.items():
            if isinstance(entity, discord.Role):
                # Handle @everyone role specially
                if entity.name == "@everyone":
                    new_overwrites[target_guild.default_role] = overwrite
                else:
                    # Match by role name (case-insensitive)
                    target_role = role_mapping.get(entity.name.lower())
                    if target_role:
                        new_overwrites[target_role] = overwrite
                    else:
                        logger.warning(f"Role '{entity.name}' not found in target guild")
                        
            elif isinstance(entity, discord.Member):
                # Check if member exists in target guild
                target_member = target_guild.get_member(entity.id)
                if target_member:
                    new_overwrites[target_member] = overwrite
                else:
                    logger.debug(f"Member {entity.name} not in target guild")
                    
        return new_overwrites
    
    async def copy_text_channel(
        self,
        source_channel: discord.TextChannel,
        target_guild: discord.Guild,
        category: Optional[discord.CategoryChannel] = None,
        role_mapping: Optional[Dict[str, discord.Role]] = None
    ) -> discord.TextChannel:
        """Copy a text channel to target guild"""
        overwrites = await self.map_overwrites(
            source_channel.overwrites,
            target_guild,
            role_mapping
        )
        
        kwargs = {
            'name': source_channel.name,
            'overwrites': overwrites,
            'category': category,
            'slowmode_delay': source_channel.slowmode_delay,
            'nsfw': source_channel.nsfw,
            'position': source_channel.position
        }
        if source_channel.topic:
            kwargs['topic'] = source_channel.topic
        
        new_channel = await target_guild.create_text_channel(**kwargs)
        
        logger.info(f"Copied text channel: {source_channel.name}")
        return new_channel
    
    async def copy_voice_channel(
        self,
        source_channel: discord.VoiceChannel,
        target_guild: discord.Guild,
        category: Optional[discord.CategoryChannel] = None,
        role_mapping: Optional[Dict[str, discord.Role]] = None
    ) -> discord.VoiceChannel:
        """Copy a voice channel to target guild"""
        overwrites = await self.map_overwrites(
            source_channel.overwrites,
            target_guild,
            role_mapping
        )
        
        new_channel = await target_guild.create_voice_channel(
            name=source_channel.name,
            overwrites=overwrites,
            category=category,
            bitrate=source_channel.bitrate,
            user_limit=source_channel.user_limit,
            position=source_channel.position
        )
        
        logger.info(f"Copied voice channel: {source_channel.name}")
        return new_channel
    
    async def copy_stage_channel(
        self,
        source_channel: discord.StageChannel,
        target_guild: discord.Guild,
        category: Optional[discord.CategoryChannel] = None,
        role_mapping: Optional[Dict[str, discord.Role]] = None
    ) -> discord.StageChannel:
        """Copy a stage channel to target guild"""
        overwrites = await self.map_overwrites(
            source_channel.overwrites,
            target_guild,
            role_mapping
        )
        
        new_channel = await target_guild.create_stage_channel(
            name=source_channel.name,
            overwrites=overwrites,
            category=category,
            position=source_channel.position
        )
        
        logger.info(f"Copied stage channel: {source_channel.name}")
        return new_channel
    
    async def copy_forum_channel(
        self,
        source_channel: discord.ForumChannel,
        target_guild: discord.Guild,
        category: Optional[discord.CategoryChannel] = None,
        role_mapping: Optional[Dict[str, discord.Role]] = None
    ) -> Optional[discord.ForumChannel]:
        """Copy a forum channel to target guild"""
        overwrites = await self.map_overwrites(
            source_channel.overwrites,
            target_guild,
            role_mapping
        )
        
        try:
            kwargs = {
                'name': source_channel.name,
                'overwrites': overwrites,
                'category': category,
                'position': source_channel.position,
                'nsfw': source_channel.nsfw
            }
            if source_channel.topic:
                kwargs['topic'] = source_channel.topic
            
            new_channel = await target_guild.create_forum(**kwargs)
            logger.info(f"Copied forum channel: {source_channel.name}")
            return new_channel
        except (AttributeError, TypeError):
            logger.warning(f"Forum channels not supported in this discord.py version")
            return None
    
    async def copy_category(
        self,
        source_category: discord.CategoryChannel,
        target_guild: discord.Guild,
        role_mapping: Optional[Dict[str, discord.Role]] = None,
        copy_channels: bool = True
    ) -> discord.CategoryChannel:
        """Copy a category and optionally its channels to target guild"""
        overwrites = await self.map_overwrites(
            source_category.overwrites,
            target_guild,
            role_mapping
        )
        
        new_category = await target_guild.create_category(
            name=source_category.name,
            overwrites=overwrites,
            position=source_category.position
        )
        
        logger.info(f"Copied category: {source_category.name}")
        
        # Copy channels within the category
        if copy_channels:
            for channel in source_category.channels:
                try:
                    if isinstance(channel, discord.TextChannel):
                        await self.copy_text_channel(channel, target_guild, new_category, role_mapping)
                    elif isinstance(channel, discord.VoiceChannel):
                        await self.copy_voice_channel(channel, target_guild, new_category, role_mapping)
                    elif isinstance(channel, discord.StageChannel):
                        await self.copy_stage_channel(channel, target_guild, new_category, role_mapping)
                    elif isinstance(channel, discord.ForumChannel):
                        await self.copy_forum_channel(channel, target_guild, new_category, role_mapping)
                    
                    # Add a small delay to avoid rate limits
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Failed to copy channel {channel.name}: {e}")
        
        return new_category
    
    @app_commands.command(name="copy-channel", description="Copy a channel to another server")
    @app_commands.describe(
        channel="The channel to copy",
        target_server_id="The ID of the target server"
    )
    async def copy_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.abc.GuildChannel,
        target_server_id: str
    ):
        """Copy a single channel to another server"""
        await interaction.response.defer()
        
        try:
            target_guild_id = int(target_server_id)
            target_guild = self.bot.get_guild(target_guild_id)
            
            if not target_guild:
                await interaction.followup.send("❌ Target server not found. Make sure the bot is in that server.")
                return
            
            # Check if user has permissions in both servers
            if not interaction.guild:
                await interaction.followup.send("❌ This command must be used in a server.")
                return
            
            # Fetch members to handle cache misses
            try:
                source_member = await interaction.guild.fetch_member(interaction.user.id)
            except discord.NotFound:
                await interaction.followup.send("❌ You are not in the source server.")
                return
            
            try:
                target_member = await target_guild.fetch_member(interaction.user.id)
            except discord.NotFound:
                await interaction.followup.send("❌ You are not in the target server.")
                return
            
            if not source_member.guild_permissions.administrator:
                await interaction.followup.send("❌ You need Administrator permissions in the source server.")
                return
                
            if not target_member.guild_permissions.administrator:
                await interaction.followup.send("❌ You need Administrator permissions in the target server.")
                return
            
            # Build case-insensitive role mapping
            role_mapping = {role.name.lower(): role for role in target_guild.roles}
            
            # Copy the channel based on type
            if isinstance(channel, discord.TextChannel):
                new_channel = await self.copy_text_channel(channel, target_guild, None, role_mapping)
            elif isinstance(channel, discord.VoiceChannel):
                new_channel = await self.copy_voice_channel(channel, target_guild, None, role_mapping)
            elif isinstance(channel, discord.StageChannel):
                new_channel = await self.copy_stage_channel(channel, target_guild, None, role_mapping)
            elif isinstance(channel, discord.ForumChannel):
                new_channel = await self.copy_forum_channel(channel, target_guild, None, role_mapping)
            elif isinstance(channel, discord.CategoryChannel):
                new_channel = await self.copy_category(channel, target_guild, role_mapping, copy_channels=True)
            else:
                await interaction.followup.send("❌ Unsupported channel type.")
                return
            
            if new_channel:
                await interaction.followup.send(
                    f"✅ Successfully copied **{channel.name}** to **{target_guild.name}**!\n"
                    f"New channel: {new_channel.mention if hasattr(new_channel, 'mention') else new_channel.name}"
                )
            else:
                await interaction.followup.send(
                    f"⚠️ Channel **{channel.name}** could not be copied (possibly unsupported channel type)."
                )
            
        except ValueError:
            await interaction.followup.send("❌ Invalid server ID. Please provide a valid numeric server ID.")
        except discord.Forbidden:
            await interaction.followup.send("❌ Bot lacks permissions to create channels in the target server.")
        except Exception as e:
            logger.error(f"Error copying channel: {e}")
            await interaction.followup.send(f"❌ An error occurred: {str(e)}")
    
    @app_commands.command(name="copy-all-channels", description="Copy all channels from another server to this server")
    @app_commands.describe(
        source_server_id="The ID of the source server to copy from"
    )
    async def copy_all_channels(
        self,
        interaction: discord.Interaction,
        source_server_id: str
    ):
        """Copy all channels from source server to target server"""
        await interaction.response.defer()
        
        try:
            source_guild_id = int(source_server_id)
            source_guild = self.bot.get_guild(source_guild_id)
            
            if not source_guild:
                await interaction.followup.send("❌ Source server not found. Make sure the bot is in that server.")
                return
            
            # Check permissions
            if not interaction.guild:
                await interaction.followup.send("❌ This command must be used in a server.")
                return
            
            target_guild = interaction.guild
            
            # Fetch members to handle cache misses
            try:
                source_member = await source_guild.fetch_member(interaction.user.id)
            except discord.NotFound:
                await interaction.followup.send("❌ You are not in the source server.")
                return
            
            try:
                target_member = await target_guild.fetch_member(interaction.user.id)
            except discord.NotFound:
                await interaction.followup.send("❌ You are not in the target server.")
                return
            
            if not source_member.guild_permissions.administrator:
                await interaction.followup.send("❌ You need Administrator permissions in the source server.")
                return
                
            if not target_member.guild_permissions.administrator:
                await interaction.followup.send("❌ You need Administrator permissions in the target server.")
                return
            
            # First, copy roles to preserve permissions
            existing_role_names = {role.name.lower() for role in target_guild.roles}
            sorted_roles = sorted(source_guild.roles, key=lambda r: r.position)
            copied_roles = 0
            new_roles = []
            
            for role in sorted_roles:
                if role.name == "@everyone" or role.name.lower() in existing_role_names:
                    continue
                try:
                    new_role = await target_guild.create_role(
                        name=role.name,
                        permissions=role.permissions,
                        colour=role.colour,
                        hoist=role.hoist,
                        mentionable=role.mentionable
                    )
                    new_roles.append((new_role, role.position))
                    copied_roles += 1
                    await asyncio.sleep(0.3)
                except Exception as e:
                    logger.error(f"Failed to copy role {role.name}: {e}")
            
            # Adjust role positions to preserve hierarchy
            if new_roles:
                try:
                    positions = {}
                    for new_role, original_position in new_roles:
                        positions[new_role] = original_position
                    await target_guild.edit_role_positions(positions)
                except Exception as e:
                    logger.warning(f"Failed to adjust role positions: {e}")
            
            # Refresh target guild to get newly created roles
            await target_guild.chunk()
            
            # Build case-insensitive role mapping with fresh role data
            role_mapping = {role.name.lower(): role for role in target_guild.roles}
            
            # Track statistics
            copied_categories = 0
            copied_text = 0
            copied_voice = 0
            copied_stage = 0
            copied_forum = 0
            failed = 0
            
            # First, copy categories
            for category in source_guild.categories:
                try:
                    await self.copy_category(category, target_guild, role_mapping, copy_channels=True)
                    copied_categories += 1
                    # Count channels in category
                    for channel in category.channels:
                        if isinstance(channel, discord.TextChannel):
                            copied_text += 1
                        elif isinstance(channel, discord.VoiceChannel):
                            copied_voice += 1
                        elif isinstance(channel, discord.StageChannel):
                            copied_stage += 1
                        elif isinstance(channel, discord.ForumChannel):
                            copied_forum += 1
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Failed to copy category {category.name}: {e}")
                    failed += 1
            
            # Then copy channels without categories
            for channel in source_guild.channels:
                if channel.category is None and not isinstance(channel, discord.CategoryChannel):
                    try:
                        if isinstance(channel, discord.TextChannel):
                            await self.copy_text_channel(channel, target_guild, None, role_mapping)
                            copied_text += 1
                        elif isinstance(channel, discord.VoiceChannel):
                            await self.copy_voice_channel(channel, target_guild, None, role_mapping)
                            copied_voice += 1
                        elif isinstance(channel, discord.StageChannel):
                            await self.copy_stage_channel(channel, target_guild, None, role_mapping)
                            copied_stage += 1
                        elif isinstance(channel, discord.ForumChannel):
                            await self.copy_forum_channel(channel, target_guild, None, role_mapping)
                            copied_forum += 1
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.error(f"Failed to copy channel {channel.name}: {e}")
                        failed += 1
            
            # Build summary
            summary = f"✅ **Copy Complete!**\n\n"
            summary += f"📊 **Summary:**\n"
            summary += f"• Roles: {copied_roles}\n"
            summary += f"• Categories: {copied_categories}\n"
            summary += f"• Text Channels: {copied_text}\n"
            summary += f"• Voice Channels: {copied_voice}\n"
            if copied_stage > 0:
                summary += f"• Stage Channels: {copied_stage}\n"
            if copied_forum > 0:
                summary += f"• Forum Channels: {copied_forum}\n"
            if failed > 0:
                summary += f"• Failed: {failed}\n"
            
            summary += f"\n✨ All roles and channels have been copied from **{source_guild.name}** to **{target_guild.name}**!"
            
            await interaction.followup.send(summary)
            
        except ValueError:
            await interaction.followup.send("❌ Invalid server ID. Please provide a valid numeric server ID.")
        except discord.Forbidden:
            await interaction.followup.send("❌ Bot lacks permissions in the target server.")
        except Exception as e:
            logger.error(f"Error copying all channels: {e}")
            await interaction.followup.send(f"❌ An error occurred: {str(e)}")
    
    @app_commands.command(name="copy-roles", description="Copy roles from this server to another")
    @app_commands.describe(
        target_server_id="The ID of the target server"
    )
    async def copy_roles(
        self,
        interaction: discord.Interaction,
        target_server_id: str
    ):
        """Copy all roles from source server to target server"""
        await interaction.response.defer()
        
        try:
            target_guild_id = int(target_server_id)
            target_guild = self.bot.get_guild(target_guild_id)
            
            if not target_guild:
                await interaction.followup.send("❌ Target server not found. Make sure the bot is in that server.")
                return
            
            # Check permissions
            if not interaction.guild:
                await interaction.followup.send("❌ This command must be used in a server.")
                return
            
            # Fetch members to handle cache misses
            try:
                source_member = await interaction.guild.fetch_member(interaction.user.id)
            except discord.NotFound:
                await interaction.followup.send("❌ You are not in the source server.")
                return
            
            try:
                target_member = await target_guild.fetch_member(interaction.user.id)
            except discord.NotFound:
                await interaction.followup.send("❌ You are not in the target server.")
                return
            
            if not source_member.guild_permissions.administrator:
                await interaction.followup.send("❌ You need Administrator permissions in the source server.")
                return
                
            if not target_member.guild_permissions.administrator:
                await interaction.followup.send("❌ You need Administrator permissions in the target server.")
                return
            
            source_guild = interaction.guild
            
            # Get existing role names in target to avoid duplicates
            existing_role_names = {role.name.lower() for role in target_guild.roles}
            
            copied = 0
            skipped = 0
            failed = 0
            
            # Sort roles by position (bottom to top)
            sorted_roles = sorted(source_guild.roles, key=lambda r: r.position)
            
            for role in sorted_roles:
                # Skip @everyone role and roles already in target
                if role.name == "@everyone":
                    continue
                    
                if role.name.lower() in existing_role_names:
                    skipped += 1
                    continue
                
                try:
                    await target_guild.create_role(
                        name=role.name,
                        permissions=role.permissions,
                        colour=role.colour,
                        hoist=role.hoist,
                        mentionable=role.mentionable
                    )
                    copied += 1
                    await asyncio.sleep(0.3)  # Rate limit protection
                except Exception as e:
                    logger.error(f"Failed to copy role {role.name}: {e}")
                    failed += 1
            
            summary = f"✅ **Role Copy Complete!**\n\n"
            summary += f"📊 **Summary:**\n"
            summary += f"• Copied: {copied}\n"
            summary += f"• Skipped (already exist): {skipped}\n"
            if failed > 0:
                summary += f"• Failed: {failed}\n"
            
            await interaction.followup.send(summary)
            
        except ValueError:
            await interaction.followup.send("❌ Invalid server ID. Please provide a valid numeric server ID.")
        except discord.Forbidden:
            await interaction.followup.send("❌ Bot lacks permissions in the target server.")
        except Exception as e:
            logger.error(f"Error copying roles: {e}")
            await interaction.followup.send(f"❌ An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(ServerClone(bot))
