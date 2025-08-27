import discord
from discord.ext import commands
from discord import app_commands
import json
import logging
import asyncio
import os
from datetime import datetime
from typing import Optional
from utils.permissions import has_mod_permissions

logger = logging.getLogger(__name__)

class EmbedData:
    def __init__(self):
        self.title = None
        self.description = None
        self.color = 0x2F3136
        self.footer = None
        self.footer_icon = None
        self.author = None
        self.author_icon = None
        self.thumbnail = None
        self.image = None
        self.fields = []
        self.timestamp = False
    
    def to_embed(self):
        embed = discord.Embed(
            title=self.title,
            description=self.description,
            color=self.color
        )
        
        if self.footer:
            embed.set_footer(text=self.footer, icon_url=self.footer_icon)
        
        if self.author:
            embed.set_author(name=self.author, icon_url=self.author_icon)
        
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        
        if self.image:
            embed.set_image(url=self.image)
        
        for field in self.fields:
            embed.add_field(
                name=field['name'],
                value=field['value'],
                inline=field.get('inline', True)
            )
        
        if self.timestamp:
            embed.timestamp = datetime.utcnow()
        
        return embed

class EmbedTitleModal(discord.ui.Modal, title='Embed Title & Description'):
    def __init__(self, embed_data: EmbedData):
        super().__init__()
        self.embed_data = embed_data
        
        self.title_input = discord.ui.TextInput(
            label='Title',
            placeholder='Enter embed title (optional)',
            default=self.embed_data.title or '',
            max_length=256,
            required=False
        )
        
        self.description_input = discord.ui.TextInput(
            label='Description',
            placeholder='Enter embed description (optional)',
            default=self.embed_data.description or '',
            style=discord.TextStyle.paragraph,
            max_length=4000,
            required=False
        )
        
        self.add_item(self.title_input)
        self.add_item(self.description_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        self.embed_data.title = self.title_input.value.strip() or None
        self.embed_data.description = self.description_input.value.strip() or None
        await interaction.response.defer()

class EmbedAuthorModal(discord.ui.Modal, title='Embed Author'):
    def __init__(self, embed_data: EmbedData):
        super().__init__()
        self.embed_data = embed_data
        
        self.author_input = discord.ui.TextInput(
            label='Author Name',
            placeholder='Enter author name (optional)',
            default=self.embed_data.author or '',
            max_length=256,
            required=False
        )
        
        self.author_icon_input = discord.ui.TextInput(
            label='Author Icon URL',
            placeholder='Enter author icon URL (optional)',
            default=self.embed_data.author_icon or '',
            max_length=1000,
            required=False
        )
        
        self.add_item(self.author_input)
        self.add_item(self.author_icon_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        self.embed_data.author = self.author_input.value.strip() or None
        self.embed_data.author_icon = self.author_icon_input.value.strip() or None
        await interaction.response.defer()

class EmbedFooterModal(discord.ui.Modal, title='Embed Footer'):
    def __init__(self, embed_data: EmbedData):
        super().__init__()
        self.embed_data = embed_data
        
        self.footer_input = discord.ui.TextInput(
            label='Footer Text',
            placeholder='Enter footer text (optional)',
            default=self.embed_data.footer or '',
            max_length=2048,
            required=False
        )
        
        self.footer_icon_input = discord.ui.TextInput(
            label='Footer Icon URL',
            placeholder='Enter footer icon URL (optional)',
            default=self.embed_data.footer_icon or '',
            max_length=1000,
            required=False
        )
        
        self.add_item(self.footer_input)
        self.add_item(self.footer_icon_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        self.embed_data.footer = self.footer_input.value.strip() or None
        self.embed_data.footer_icon = self.footer_icon_input.value.strip() or None
        await interaction.response.defer()

class EmbedImageModal(discord.ui.Modal, title='Embed Images'):
    def __init__(self, embed_data: EmbedData):
        super().__init__()
        self.embed_data = embed_data
        
        self.thumbnail_input = discord.ui.TextInput(
            label='Thumbnail URL',
            placeholder='Enter thumbnail URL (optional)',
            default=self.embed_data.thumbnail or '',
            max_length=1000,
            required=False
        )
        
        self.image_input = discord.ui.TextInput(
            label='Main Image URL',
            placeholder='Enter main image URL (optional)',
            default=self.embed_data.image or '',
            max_length=1000,
            required=False
        )
        
        self.add_item(self.thumbnail_input)
        self.add_item(self.image_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        self.embed_data.thumbnail = self.thumbnail_input.value.strip() or None
        self.embed_data.image = self.image_input.value.strip() or None
        await interaction.response.defer()

class EmbedFieldModal(discord.ui.Modal, title='Add Embed Field'):
    def __init__(self, embed_data: EmbedData, field_index=None):
        super().__init__()
        self.embed_data = embed_data
        self.field_index = field_index
        
        existing_field = None
        if field_index is not None and 0 <= field_index < len(embed_data.fields):
            existing_field = embed_data.fields[field_index]
        
        self.name_input = discord.ui.TextInput(
            label='Field Name',
            placeholder='Enter field name',
            default=existing_field['name'] if existing_field else '',
            max_length=256,
            required=True
        )
        
        self.value_input = discord.ui.TextInput(
            label='Field Value',
            placeholder='Enter field value',
            default=existing_field['value'] if existing_field else '',
            style=discord.TextStyle.paragraph,
            max_length=1024,
            required=True
        )
        
        self.inline_input = discord.ui.TextInput(
            label='Inline (true/false)',
            placeholder='true or false',
            default=str(existing_field.get('inline', True)).lower() if existing_field else 'true',
            max_length=5,
            required=False
        )
        
        self.add_item(self.name_input)
        self.add_item(self.value_input)
        self.add_item(self.inline_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        inline = self.inline_input.value.strip().lower() in ['true', '1', 'yes', 'y']
        
        field_data = {
            'name': self.name_input.value.strip(),
            'value': self.value_input.value.strip(),
            'inline': inline
        }
        
        if self.field_index is not None and 0 <= self.field_index < len(self.embed_data.fields):
            # Edit existing field
            self.embed_data.fields[self.field_index] = field_data
        else:
            # Add new field
            if len(self.embed_data.fields) < 25:
                self.embed_data.fields.append(field_data)
        
        await interaction.response.defer()

class ColorSelectView(discord.ui.View):
    def __init__(self, embed_data: EmbedData):
        super().__init__(timeout=300)
        self.embed_data = embed_data
        self.colors = {
            'Default': 0x2F3136,
            'Red': 0xFF0000,
            'Green': 0x00FF00,
            'Blue': 0x0000FF,
            'Yellow': 0xFFFF00,
            'Purple': 0x800080,
            'Orange': 0xFFA500,
            'Pink': 0xFFC0CB,
            'Cyan': 0x00FFFF,
            'Discord Blurple': 0x5865F2,
            'Discord Green': 0x57F287,
            'Discord Yellow': 0xFEE75C,
            'Discord Red': 0xED4245,
            'Black': 0x000000,
            'White': 0xFFFFFF,
            'Dark Grey': 0x36393F
        }
    
    @discord.ui.select(
        placeholder="Choose a color...",
        options=[
            discord.SelectOption(label=name, value=str(color), description=f"Hex: {hex(color)}")
            for name, color in list({
                'Default': 0x2F3136,
                'Red': 0xFF0000,
                'Green': 0x00FF00,
                'Blue': 0x0000FF,
                'Yellow': 0xFFFF00,
                'Purple': 0x800080,
                'Orange': 0xFFA500,
                'Pink': 0xFFC0CB,
                'Cyan': 0x00FFFF,
                'Discord Blurple': 0x5865F2,
                'Discord Green': 0x57F287,
                'Discord Yellow': 0xFEE75C,
                'Discord Red': 0xED4245,
                'Black': 0x000000,
                'White': 0xFFFFFF,
                'Dark Grey': 0x36393F
            }.items())[:25]  # Discord limit
        ]
    )
    async def color_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.embed_data.color = int(select.values[0])
        await interaction.response.defer()

class FieldSelectView(discord.ui.View):
    def __init__(self, embed_data: EmbedData):
        super().__init__(timeout=300)
        self.embed_data = embed_data
        self.update_options()
    
    def update_options(self):
        self.clear_items()
        
        if self.embed_data.fields:
            options = []
            for i, field in enumerate(self.embed_data.fields[:25]):  # Discord limit
                options.append(
                    discord.SelectOption(
                        label=f"Field {i+1}: {field['name'][:50]}",
                        value=str(i),
                        description=f"{'Inline' if field.get('inline', True) else 'Not inline'}"
                    )
                )
            
            select = discord.ui.Select(
                placeholder="Select a field to edit or remove...",
                options=options
            )
            select.callback = self.field_select_callback
            self.add_item(select)
    
    async def field_select_callback(self, interaction: discord.Interaction):
        self.selected_field = int(interaction.data['values'][0])
        await interaction.response.defer()

class EmbedBuilderView(discord.ui.View):
    def __init__(self, user_id: int, embed_data: EmbedData = None):
        super().__init__(timeout=600)
        self.user_id = user_id
        self.embed_data = embed_data or EmbedData()
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This embed builder is not for you!", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label='📝 Title & Description', style=discord.ButtonStyle.primary)
    async def edit_title_desc(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EmbedTitleModal(self.embed_data)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self.update_embed(interaction)
    
    @discord.ui.button(label='👤 Author', style=discord.ButtonStyle.secondary)
    async def edit_author(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EmbedAuthorModal(self.embed_data)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self.update_embed(interaction)
    
    @discord.ui.button(label='📄 Footer', style=discord.ButtonStyle.secondary)
    async def edit_footer(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EmbedFooterModal(self.embed_data)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self.update_embed(interaction)
    
    @discord.ui.button(label='🖼️ Images', style=discord.ButtonStyle.secondary)
    async def edit_images(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EmbedImageModal(self.embed_data)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self.update_embed(interaction)
    
    @discord.ui.button(label='🎨 Color', style=discord.ButtonStyle.secondary)
    async def edit_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ColorSelectView(self.embed_data)
        embed = discord.Embed(
            title="🎨 Choose Embed Color",
            description="Select a color from the dropdown below:",
            color=self.embed_data.color
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await view.wait()
        await self.update_embed(interaction)
    
    @discord.ui.button(label='➕ Add Field', style=discord.ButtonStyle.success, row=1)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.embed_data.fields) >= 25:
            await interaction.response.send_message("❌ Maximum 25 fields allowed!", ephemeral=True)
            return
        
        modal = EmbedFieldModal(self.embed_data)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self.update_embed(interaction)
    
    @discord.ui.button(label='✏️ Edit Fields', style=discord.ButtonStyle.secondary, row=1)
    async def edit_fields(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.embed_data.fields:
            await interaction.response.send_message("❌ No fields to edit!", ephemeral=True)
            return
        
        view = FieldSelectView(self.embed_data)
        embed = discord.Embed(
            title="✏️ Edit Fields",
            description="Select a field to edit:",
            color=self.embed_data.color
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await view.wait()
        
        if hasattr(view, 'selected_field'):
            modal = EmbedFieldModal(self.embed_data, view.selected_field)
            await interaction.followup.send_modal(modal)
            await modal.wait()
            await self.update_embed(interaction)
    
    @discord.ui.button(label='🗑️ Remove Field', style=discord.ButtonStyle.danger, row=1)
    async def remove_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.embed_data.fields:
            await interaction.response.send_message("❌ No fields to remove!", ephemeral=True)
            return
        
        view = FieldSelectView(self.embed_data)
        embed = discord.Embed(
            title="🗑️ Remove Field",
            description="Select a field to remove:",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await view.wait()
        
        if hasattr(view, 'selected_field'):
            self.embed_data.fields.pop(view.selected_field)
            await interaction.followup.send("✅ Field removed!", ephemeral=True)
            await self.update_embed(interaction)
    
    @discord.ui.button(label='⏰ Toggle Timestamp', style=discord.ButtonStyle.secondary, row=1)
    async def toggle_timestamp(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.embed_data.timestamp = not self.embed_data.timestamp
        await interaction.response.defer()
        await self.update_embed(interaction)
    
    @discord.ui.button(label='🚀 Send Embed', style=discord.ButtonStyle.success, row=2)
    async def send_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any([self.embed_data.title, self.embed_data.description, self.embed_data.fields]):
            await interaction.response.send_message("❌ Embed must have at least a title, description, or fields!", ephemeral=True)
            return
        
        embed = self.embed_data.to_embed()
        channel = interaction.channel
        
        try:
            await channel.send(embed=embed)
            await interaction.response.send_message("✅ Embed sent successfully!", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"❌ Failed to send embed: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label='📋 Copy JSON', style=discord.ButtonStyle.secondary, row=2)
    async def copy_json(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_dict = {
            'title': self.embed_data.title,
            'description': self.embed_data.description,
            'color': self.embed_data.color,
            'footer': {'text': self.embed_data.footer, 'icon_url': self.embed_data.footer_icon} if self.embed_data.footer else None,
            'author': {'name': self.embed_data.author, 'icon_url': self.embed_data.author_icon} if self.embed_data.author else None,
            'thumbnail': {'url': self.embed_data.thumbnail} if self.embed_data.thumbnail else None,
            'image': {'url': self.embed_data.image} if self.embed_data.image else None,
            'fields': self.embed_data.fields,
            'timestamp': self.embed_data.timestamp
        }
        
        # Remove None values
        embed_dict = {k: v for k, v in embed_dict.items() if v is not None}
        
        json_str = json.dumps(embed_dict, indent=2)
        
        if len(json_str) > 1900:
            await interaction.response.send_message("❌ JSON too long to display!", ephemeral=True)
            return
        
        await interaction.response.send_message(f"```json\n{json_str}\n```", ephemeral=True)
    
    @discord.ui.button(label='🔄 Clear All', style=discord.ButtonStyle.danger, row=2)
    async def clear_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.embed_data = EmbedData()
        await interaction.response.defer()
        await self.update_embed(interaction)
    
    @discord.ui.button(label='❌ Close', style=discord.ButtonStyle.danger, row=2)
    async def close_builder(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="✅ Embed builder closed.", embed=None, view=None)
    
    async def update_embed(self, interaction: discord.Interaction):
        embed = self.embed_data.to_embed()
        
        if not any([self.embed_data.title, self.embed_data.description, self.embed_data.fields]):
            embed = discord.Embed(
                title="🎨 Embed Builder",
                description="**Your embed will appear here as you build it!**\n\nStart by clicking the buttons below to customize your embed.",
                color=self.embed_data.color
            )
        
        try:
            await interaction.edit_original_response(embed=embed, view=self)
        except:
            pass

class EmbedBuilder(commands.Cog):
    """Advanced embed builder and message utilities"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name='embed')
    @commands.guild_only()
    async def create_embed(self, ctx):
        """Launch the interactive embed builder"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use the embed builder.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        embed_data = EmbedData()
        view = EmbedBuilderView(ctx.author.id, embed_data)
        
        embed = discord.Embed(
            title="🎨 Embed Builder",
            description="**Your embed will appear here as you build it!**\n\nStart by clicking the buttons below to customize your embed.",
            color=embed_data.color
        )
        
        embed.add_field(
            name="🛠️ How to Use",
            value="• Click **Title & Description** to set basic content\n• Use **Color** to choose embed color\n• Add **Fields** for organized information\n• Set **Author**, **Footer**, and **Images** for styling\n• Click **Send Embed** when ready!",
            inline=False
        )
        
        await ctx.send(embed=embed, view=view)
    
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