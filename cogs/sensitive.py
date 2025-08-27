import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class SensitiveCommands(commands.Cog, name="🔒 Sensitive Information"):
    """Secure messaging system for private information"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'data/sensitive_config.json'
    
    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default config if file doesn't exist
            return {
                "routing_type": "dm",
                "channel_id": None,
                "guild_id": None
            }
        except Exception:
            return {
                "routing_type": "dm", 
                "channel_id": None,
                "guild_id": None
            }
    
    def save_config(self, config):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception:
            return False
    
    def is_owner(self, user_id):
        """Check if user is the bot owner"""
        owner_id = int(os.getenv('OWNER_ID', 0)) if os.getenv('OWNER_ID') else None
        return owner_id == user_id
    
    @app_commands.command(name='sensitive', description='Send private information securely to the bot owner')
    @app_commands.describe(
        information='Your private/sensitive information (this will be sent directly to the bot owner)'
    )
    async def sensitive_info(self, interaction: discord.Interaction, information: str):
        """Allow users to send sensitive information directly to bot owner"""
        
        # Check if bot owner is configured
        owner_id = int(os.getenv('OWNER_ID', 0)) if os.getenv('OWNER_ID') else None
        if not owner_id:
            embed = discord.Embed(
                title="❌ Service Unavailable",
                description="The sensitive information service is not configured. Please contact an administrator.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Load routing configuration
        config = self.load_config()
        
        # Create embed with sensitive information
        info_embed = discord.Embed(
            title="🔒 Sensitive Information Received",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        info_embed.add_field(
            name="👤 From User",
            value=f"**Username:** {interaction.user.name}\n"
                  f"**Display Name:** {interaction.user.display_name}\n"
                  f"**User ID:** {interaction.user.id}",
            inline=False
        )
        
        if interaction.guild:
            channel_name = getattr(interaction.channel, 'name', 'Unknown Channel')
            info_embed.add_field(
                name="🏢 Server Information",
                value=f"**Server:** {interaction.guild.name}\n"
                      f"**Server ID:** {interaction.guild.id}\n"
                      f"**Channel:** {channel_name}",
                inline=False
            )
        else:
            info_embed.add_field(
                name="📱 Location",
                value="Direct Message",
                inline=False
            )
        
        info_embed.add_field(
            name="📝 Sensitive Information",
            value=f"```\n{information}\n```",
            inline=False
        )
        
        # Add user avatar if available
        if interaction.user.avatar:
            info_embed.set_thumbnail(url=interaction.user.avatar.url)
        
        info_embed.set_footer(
            text="Sensitive Information System",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        # Route message based on configuration
        success = False
        destination = "unknown"
        
        try:
            if config['routing_type'] == 'channel' and config['channel_id']:
                # Send to configured channel
                channel = self.bot.get_channel(config['channel_id'])
                if channel:
                    # Check if bot has permissions
                    permissions = channel.permissions_for(channel.guild.me)
                    if permissions.send_messages and permissions.embed_links:
                        await channel.send(embed=info_embed)
                        success = True
                        destination = f"#{channel.name} in {channel.guild.name}"
                    else:
                        # Fallback to DM if no permissions
                        owner = await self.bot.fetch_user(owner_id)
                        await owner.send(embed=info_embed)
                        success = True
                        destination = "bot owner's DM (fallback due to channel permissions)"
                else:
                    # Channel not found, fallback to DM
                    owner = await self.bot.fetch_user(owner_id)
                    await owner.send(embed=info_embed)
                    success = True
                    destination = "bot owner's DM (fallback: channel not found)"
            else:
                # Send to owner's DM (default)
                owner = await self.bot.fetch_user(owner_id)
                await owner.send(embed=info_embed)
                success = True
                destination = "bot owner's DM"
            
            if success:
                # Confirm to user (without revealing the information)
                user_embed = discord.Embed(
                    title="✅ Information Sent Successfully",
                    description=f"Your sensitive information has been securely delivered to {destination}. "
                               "The bot owner will review it and may contact you if necessary.",
                    color=discord.Color.green()
                )
                
                user_embed.add_field(
                    name="🔐 Privacy Notice",
                    value="• Your information was sent securely to the bot owner\n"
                          "• This conversation is private and secure\n"
                          "• The bot owner may reach out to you if needed",
                    inline=False
                )
                
                user_embed.set_footer(text="Your privacy is important to us")
                await interaction.response.send_message(embed=user_embed, ephemeral=True)
                
        except discord.Forbidden:
            # Delivery failed due to permissions
            embed = discord.Embed(
                title="❌ Delivery Failed",
                description="Unable to deliver your information due to permission restrictions. "
                           "Please contact the bot owner directly or try again later.",
                color=discord.Color.red()
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.NotFound:
            # Owner or channel not found
            embed = discord.Embed(
                title="❌ Delivery Failed",
                description="Unable to find the configured destination for your message. "
                           "Please contact an administrator.",
                color=discord.Color.red()
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            # Other error
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while sending your information. Please try again later "
                           "or contact the bot owner directly.",
                color=discord.Color.red()
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name='sensitive-help', description='Get information about the sensitive information system')
    async def sensitive_help(self, interaction: discord.Interaction):
        """Provide help information about the sensitive command system"""
        
        # Check if bot owner is configured
        owner_id = int(os.getenv('OWNER_ID', 0)) if os.getenv('OWNER_ID') else None
        
        embed = discord.Embed(
            title="🔒 Sensitive Information System",
            description="This system allows you to securely send private information directly to the bot owner.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📋 How to Use",
            value="Use `/sensitive` followed by your private information. "
                  "The information will be sent to the bot owner based on their configuration.",
            inline=False
        )
        
        embed.add_field(
            name="🔐 Security Features",
            value="• Messages are sent privately (only you can see the response)\n"
                  "• Information goes to bot owner via DM or configured channel\n"
                  "• No one else in the server can see your message\n"
                  "• Your user information is included for context\n"
                  "• Smart fallback if configured channel unavailable",
            inline=False
        )
        
        embed.add_field(
            name="📝 What to Include",
            value="• Account issues or problems\n"
                  "• Bug reports with sensitive data\n"
                  "• Private concerns or questions\n"
                  "• Any information you don't want public",
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Important Notes",
            value="• Only use this for legitimate concerns\n"
                  "• The bot owner will receive your Discord username and ID\n"
                  "• Response time may vary depending on availability\n"
                  "• Don't share illegal content or spam",
            inline=False
        )
        
        embed.add_field(
            name="🔧 Routing System",
            value="• Bot owner can configure where messages are sent\n"
                  "• Options: Owner's DM or specific channel\n"
                  "• Auto-fallback to DM if channel has issues\n"
                  "• You'll be informed where your message was delivered",
            inline=False
        )
        
        if owner_id:
            embed.add_field(
                name="✅ Status",
                value="The sensitive information system is **online** and ready to use.",
                inline=False
            )
        else:
            embed.add_field(
                name="❌ Status",
                value="The sensitive information system is currently **unavailable**. Please contact an administrator.",
                inline=False
            )
        
        embed.set_footer(text="Use this system responsibly and only for legitimate purposes")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name='sensitive-config-dm', description='[OWNER ONLY] Configure sensitive messages to be sent to your DM')
    async def config_dm(self, interaction: discord.Interaction):
        """Configure sensitive messages to be sent to owner's DM"""
        logger.info(f"Config DM command called by {interaction.user.id}")
        
        if not self.is_owner(interaction.user.id):
            logger.warning(f"Non-owner {interaction.user.id} tried to use config DM command")
            embed = discord.Embed(
                title="❌ Access Denied",
                description="Only the bot owner can use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        config = self.load_config()
        config['routing_type'] = 'dm'
        config['channel_id'] = None
        config['guild_id'] = None
        
        if self.save_config(config):
            logger.info("Successfully updated config to DM mode")
            embed = discord.Embed(
                title="✅ Configuration Updated",
                description="Sensitive messages will now be sent to your DM.",
                color=discord.Color.green()
            )
        else:
            logger.error("Failed to save config to DM mode")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to save configuration. Please try again.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name='sensitive-config-channel', description='[OWNER ONLY] Configure sensitive messages to be sent to a specific channel')
    @app_commands.describe(channel='The channel where sensitive messages should be sent')
    async def config_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Configure sensitive messages to be sent to a specific channel"""
        logger.info(f"Config channel command called by {interaction.user.id} for channel {channel.id}")
        
        if not self.is_owner(interaction.user.id):
            logger.warning(f"Non-owner {interaction.user.id} tried to use config channel command")
            embed = discord.Embed(
                title="❌ Access Denied",
                description="Only the bot owner can use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if we're in a guild and bot has permissions in the channel
        if not interaction.guild:
            embed = discord.Embed(
                title="❌ Guild Required",
                description="This command must be used in a server, not in DMs.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        permissions = channel.permissions_for(interaction.guild.me)
        if not (permissions.send_messages and permissions.embed_links):
            logger.warning(f"Bot lacks permissions in channel {channel.id}")
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description=f"I don't have permission to send messages or embed links in {channel.mention}.\n"
                           "Please ensure I have the required permissions and try again.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        config = self.load_config()
        config['routing_type'] = 'channel'
        config['channel_id'] = channel.id
        config['guild_id'] = interaction.guild.id if interaction.guild else None
        
        if self.save_config(config):
            logger.info(f"Successfully updated config to channel mode: {channel.id}")
            embed = discord.Embed(
                title="✅ Configuration Updated",
                description=f"Sensitive messages will now be sent to {channel.mention}.",
                color=discord.Color.green()
            )
        else:
            logger.error(f"Failed to save config for channel {channel.id}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to save configuration. Please try again.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name='sensitive-config-status', description='[OWNER ONLY] View current sensitive message routing configuration')
    async def config_status(self, interaction: discord.Interaction):
        """Show current sensitive message routing configuration"""
        logger.info(f"Config status command called by {interaction.user.id}")
        
        if not self.is_owner(interaction.user.id):
            embed = discord.Embed(
                title="❌ Access Denied",
                description="Only the bot owner can use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        config = self.load_config()
        logger.info(f"Current config: {config}")
        
        embed = discord.Embed(
            title="🔧 Sensitive Message Configuration",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        if config['routing_type'] == 'dm':
            embed.add_field(
                name="📤 Current Routing",
                value="**Direct Message** to bot owner",
                inline=False
            )
        elif config['routing_type'] == 'channel' and config['channel_id']:
            try:
                channel = self.bot.get_channel(config['channel_id'])
                if channel:
                    embed.add_field(
                        name="📤 Current Routing",
                        value=f"**Channel:** {channel.mention}\n**Guild:** {channel.guild.name}",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="📤 Current Routing",
                        value="**Channel:** ⚠️ Channel not found (may have been deleted)",
                        inline=False
                    )
            except Exception:
                embed.add_field(
                    name="📤 Current Routing",
                    value="**Channel:** ⚠️ Error accessing channel",
                    inline=False
                )
        else:
            embed.add_field(
                name="📤 Current Routing",
                value="**Default:** Direct Message to bot owner",
                inline=False
            )
        
        embed.add_field(
            name="🛠️ Configuration Commands",
            value="`/sensitive-config-dm` - Route to your DM\n"
                  "`/sensitive-config-channel` - Route to a channel\n"
                  "`/sensitive-config-status` - View this status",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    """Setup function to add this cog to the bot"""
    await bot.add_cog(SensitiveCommands(bot))