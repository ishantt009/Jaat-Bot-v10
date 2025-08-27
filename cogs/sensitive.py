import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os
import asyncio

class SensitiveCommands(commands.Cog):
    """Sensitive information handling commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
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
        
        # Get bot owner
        try:
            owner = await self.bot.fetch_user(owner_id)
        except discord.NotFound:
            embed = discord.Embed(
                title="❌ Error",
                description="Bot owner not found. Please contact an administrator.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while processing your request. Please try again later.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create embed for the owner
        owner_embed = discord.Embed(
            title="🔒 Sensitive Information Received",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        owner_embed.add_field(
            name="👤 From User",
            value=f"**Username:** {interaction.user.name}\n"
                  f"**Display Name:** {interaction.user.display_name}\n"
                  f"**User ID:** {interaction.user.id}",
            inline=False
        )
        
        if interaction.guild:
            channel_name = getattr(interaction.channel, 'name', 'Unknown Channel')
            owner_embed.add_field(
                name="🏢 Server Information",
                value=f"**Server:** {interaction.guild.name}\n"
                      f"**Server ID:** {interaction.guild.id}\n"
                      f"**Channel:** {channel_name}",
                inline=False
            )
        else:
            owner_embed.add_field(
                name="📱 Location",
                value="Direct Message",
                inline=False
            )
        
        owner_embed.add_field(
            name="📝 Sensitive Information",
            value=f"```\n{information}\n```",
            inline=False
        )
        
        # Add user avatar if available
        if interaction.user.avatar:
            owner_embed.set_thumbnail(url=interaction.user.avatar.url)
        
        owner_embed.set_footer(
            text="Sensitive Information System",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        # Try to send to owner
        try:
            await owner.send(embed=owner_embed)
            
            # Confirm to user (without revealing the information)
            user_embed = discord.Embed(
                title="✅ Information Sent Successfully",
                description="Your sensitive information has been securely delivered to the bot owner. "
                           "They will review it and may contact you if necessary.",
                color=discord.Color.green()
            )
            
            user_embed.add_field(
                name="🔐 Privacy Notice",
                value="• Your information was sent directly to the bot owner\n"
                      "• This conversation is private and secure\n"
                      "• The bot owner may reach out to you if needed",
                inline=False
            )
            
            user_embed.set_footer(text="Your privacy is important to us")
            
            await interaction.response.send_message(embed=user_embed, ephemeral=True)
            
        except discord.Forbidden:
            # Owner has DMs disabled
            embed = discord.Embed(
                title="❌ Delivery Failed",
                description="Unable to deliver your information. The bot owner's DMs may be disabled. "
                           "Please try contacting them through other means.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            # Other error
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while sending your information. Please try again later "
                           "or contact the bot owner directly.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
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
                  "The information will be sent directly to the bot owner via private message.",
            inline=False
        )
        
        embed.add_field(
            name="🔐 Security Features",
            value="• Messages are sent privately (only you can see the response)\n"
                  "• Information goes directly to the bot owner\n"
                  "• No one else in the server can see your message\n"
                  "• Your user information is included for context",
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

async def setup(bot):
    """Setup function to add this cog to the bot"""
    await bot.add_cog(SensitiveCommands(bot))