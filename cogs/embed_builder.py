import discord
from discord.ext import commands
from discord import app_commands
import json
import logging
from utils.permissions import has_mod_permissions

logger = logging.getLogger(__name__)

class EmbedBuilder(commands.Cog):
    """Embed builder and message utilities"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name='embed')
    @commands.guild_only()
    async def create_embed(self, ctx):
        """Interactive embed builder"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use the embed builder.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎨 Embed Builder",
            description="Use the slash command `/embed` for interactive embed building!\n\nAlternatively, you can use these commands:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📝 Simple Message",
            value="`!say <message>` - Send a message as the bot",
            inline=False
        )
        
        embed.add_field(
            name="💬 Direct Message",
            value="`!dm @user <message>` - Send a DM to a user",
            inline=False
        )
        
        embed.add_field(
            name="🎨 Rich Embed",
            value="Use `/embed` for full interactive embed creation",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='say')
    @app_commands.describe(message="Message to send as the bot")
    @commands.guild_only()
    async def say_message(self, ctx, *, message: str):
        """Send a message as the bot"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Check message length
        if len(message) > 2000:
            embed = discord.Embed(
                title="❌ Message Too Long",
                description="Message cannot exceed 2000 characters.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Delete the command message if it's a prefix command
        if ctx.interaction is None:
            try:
                await ctx.message.delete()
            except:
                pass
        
        # Send the message
        try:
            await ctx.send(message)
            if ctx.interaction:
                # Send confirmation for slash command
                embed = discord.Embed(
                    title="✅ Message Sent",
                    description="Your message has been posted.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="❌ Failed to Send",
                description=f"Could not send the message: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name='dm')
    @app_commands.describe(
        user="User to send the DM to",
        message="Message to send"
    )
    @commands.guild_only()
    async def dm_user(self, ctx, user: discord.Member, *, message: str):
        """Send a direct message to a user"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Check message length
        if len(message) > 2000:
            embed = discord.Embed(
                title="❌ Message Too Long",
                description="Message cannot exceed 2000 characters.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Can't DM bots
        if user.bot:
            embed = discord.Embed(
                title="❌ Cannot DM Bots",
                description="Cannot send direct messages to bots.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Create DM embed
        dm_embed = discord.Embed(
            title=f"Message from {ctx.guild.name}",
            description=message,
            color=discord.Color.blue()
        )
        dm_embed.set_footer(text=f"Sent by {ctx.author} • {ctx.guild.name}")
        
        if ctx.guild.icon:
            dm_embed.set_thumbnail(url=ctx.guild.icon.url)
        
        # Try to send DM
        try:
            await user.send(embed=dm_embed)
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ DM Sent",
                description=f"Successfully sent DM to **{user.display_name}**.",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 Recipient", value=user.mention, inline=True)
            embed.add_field(name="👮 Sender", value=ctx.author.mention, inline=True)
            embed.add_field(name="📝 Preview", value=message[:100] + ("..." if len(message) > 100 else ""), inline=False)
            
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} sent DM to {user} from {ctx.guild.name}")
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ DM Failed",
                description=f"Could not send DM to **{user.display_name}**. They may have DMs disabled or have blocked the bot.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="❌ DM Failed",
                description=f"Failed to send DM: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))