import discord
from discord.ext import commands
from discord import app_commands
import json
import logging
import asyncio
import os
import uuid
from datetime import datetime
from typing import Optional
from utils.permissions import has_mod_permissions

logger = logging.getLogger(__name__)

class EmbedStorage:
    """Manages saving and loading embeds with unique IDs"""
    
    def __init__(self):
        self.storage_file = "data/saved_embeds.json"
        self.ensure_storage_dir()
    
    def ensure_storage_dir(self):
        """Ensure the data directory exists"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, 'w') as f:
                json.dump({}, f)
    
    def save_embed(self, embed_data, name=None, user_id=None):
        """Save an embed and return its unique ID"""
        embed_id = str(uuid.uuid4())[:8]  # Short 8-character ID
        
        embed_dict = {
            'id': embed_id,
            'name': name or f"Embed {embed_id}",
            'created_by': user_id,
            'created_at': datetime.now().isoformat(),
            'data': {
                'title': embed_data.title,
                'description': embed_data.description,
                'color': embed_data.color,
                'footer': embed_data.footer,
                'footer_icon': embed_data.footer_icon,
                'author': embed_data.author,
                'author_icon': embed_data.author_icon,
                'thumbnail': embed_data.thumbnail,
                'image': embed_data.image,
                'fields': embed_data.fields,
                'timestamp': embed_data.timestamp
            }
        }
        
        # Load existing embeds
        with open(self.storage_file, 'r') as f:
            embeds = json.load(f)
        
        # Save new embed
        embeds[embed_id] = embed_dict
        
        with open(self.storage_file, 'w') as f:
            json.dump(embeds, f, indent=2)
        
        return embed_id
    
    def load_embed(self, embed_id):
        """Load an embed by ID"""
        try:
            with open(self.storage_file, 'r') as f:
                embeds = json.load(f)
            
            if embed_id in embeds:
                return embeds[embed_id]
            return None
        except:
            return None
    
    def get_all_embeds(self, user_id=None):
        """Get all saved embeds, optionally filtered by user"""
        try:
            with open(self.storage_file, 'r') as f:
                embeds = json.load(f)
            
            if user_id:
                return {k: v for k, v in embeds.items() if v.get('created_by') == user_id}
            return embeds
        except:
            return {}
    
    def delete_embed(self, embed_id, user_id=None):
        """Delete an embed by ID"""
        try:
            with open(self.storage_file, 'r') as f:
                embeds = json.load(f)
            
            if embed_id in embeds:
                # Check if user owns the embed or is authorized
                embed_data = embeds[embed_id]
                if user_id and embed_data.get('created_by') != user_id:
                    return False, "You can only delete embeds you created."
                
                del embeds[embed_id]
                
                with open(self.storage_file, 'w') as f:
                    json.dump(embeds, f, indent=2)
                
                return True, "Embed deleted successfully."
            
            return False, "Embed not found."
        except:
            return False, "Error deleting embed."

# Global embed storage instance
embed_storage = EmbedStorage()

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
    
    @discord.ui.button(label='💾 Save & Send', style=discord.ButtonStyle.success, row=2)
    async def send_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any([self.embed_data.title, self.embed_data.description, self.embed_data.fields]):
            await interaction.response.send_message("❌ Embed must have at least a title, description, or fields!", ephemeral=True)
            return
        
        # Save embed with ID
        embed_id = embed_storage.save_embed(self.embed_data, user_id=interaction.user.id)
        
        embed = self.embed_data.to_embed()
        embed.set_footer(text=f"{embed.footer.text if embed.footer else ''} • ID: {embed_id}".strip(" • "))
        
        channel = interaction.channel
        
        try:
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Embed sent and saved with ID: `{embed_id}`\n\nYou can now use this embed in any message command with: `embed:{embed_id}`", ephemeral=True)
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
    @app_commands.describe(message="Message or embed ID (embed:ID) to send as the bot")
    @commands.guild_only()
    async def say_message(self, ctx, *, message: str):
        """Send a message or embed as the bot"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Parse message or embed ID
        msg_type, content, embed_id = self.parse_message_or_embed(message)
        
        if msg_type == 'error':
            embed = discord.Embed(
                title="❌ Error",
                description=content,
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Check message length for text messages
        if msg_type == 'text' and len(content) > 2000:
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
        
        # Send the message or embed
        try:
            if msg_type == 'embed':
                await ctx.send(embed=content)
            else:
                await ctx.send(content)
            
            if ctx.interaction:
                # Send confirmation for slash command
                confirmation_text = f"Embed `{embed_id}` posted successfully!" if msg_type == 'embed' else "Your message has been posted."
                embed = discord.Embed(
                    title="✅ Message Sent",
                    description=confirmation_text,
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
    
    @commands.hybrid_command(name='saychannel')
    @app_commands.describe(
        channel="The channel to send the message to",
        message="Message or embed ID (embed:ID) to send as the bot"
    )
    @commands.guild_only()
    async def say_channel(self, ctx, channel: discord.TextChannel, *, message: str):
        """Send a message or embed to a specific channel as the bot"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Parse message or embed ID
        msg_type, content, embed_id = self.parse_message_or_embed(message)
        
        if msg_type == 'error':
            embed = discord.Embed(
                title="❌ Error",
                description=content,
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Check message length for text messages
        if msg_type == 'text' and len(content) > 2000:
            embed = discord.Embed(
                title="❌ Message Too Long",
                description="Message cannot exceed 2000 characters.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Check if bot can send messages in target channel
        if not channel.permissions_for(ctx.guild.me).send_messages:
            embed = discord.Embed(
                title="❌ No Permission",
                description=f"I don't have permission to send messages in {channel.mention}.",
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
        
        # Send the message or embed to target channel
        try:
            if msg_type == 'embed':
                await channel.send(embed=content)
            else:
                await channel.send(content)
            
            # Send confirmation
            confirmation_text = f"Embed `{embed_id}` posted to {channel.mention}!" if msg_type == 'embed' else f"Your message has been posted to {channel.mention}."
            embed = discord.Embed(
                title="✅ Message Sent",
                description=confirmation_text,
                color=discord.Color.green()
            )
            
            if msg_type == 'text':
                embed.add_field(
                    name="Message Preview",
                    value=content[:100] + ("..." if len(content) > 100 else ""),
                    inline=False
                )
            
            if ctx.interaction:
                await ctx.send(embed=embed, ephemeral=True)
            else:
                # For prefix commands, send confirmation in current channel briefly
                confirm_msg = await ctx.send(embed=embed)
                await asyncio.sleep(3)
                try:
                    await confirm_msg.delete()
                except:
                    pass
                
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="❌ Failed to Send",
                description=f"Could not send the message to {channel.mention}: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
    
    def parse_message_or_embed(self, message_text):
        """Parse message text to check if it's an embed ID or regular text"""
        if message_text.startswith('embed:'):
            embed_id = message_text[6:].strip()
            embed_data = embed_storage.load_embed(embed_id)
            if embed_data:
                # Convert back to EmbedData object
                data = embed_data['data']
                embed_obj = EmbedData()
                embed_obj.title = data.get('title')
                embed_obj.description = data.get('description')
                embed_obj.color = data.get('color', 0x2F3136)
                embed_obj.footer = data.get('footer')
                embed_obj.footer_icon = data.get('footer_icon')
                embed_obj.author = data.get('author')
                embed_obj.author_icon = data.get('author_icon')
                embed_obj.thumbnail = data.get('thumbnail')
                embed_obj.image = data.get('image')
                embed_obj.fields = data.get('fields', [])
                embed_obj.timestamp = data.get('timestamp', False)
                
                embed = embed_obj.to_embed()
                # Add ID to footer
                current_footer = embed.footer.text if embed.footer else ""
                embed.set_footer(text=f"{current_footer} • ID: {embed_id}".strip(" • "))
                return ('embed', embed, embed_id)
            else:
                return ('error', f"❌ Embed ID `{embed_id}` not found.", None)
        else:
            return ('text', message_text, None)
    
    @commands.hybrid_command(name='embeds')
    @commands.guild_only()
    async def list_embeds(self, ctx):
        """List your saved embeds"""
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        user_embeds = embed_storage.get_all_embeds(ctx.author.id)
        
        if not user_embeds:
            embed = discord.Embed(
                title="📋 Your Saved Embeds",
                description="You haven't saved any embeds yet.\n\nUse the embed builder (`!embed`) to create and save embeds!",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="📋 Your Saved Embeds",
            description=f"You have **{len(user_embeds)}** saved embeds:",
            color=discord.Color.blue()
        )
        
        for embed_id, embed_data in list(user_embeds.items())[:10]:  # Show first 10
            title = embed_data['data'].get('title', 'No Title')
            created_at = datetime.fromisoformat(embed_data['created_at']).strftime("%m/%d/%Y")
            embed.add_field(
                name=f"🆔 `{embed_id}`",
                value=f"**{title[:50]}{'...' if len(title) > 50 else ''}**\nCreated: {created_at}",
                inline=True
            )
        
        if len(user_embeds) > 10:
            embed.add_field(
                name="➕ More",
                value=f"And {len(user_embeds) - 10} more...",
                inline=True
            )
        
        embed.add_field(
            name="💡 How to Use",
            value="Use `embed:ID` in any message command\nExample: `!say embed:abc123`",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='viewembed')
    @app_commands.describe(embed_id="The ID of the embed to view")
    @commands.guild_only()
    async def view_embed(self, ctx, embed_id: str):
        """View a specific saved embed"""
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        embed_data = embed_storage.load_embed(embed_id)
        
        if not embed_data:
            embed = discord.Embed(
                title="❌ Embed Not Found",
                description=f"No embed found with ID `{embed_id}`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Convert to embed and display
        data = embed_data['data']
        embed_obj = EmbedData()
        embed_obj.title = data.get('title')
        embed_obj.description = data.get('description')
        embed_obj.color = data.get('color', 0x2F3136)
        embed_obj.footer = data.get('footer')
        embed_obj.footer_icon = data.get('footer_icon')
        embed_obj.author = data.get('author')
        embed_obj.author_icon = data.get('author_icon')
        embed_obj.thumbnail = data.get('thumbnail')
        embed_obj.image = data.get('image')
        embed_obj.fields = data.get('fields', [])
        embed_obj.timestamp = data.get('timestamp', False)
        
        embed = embed_obj.to_embed()
        embed.set_footer(text=f"{embed.footer.text if embed.footer else ''} • ID: {embed_id}".strip(" • "))
        
        info_embed = discord.Embed(
            title="👀 Embed Preview",
            description=f"**ID:** `{embed_id}`\n**Created:** {datetime.fromisoformat(embed_data['created_at']).strftime('%B %d, %Y')}\n**Creator:** <@{embed_data.get('created_by')}>\n\n**Preview:**",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=info_embed)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='deleteembed')
    @app_commands.describe(embed_id="The ID of the embed to delete")
    @commands.guild_only()
    async def delete_embed(self, ctx, embed_id: str):
        """Delete a saved embed"""
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        success, message = embed_storage.delete_embed(embed_id, ctx.author.id)
        
        embed = discord.Embed(
            title="✅ Success" if success else "❌ Error",
            description=message,
            color=discord.Color.green() if success else discord.Color.red()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))