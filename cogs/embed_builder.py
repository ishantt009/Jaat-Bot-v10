import discord
from discord.ext import commands
from discord import app_commands
import json
import logging
from typing import Optional
from utils.permissions import has_mod_permissions

logger = logging.getLogger(__name__)

class EmbedBuilder(commands.Cog):
    """Complete embed builder system for creating custom embeds"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name='embed')
    @app_commands.describe(
        channel="Channel to send the embed to",
        title="Embed title",
        description="Embed description",
        color="Embed color (hex code like #ff0000)",
        image="Image URL",
        thumbnail="Thumbnail URL",
        footer="Footer text",
        author="Author name"
    )
    @commands.guild_only()
    async def create_embed(
        self, 
        ctx, 
        channel: Optional[discord.TextChannel] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        image: Optional[str] = None,
        thumbnail: Optional[str] = None,
        footer: Optional[str] = None,
        author: Optional[str] = None
    ):
        """Create and send a custom embed"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to create embeds.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Default values
        if not title and not description:
            title = "Custom Embed"
            description = "This is a custom embed created with the embed builder!"
        
        target_channel = channel or ctx.channel
        
        # Create embed
        embed_color = discord.Color.blue()
        if color:
            try:
                # Remove # if present and convert hex to int
                color_hex = color.lstrip('#')
                embed_color = discord.Color(int(color_hex, 16))
            except ValueError:
                embed_color = discord.Color.blue()
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=embed_color
        )
        
        # Add optional components
        if author:
            embed.set_author(name=author)
        
        if image:
            try:
                embed.set_image(url=image)
            except:
                pass
        
        if thumbnail:
            try:
                embed.set_thumbnail(url=thumbnail)
            except:
                pass
        
        if footer:
            embed.set_footer(text=footer)
        
        # Send embed
        try:
            await target_channel.send(embed=embed)
            
            # Confirmation
            if target_channel != ctx.channel:
                confirm_embed = discord.Embed(
                    title="✅ Embed Sent",
                    description=f"Custom embed sent to {target_channel.mention}",
                    color=discord.Color.green()
                )
                await ctx.send(embed=confirm_embed, ephemeral=True)
            
            logger.info(f"{ctx.author} created embed in {target_channel.name} in {ctx.guild.name}")
            
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Permission Error",
                description=f"I don't have permission to send messages in {target_channel.mention}",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed, ephemeral=True)
    
    @commands.hybrid_command(name='embedjson')
    @app_commands.describe(
        channel="Channel to send the embed to",
        json_data="JSON data for the embed"
    )
    @commands.guild_only()
    async def embed_from_json(
        self, 
        ctx, 
        channel: Optional[discord.TextChannel] = None,
        *, 
        json_data: str
    ):
        """Create embed from JSON data (advanced users)"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to create embeds.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        target_channel = channel or ctx.channel
        
        try:
            # Parse JSON
            embed_data = json.loads(json_data)
            
            # Create embed from JSON
            embed = discord.Embed.from_dict(embed_data)
            
            # Send embed
            await target_channel.send(embed=embed)
            
            # Confirmation
            if target_channel != ctx.channel:
                confirm_embed = discord.Embed(
                    title="✅ Embed Sent",
                    description=f"JSON embed sent to {target_channel.mention}",
                    color=discord.Color.green()
                )
                await ctx.send(embed=confirm_embed, ephemeral=True)
            
            logger.info(f"{ctx.author} created JSON embed in {target_channel.name} in {ctx.guild.name}")
            
        except json.JSONDecodeError:
            error_embed = discord.Embed(
                title="❌ Invalid JSON",
                description="The provided JSON data is invalid. Please check your syntax.",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed, ephemeral=True)
        
        except discord.HTTPException as e:
            error_embed = discord.Embed(
                title="❌ Embed Error",
                description=f"Failed to create embed: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed, ephemeral=True)
        
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Permission Error",
                description=f"I don't have permission to send messages in {target_channel.mention}",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed, ephemeral=True)
    
    @commands.hybrid_command(name='embedfields')
    @app_commands.describe(
        channel="Channel to send the embed to",
        title="Embed title",
        description="Embed description",
        field1="Field 1: name|value|inline(true/false)",
        field2="Field 2: name|value|inline(true/false)",
        field3="Field 3: name|value|inline(true/false)"
    )
    @commands.guild_only()
    async def embed_with_fields(
        self,
        ctx,
        channel: Optional[discord.TextChannel] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        field1: Optional[str] = None,
        field2: Optional[str] = None,
        field3: Optional[str] = None
    ):
        """Create embed with custom fields"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to create embeds.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        target_channel = channel or ctx.channel
        
        # Create base embed
        embed = discord.Embed(
            title=title or "Custom Embed with Fields",
            description=description or "Embed created with custom fields",
            color=discord.Color.blue()
        )
        
        # Add fields
        fields = [field1, field2, field3]
        for field_data in fields:
            if field_data:
                try:
                    parts = field_data.split('|')
                    if len(parts) >= 2:
                        name = parts[0]
                        value = parts[1]
                        inline = parts[2].lower() == 'true' if len(parts) > 2 else False
                        embed.add_field(name=name, value=value, inline=inline)
                except:
                    continue
        
        # Send embed
        try:
            await target_channel.send(embed=embed)
            
            # Confirmation
            if target_channel != ctx.channel:
                confirm_embed = discord.Embed(
                    title="✅ Embed Sent",
                    description=f"Field embed sent to {target_channel.mention}",
                    color=discord.Color.green()
                )
                await ctx.send(embed=confirm_embed, ephemeral=True)
            
            logger.info(f"{ctx.author} created field embed in {target_channel.name} in {ctx.guild.name}")
            
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Permission Error",
                description=f"I don't have permission to send messages in {target_channel.mention}",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed, ephemeral=True)
    
    @commands.hybrid_command(name='embedtemplate')
    @commands.guild_only()
    async def embed_template(self, ctx):
        """Show embed creation templates and examples"""
        embed = discord.Embed(
            title="🎨 Embed Builder Templates",
            description="Here are different ways to create custom embeds:",
            color=discord.Color.blue()
        )
        
        # Basic embed command
        embed.add_field(
            name="📝 Basic Embed",
            value="`/embed title:My Title description:My Description color:#ff0000`",
            inline=False
        )
        
        # With images
        embed.add_field(
            name="🖼️ With Images",
            value="`/embed title:Cool Image image:https://example.com/image.png thumbnail:https://example.com/thumb.png`",
            inline=False
        )
        
        # With fields
        embed.add_field(
            name="📋 With Fields",
            value="`/embedfields title:My Title field1:Name1|Value1|true field2:Name2|Value2|false`",
            inline=False
        )
        
        # JSON example
        json_example = """{
  "title": "JSON Embed",
  "description": "Advanced embed from JSON",
  "color": 3447003,
  "fields": [
    {"name": "Field 1", "value": "Value 1", "inline": true},
    {"name": "Field 2", "value": "Value 2", "inline": true}
  ],
  "footer": {"text": "Footer text"}
}"""
        
        embed.add_field(
            name="⚙️ JSON Embed (Advanced)",
            value=f"```json\n{json_example[:200]}...```\nUse `/embedjson` with this JSON",
            inline=False
        )
        
        # Color codes
        embed.add_field(
            name="🎨 Color Codes",
            value="Red: `#ff0000` | Green: `#00ff00` | Blue: `#0000ff` | Orange: `#ffa500`",
            inline=False
        )
        
        embed.set_footer(text="💡 All embed commands require moderator permissions")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='say')
    @app_commands.describe(
        channel="Channel to send the message to",
        message="Message content to send"
    )
    @commands.guild_only()
    async def say_message(
        self,
        ctx,
        channel: Optional[discord.TextChannel] = None,
        *,
        message: str
    ):
        """Send a message as the bot"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use the say command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        target_channel = channel or ctx.channel
        
        try:
            await target_channel.send(message)
            
            # Confirmation if different channel
            if target_channel != ctx.channel:
                confirm_embed = discord.Embed(
                    title="✅ Message Sent",
                    description=f"Message sent to {target_channel.mention}",
                    color=discord.Color.green()
                )
                await ctx.send(embed=confirm_embed, ephemeral=True)
            
            logger.info(f"{ctx.author} used say command in {target_channel.name} in {ctx.guild.name}")
            
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Permission Error",
                description=f"I don't have permission to send messages in {target_channel.mention}",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))