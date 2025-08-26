import discord
from discord.ext import commands
from discord import app_commands
import json
import logging
from typing import Optional
from utils.permissions import has_mod_permissions

logger = logging.getLogger(__name__)

class EmbedBuilderView(discord.ui.View):
    """Interactive embed builder view like Mimu"""
    
    def __init__(self, author):
        super().__init__(timeout=300)
        self.author = author
        self.embed_data = {
            'title': None,
            'description': None,
            'color': discord.Color.blue(),
            'image': None,
            'thumbnail': None,
            'footer': None,
            'author': None,
            'fields': []
        }
    
    def create_embed(self):
        """Create embed from current data"""
        embed = discord.Embed(
            title=self.embed_data['title'] or "Embed Builder",
            description=self.embed_data['description'] or "Use the buttons below to customize this embed",
            color=self.embed_data['color']
        )
        
        if self.embed_data['author']:
            embed.set_author(name=self.embed_data['author'])
        
        if self.embed_data['image']:
            try:
                embed.set_image(url=self.embed_data['image'])
            except:
                pass
        
        if self.embed_data['thumbnail']:
            try:
                embed.set_thumbnail(url=self.embed_data['thumbnail'])
            except:
                pass
        
        if self.embed_data['footer']:
            embed.set_footer(text=self.embed_data['footer'])
        
        for field in self.embed_data['fields']:
            embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])
        
        return embed
    
    @discord.ui.button(label='📝 Title', style=discord.ButtonStyle.secondary)
    async def set_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command user can edit this embed!", ephemeral=True)
            return
        
        modal = TextModal("Set Title", "Enter embed title:", self.embed_data['title'])
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        if modal.value:
            self.embed_data['title'] = modal.value
            await interaction.edit_original_response(embed=self.create_embed(), view=self)
    
    @discord.ui.button(label='📄 Description', style=discord.ButtonStyle.secondary)
    async def set_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command user can edit this embed!", ephemeral=True)
            return
        
        modal = TextModal("Set Description", "Enter embed description:", self.embed_data['description'])
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        if modal.value:
            self.embed_data['description'] = modal.value
            await interaction.edit_original_response(embed=self.create_embed(), view=self)
    
    @discord.ui.button(label='🎨 Color', style=discord.ButtonStyle.secondary)
    async def set_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command user can edit this embed!", ephemeral=True)
            return
        
        modal = TextModal("Set Color", "Enter hex color (e.g., #ff0000):", "")
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        if modal.value:
            try:
                color_hex = modal.value.lstrip('#')
                self.embed_data['color'] = discord.Color(int(color_hex, 16))
                await interaction.edit_original_response(embed=self.create_embed(), view=self)
            except:
                await interaction.followup.send("❌ Invalid color format! Use hex like #ff0000", ephemeral=True)
    
    @discord.ui.button(label='🖼️ Image', style=discord.ButtonStyle.secondary)
    async def set_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command user can edit this embed!", ephemeral=True)
            return
        
        modal = TextModal("Set Image", "Enter image URL:", self.embed_data['image'])
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        if modal.value:
            self.embed_data['image'] = modal.value
            await interaction.edit_original_response(embed=self.create_embed(), view=self)
    
    @discord.ui.button(label='🏷️ Footer', style=discord.ButtonStyle.secondary, row=1)
    async def set_footer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command user can edit this embed!", ephemeral=True)
            return
        
        modal = TextModal("Set Footer", "Enter footer text:", self.embed_data['footer'])
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        if modal.value:
            self.embed_data['footer'] = modal.value
            await interaction.edit_original_response(embed=self.create_embed(), view=self)
    
    @discord.ui.button(label='➕ Add Field', style=discord.ButtonStyle.primary, row=1)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command user can edit this embed!", ephemeral=True)
            return
        
        if len(self.embed_data['fields']) >= 25:
            await interaction.response.send_message("❌ Maximum 25 fields allowed!", ephemeral=True)
            return
        
        modal = FieldModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        if modal.name and modal.value:
            self.embed_data['fields'].append({
                'name': modal.name,
                'value': modal.value,
                'inline': modal.inline
            })
            await interaction.edit_original_response(embed=self.create_embed(), view=self)
    
    @discord.ui.button(label='🗑️ Clear Fields', style=discord.ButtonStyle.danger, row=1)
    async def clear_fields(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command user can edit this embed!", ephemeral=True)
            return
        
        self.embed_data['fields'] = []
        await interaction.response.edit_message(embed=self.create_embed(), view=self)
    
    @discord.ui.button(label='📤 Send to Channel', style=discord.ButtonStyle.success, row=2)
    async def send_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command user can edit this embed!", ephemeral=True)
            return
        
        view = ChannelSelectView(self.embed_data, interaction.guild)
        await interaction.response.send_message("Select a channel to send the embed:", view=view, ephemeral=True)
    
    @discord.ui.button(label='💌 Send DM', style=discord.ButtonStyle.success, row=2)
    async def send_dm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command user can edit this embed!", ephemeral=True)
            return
        
        view = UserSelectView(self.embed_data)
        await interaction.response.send_message("Select a user to send the embed via DM:", view=view, ephemeral=True)
    
    @discord.ui.button(label='❌ Cancel', style=discord.ButtonStyle.danger, row=2)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command user can edit this embed!", ephemeral=True)
            return
        
        await interaction.response.edit_message(content="❌ Embed builder cancelled.", embed=None, view=None)

class TextModal(discord.ui.Modal):
    """Modal for text input"""
    
    def __init__(self, title, label, default_value=""):
        super().__init__(title=title)
        self.value = None
        self.text_input = discord.ui.TextInput(
            label=label,
            default=default_value,
            max_length=1024,
            required=False
        )
        self.add_item(self.text_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        self.value = self.text_input.value or None
        await interaction.response.defer()

class FieldModal(discord.ui.Modal):
    """Modal for field input"""
    
    def __init__(self):
        super().__init__(title="Add Field")
        self.name = None
        self.value = None
        self.inline = True
        
        self.name_input = discord.ui.TextInput(
            label="Field Name",
            max_length=256,
            required=True
        )
        self.value_input = discord.ui.TextInput(
            label="Field Value",
            style=discord.TextStyle.paragraph,
            max_length=1024,
            required=True
        )
        self.inline_input = discord.ui.TextInput(
            label="Inline (true/false)",
            default="true",
            max_length=5,
            required=False
        )
        
        self.add_item(self.name_input)
        self.add_item(self.value_input)
        self.add_item(self.inline_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        self.name = self.name_input.value
        self.value = self.value_input.value
        self.inline = self.inline_input.value.lower() in ['true', 't', 'yes', 'y', '1']
        await interaction.response.defer()

class ChannelSelectView(discord.ui.View):
    """Channel selection for embed sending"""
    
    def __init__(self, embed_data, guild):
        super().__init__(timeout=60)
        self.embed_data = embed_data
        self.guild = guild
    
    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text])
    async def select_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        channel = select.values[0]
        
        embed = discord.Embed(
            title=self.embed_data['title'] or "Custom Embed",
            description=self.embed_data['description'] or "Embed created with embed builder",
            color=self.embed_data['color']
        )
        
        if self.embed_data['author']:
            embed.set_author(name=self.embed_data['author'])
        if self.embed_data['image']:
            try:
                embed.set_image(url=self.embed_data['image'])
            except:
                pass
        if self.embed_data['thumbnail']:
            try:
                embed.set_thumbnail(url=self.embed_data['thumbnail'])
            except:
                pass
        if self.embed_data['footer']:
            embed.set_footer(text=self.embed_data['footer'])
        
        for field in self.embed_data['fields']:
            embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])
        
        try:
            await channel.send(embed=embed)
            await interaction.response.edit_message(
                content=f"✅ Embed sent to {channel.mention}!",
                view=None
            )
        except discord.Forbidden:
            await interaction.response.edit_message(
                content=f"❌ No permission to send messages in {channel.mention}!",
                view=None
            )

class UserSelectView(discord.ui.View):
    """User selection for DM sending"""
    
    def __init__(self, embed_data):
        super().__init__(timeout=60)
        self.embed_data = embed_data
    
    @discord.ui.select(cls=discord.ui.UserSelect)
    async def select_user(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        user = select.values[0]
        
        embed = discord.Embed(
            title=self.embed_data['title'] or "Custom Embed",
            description=self.embed_data['description'] or "Embed created with embed builder",
            color=self.embed_data['color']
        )
        
        if self.embed_data['author']:
            embed.set_author(name=self.embed_data['author'])
        if self.embed_data['image']:
            try:
                embed.set_image(url=self.embed_data['image'])
            except:
                pass
        if self.embed_data['thumbnail']:
            try:
                embed.set_thumbnail(url=self.embed_data['thumbnail'])
            except:
                pass
        if self.embed_data['footer']:
            embed.set_footer(text=self.embed_data['footer'])
        
        for field in self.embed_data['fields']:
            embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])
        
        try:
            await user.send(embed=embed)
            await interaction.response.edit_message(
                content=f"✅ Embed sent to {user.display_name} via DM!",
                view=None
            )
        except discord.Forbidden:
            await interaction.response.edit_message(
                content=f"❌ Cannot send DM to {user.display_name}! They may have DMs disabled.",
                view=None
            )

class EmbedBuilder(commands.Cog):
    """Interactive embed builder system like Mimu"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name='embed')
    @commands.guild_only()
    async def create_embed(self, ctx):
        """Launch interactive embed builder (Mimu style)"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to create embeds.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        view = EmbedBuilderView(ctx.author)
        embed = view.create_embed()
        
        await ctx.send(embed=embed, view=view)
        logger.info(f"{ctx.author} launched embed builder in {ctx.guild.name}")
    
    @commands.hybrid_command(name='dm')
    @app_commands.describe(
        user="User to send DM to",
        message="Message to send"
    )
    @commands.guild_only()
    async def dm_user(self, ctx, user: discord.Member, *, message: str):
        """Send a DM to a specific user"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to send DMs.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        try:
            await user.send(message)
            
            confirm_embed = discord.Embed(
                title="✅ DM Sent",
                description=f"Message sent to {user.display_name}",
                color=discord.Color.green()
            )
            await ctx.send(embed=confirm_embed, ephemeral=True)
            
            logger.info(f"{ctx.author} sent DM to {user} in {ctx.guild.name}")
            
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ DM Failed",
                description=f"Cannot send DM to {user.display_name}. They may have DMs disabled.",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed, ephemeral=True)
    
    @commands.hybrid_command(name='embedinfo')
    @commands.guild_only()
    async def embed_info(self, ctx):
        """Show information about the interactive embed builder"""
        embed = discord.Embed(
            title="🎨 Interactive Embed Builder",
            description="Create beautiful embeds with an easy-to-use interface!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📝 How to Use",
            value="Run `/embed` to open the interactive builder",
            inline=False
        )
        
        embed.add_field(
            name="✨ Features",
            value="• Interactive buttons for easy editing\n• Real-time preview\n• Send to any channel\n• Send as DM to users\n• Add up to 25 fields\n• Custom colors, images, and more!",
            inline=False
        )
        
        embed.add_field(
            name="💌 DM Feature",
            value="Use `/dm @user message` to send direct messages",
            inline=False
        )
        
        embed.set_footer(text="💡 All commands require moderator permissions")
        
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