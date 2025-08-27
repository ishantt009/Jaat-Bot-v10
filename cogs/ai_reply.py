"""
AI Reply System Cog
Provides AI-powered responses to messages with per-channel toggle control
Uses free Hugging Face API for AI responses
"""

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class AIReplySystem(commands.Cog, name="🤖 AI Reply System"):
    """AI-powered message responses with per-channel control"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'data/ai_config.json'
        self.enabled_channels: set = set()
        self.ai_settings: dict = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.load_config()
        
    async def cog_load(self):
        """Initialize aiohttp session when cog loads"""
        self.session = aiohttp.ClientSession()
        
    async def cog_unload(self):
        """Clean up aiohttp session when cog unloads"""
        if self.session:
            await self.session.close()
    
    def load_config(self):
        """Load AI configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.enabled_channels = set(config.get('enabled_channels', []))
                self.ai_settings = config.get('ai_settings', {
                    'model': 'microsoft/DialoGPT-medium',
                    'max_length': 100,
                    'temperature': 0.7,
                    'response_chance': 100,
                    'mention_only': False,
                    'ignore_bots': True,
                    'cooldown': 3
                })
        except FileNotFoundError:
            # Default settings
            self.enabled_channels = set()
            self.ai_settings = {
                'model': 'microsoft/DialoGPT-medium',
                'max_length': 100,
                'temperature': 0.7,
                'response_chance': 100,
                'mention_only': False,
                'ignore_bots': True,
                'cooldown': 3
            }
            self.save_config()
        except Exception as e:
            logger.error(f"Error loading AI config: {e}")
            
    def save_config(self):
        """Save AI configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            config = {
                'enabled_channels': list(self.enabled_channels),
                'ai_settings': self.ai_settings
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving AI config: {e}")
            return False
    
    def is_admin(self, user: discord.Member) -> bool:
        """Check if user has admin permissions"""
        if not isinstance(user, discord.Member):
            return False
        return user.guild_permissions.administrator or user.guild_permissions.manage_channels
    
    async def generate_response(self, message_text: str, context: Optional[List[str]] = None) -> Optional[str]:
        """Generate AI response using Hugging Face API"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            # Use Hugging Face Inference API (free tier)
            api_url = f"https://api-inference.huggingface.co/models/{self.ai_settings['model']}"
            
            # Prepare context for conversational model
            if context:
                conversation = " ".join(context[-3:])  # Last 3 messages for context
                input_text = f"{conversation} {message_text}"
            else:
                input_text = message_text
            
            # Prepare the payload
            payload = {
                "inputs": input_text,
                "parameters": {
                    "max_length": self.ai_settings['max_length'],
                    "temperature": self.ai_settings['temperature'],
                    "do_sample": True,
                    "pad_token_id": 50256
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            async with self.session.post(api_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get('generated_text', '')
                        
                        # Clean up the response
                        if generated_text:
                            # Remove the input text from the response
                            if input_text in generated_text:
                                generated_text = generated_text.replace(input_text, '').strip()
                            
                            # Clean up any remaining artifacts
                            generated_text = generated_text.strip()
                            if generated_text:
                                # Limit response length
                                if len(generated_text) > 200:
                                    generated_text = generated_text[:200] + "..."
                                return generated_text
                                
                elif response.status == 503:
                    # Model is loading, return a fallback
                    return "I'm thinking... 🤔 (AI model is warming up)"
                else:
                    logger.warning(f"HuggingFace API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            
        # Fallback responses
        fallback_responses = [
            "That's interesting! Tell me more.",
            "I see what you mean!",
            "Thanks for sharing that!",
            "That's a good point!",
            "Interesting perspective!",
            "I understand!",
            "That makes sense!"
        ]
        
        import random
        return random.choice(fallback_responses)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages and respond with AI if enabled"""
        
        # Skip if not in enabled channel
        if message.channel.id not in self.enabled_channels:
            return
            
        # Skip bot messages if configured
        if self.ai_settings['ignore_bots'] and message.author.bot:
            return
            
        # Skip if it's the bot's own message
        if message.author == self.bot.user:
            return
            
        # Check if mention only mode is enabled
        if self.ai_settings['mention_only']:
            if not (self.bot.user.mentioned_in(message) or 
                   isinstance(message.channel, discord.DMChannel)):
                return
        
        # Random response chance
        import random
        if random.randint(1, 100) > self.ai_settings['response_chance']:
            return
            
        # Get recent message context
        try:
            context = []
            async for msg in message.channel.history(limit=5, before=message):
                if not msg.author.bot:
                    context.append(msg.content)
            context.reverse()  # Chronological order
            
            # Generate AI response
            async with message.channel.typing():
                response = await self.generate_response(message.content, context)
                
            if response:
                # Add cooldown
                await asyncio.sleep(self.ai_settings['cooldown'])
                await message.reply(response, mention_author=False)
                
        except Exception as e:
            logger.error(f"Error in AI reply system: {e}")
    
    @commands.command(name='ai-enable', aliases=['aienable', 'ai_enable'], help='Enable AI replies in this channel')
    async def enable_ai_prefix(self, ctx):
        """Enable AI replies in the current channel (prefix version)"""
        
        if not isinstance(ctx.author, discord.Member) or not self.is_admin(ctx.author):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only administrators can manage AI reply settings.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        channel_id = ctx.channel.id
        
        if channel_id in self.enabled_channels:
            embed = discord.Embed(
                title="ℹ️ Already Enabled",
                description="AI replies are already enabled in this channel.",
                color=discord.Color.blue()
            )
        else:
            self.enabled_channels.add(channel_id)
            self.save_config()
            
            embed = discord.Embed(
                title="✅ AI Replies Enabled",
                description=f"AI replies are now enabled in {ctx.channel.mention}!",
                color=discord.Color.green()
            )
            
        await ctx.send(embed=embed)

    @app_commands.command(name='ai-enable', description='Enable AI replies in this channel')
    async def enable_ai(self, interaction: discord.Interaction):
        """Enable AI replies in the current channel"""
        
        if not isinstance(interaction.user, discord.Member) or not self.is_admin(interaction.user):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only administrators can manage AI reply settings.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not interaction.channel:
            await interaction.response.send_message("❌ Unable to determine channel.", ephemeral=True)
            return
            
        channel_id = interaction.channel.id
        
        if channel_id in self.enabled_channels:
            embed = discord.Embed(
                title="ℹ️ Already Enabled",
                description="AI replies are already enabled in this channel.",
                color=discord.Color.blue()
            )
        else:
            self.enabled_channels.add(channel_id)
            self.save_config()
            
            channel_mention = getattr(interaction.channel, 'mention', f"<#{channel_id}>")
            embed = discord.Embed(
                title="✅ AI Replies Enabled",
                description=f"AI replies are now enabled in {channel_mention}!",
                color=discord.Color.green()
            )
            
        await interaction.response.send_message(embed=embed)
    
    @commands.command(name='ai-disable', aliases=['aidisable', 'ai_disable'], help='Disable AI replies in this channel')
    async def disable_ai_prefix(self, ctx):
        """Disable AI replies in the current channel (prefix version)"""
        
        if not isinstance(ctx.author, discord.Member) or not self.is_admin(ctx.author):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only administrators can manage AI reply settings.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        channel_id = ctx.channel.id
        
        if channel_id not in self.enabled_channels:
            embed = discord.Embed(
                title="ℹ️ Already Disabled",
                description="AI replies are already disabled in this channel.",
                color=discord.Color.blue()
            )
        else:
            self.enabled_channels.discard(channel_id)
            self.save_config()
            
            embed = discord.Embed(
                title="✅ AI Replies Disabled",
                description=f"AI replies are now disabled in {ctx.channel.mention}.",
                color=discord.Color.orange()
            )
            
        await ctx.send(embed=embed)

    @app_commands.command(name='ai-disable', description='Disable AI replies in this channel')
    async def disable_ai(self, interaction: discord.Interaction):
        """Disable AI replies in the current channel"""
        
        if not isinstance(interaction.user, discord.Member) or not self.is_admin(interaction.user):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only administrators can manage AI reply settings.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not interaction.channel:
            await interaction.response.send_message("❌ Unable to determine channel.", ephemeral=True)
            return
            
        channel_id = interaction.channel.id
        
        if channel_id not in self.enabled_channels:
            embed = discord.Embed(
                title="ℹ️ Already Disabled",
                description="AI replies are already disabled in this channel.",
                color=discord.Color.blue()
            )
        else:
            self.enabled_channels.discard(channel_id)
            self.save_config()
            
            channel_mention = getattr(interaction.channel, 'mention', f"<#{channel_id}>")
            embed = discord.Embed(
                title="✅ AI Replies Disabled",
                description=f"AI replies are now disabled in {channel_mention}.",
                color=discord.Color.orange()
            )
            
        await interaction.response.send_message(embed=embed)
    
    @commands.command(name='ai-status', aliases=['aistatus', 'ai_status'], help='Check AI reply status for channels')
    async def ai_status_prefix(self, ctx):
        """Show AI reply status for all channels (prefix version)"""
        
        embed = discord.Embed(
            title="🤖 AI Reply System Status",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Current channel status
        current_status = "✅ Enabled" if ctx.channel.id in self.enabled_channels else "❌ Disabled"
        embed.add_field(
            name="Current Channel",
            value=f"{ctx.channel.mention}: {current_status}",
            inline=False
        )
        
        # All enabled channels
        if self.enabled_channels:
            enabled_channels = []
            for channel_id in self.enabled_channels:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    enabled_channels.append(channel.mention)
                    
            if enabled_channels:
                embed.add_field(
                    name="Enabled Channels",
                    value="\n".join(enabled_channels[:10]) + 
                          (f"\n... and {len(enabled_channels) - 10} more" if len(enabled_channels) > 10 else ""),
                    inline=False
                )
        else:
            embed.add_field(
                name="Enabled Channels",
                value="None",
                inline=False
            )
        
        # Settings info
        settings_info = f"**Model:** {self.ai_settings['model']}\n"
        settings_info += f"**Response Chance:** {self.ai_settings['response_chance']}%\n"
        settings_info += f"**Mention Only:** {'Yes' if self.ai_settings['mention_only'] else 'No'}\n"
        settings_info += f"**Cooldown:** {self.ai_settings['cooldown']}s"
        
        embed.add_field(
            name="AI Settings",
            value=settings_info,
            inline=False
        )
        
        embed.set_footer(text="Use !ai-enable or !ai-disable to manage channels")
        
        await ctx.send(embed=embed)

    @app_commands.command(name='ai-status', description='Check AI reply status for channels')
    async def ai_status(self, interaction: discord.Interaction):
        """Show AI reply status for all channels"""
        
        embed = discord.Embed(
            title="🤖 AI Reply System Status",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Current channel status
        if interaction.channel:
            current_status = "✅ Enabled" if interaction.channel.id in self.enabled_channels else "❌ Disabled"
            channel_mention = getattr(interaction.channel, 'mention', f"<#{interaction.channel.id}>")
            embed.add_field(
                name="Current Channel",
                value=f"{channel_mention}: {current_status}",
                inline=False
            )
        
        # All enabled channels
        if self.enabled_channels:
            enabled_channels = []
            for channel_id in self.enabled_channels:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    enabled_channels.append(channel.mention)
                    
            if enabled_channels:
                embed.add_field(
                    name="Enabled Channels",
                    value="\n".join(enabled_channels[:10]) + 
                          (f"\n... and {len(enabled_channels) - 10} more" if len(enabled_channels) > 10 else ""),
                    inline=False
                )
        else:
            embed.add_field(
                name="Enabled Channels",
                value="None",
                inline=False
            )
        
        # Settings info
        settings_info = f"**Model:** {self.ai_settings['model']}\n"
        settings_info += f"**Response Chance:** {self.ai_settings['response_chance']}%\n"
        settings_info += f"**Mention Only:** {'Yes' if self.ai_settings['mention_only'] else 'No'}\n"
        settings_info += f"**Cooldown:** {self.ai_settings['cooldown']}s"
        
        embed.add_field(
            name="AI Settings",
            value=settings_info,
            inline=False
        )
        
        embed.set_footer(text="Use /ai-enable or /ai-disable to manage channels")
        
        await interaction.response.send_message(embed=embed)
    
    @commands.command(name='ai-settings', aliases=['aisettings', 'ai_settings'], help='[ADMIN] Configure AI reply settings')
    async def ai_settings_prefix(self, ctx, response_chance: Optional[int] = None, mention_only: Optional[bool] = None, cooldown: Optional[int] = None):
        """Configure AI reply settings (prefix version)"""
        
        if not isinstance(ctx.author, discord.Member) or not self.is_admin(ctx.author):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only administrators can configure AI settings.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        changes = []
        
        if response_chance is not None:
            if 1 <= response_chance <= 100:
                self.ai_settings['response_chance'] = response_chance
                changes.append(f"Response chance: {response_chance}%")
            else:
                embed = discord.Embed(
                    title="❌ Invalid Value",
                    description="Response chance must be between 1 and 100.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        
        if mention_only is not None:
            self.ai_settings['mention_only'] = mention_only
            changes.append(f"Mention only: {'Yes' if mention_only else 'No'}")
        
        if cooldown is not None:
            if 0 <= cooldown <= 30:
                self.ai_settings['cooldown'] = cooldown
                changes.append(f"Cooldown: {cooldown}s")
            else:
                embed = discord.Embed(
                    title="❌ Invalid Value",
                    description="Cooldown must be between 0 and 30 seconds.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        
        if changes:
            self.save_config()
            embed = discord.Embed(
                title="✅ Settings Updated",
                description="AI reply settings have been updated:\n\n" + "\n".join(changes),
                color=discord.Color.green()
            )
        else:
            # Show current settings
            embed = discord.Embed(
                title="🔧 Current AI Settings",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Response Chance", value=f"{self.ai_settings['response_chance']}%", inline=True)
            embed.add_field(name="Mention Only", value="Yes" if self.ai_settings['mention_only'] else "No", inline=True)
            embed.add_field(name="Cooldown", value=f"{self.ai_settings['cooldown']}s", inline=True)
            embed.add_field(name="Model", value=self.ai_settings['model'], inline=False)
            
            embed.add_field(
                name="Usage Examples",
                value="```\n!ai-settings 50         # Set 50% response chance\n!ai-settings 100 True   # 100% chance, mention only\n!ai-settings 75 False 5 # 75% chance, any message, 5s cooldown\n```",
                inline=False
            )
            
        await ctx.send(embed=embed)

    @app_commands.command(name='ai-settings', description='[ADMIN] Configure AI reply settings')
    @app_commands.describe(
        response_chance='Percentage chance to respond (1-100)',
        mention_only='Only respond when bot is mentioned',
        cooldown='Cooldown between responses in seconds'
    )
    async def ai_settings(self, interaction: discord.Interaction, 
                         response_chance: Optional[int] = None,
                         mention_only: Optional[bool] = None,
                         cooldown: Optional[int] = None):
        """Configure AI reply settings"""
        
        if not isinstance(interaction.user, discord.Member) or not self.is_admin(interaction.user):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only administrators can configure AI settings.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        changes = []
        
        if response_chance is not None:
            if 1 <= response_chance <= 100:
                self.ai_settings['response_chance'] = response_chance
                changes.append(f"Response chance: {response_chance}%")
            else:
                embed = discord.Embed(
                    title="❌ Invalid Value",
                    description="Response chance must be between 1 and 100.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        if mention_only is not None:
            self.ai_settings['mention_only'] = mention_only
            changes.append(f"Mention only: {'Yes' if mention_only else 'No'}")
        
        if cooldown is not None:
            if 0 <= cooldown <= 30:
                self.ai_settings['cooldown'] = cooldown
                changes.append(f"Cooldown: {cooldown}s")
            else:
                embed = discord.Embed(
                    title="❌ Invalid Value",
                    description="Cooldown must be between 0 and 30 seconds.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        if changes:
            self.save_config()
            embed = discord.Embed(
                title="✅ Settings Updated",
                description="AI reply settings have been updated:\n\n" + "\n".join(changes),
                color=discord.Color.green()
            )
        else:
            # Show current settings
            embed = discord.Embed(
                title="🔧 Current AI Settings",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Response Chance", value=f"{self.ai_settings['response_chance']}%", inline=True)
            embed.add_field(name="Mention Only", value="Yes" if self.ai_settings['mention_only'] else "No", inline=True)
            embed.add_field(name="Cooldown", value=f"{self.ai_settings['cooldown']}s", inline=True)
            embed.add_field(name="Model", value=self.ai_settings['model'], inline=False)
            
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    """Setup function to add this cog to the bot"""
    await bot.add_cog(AIReplySystem(bot))