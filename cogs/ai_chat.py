import discord
from discord.ext import commands
from discord import app_commands
import json
import logging
import os
import asyncio
from openai import OpenAI
from utils.permissions import has_mod_permissions

logger = logging.getLogger(__name__)

class AIChattingStorage:
    """Manages AI chat settings for channels"""
    
    def __init__(self):
        self.storage_file = "data/ai_chat_settings.json"
        self.ensure_storage_dir()
    
    def ensure_storage_dir(self):
        """Ensure the data directory exists"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, 'w') as f:
                json.dump({}, f)
    
    def is_enabled(self, guild_id, channel_id):
        """Check if AI chat is enabled for a channel"""
        try:
            with open(self.storage_file, 'r') as f:
                settings = json.load(f)
            
            guild_key = str(guild_id)
            channel_key = str(channel_id)
            
            return settings.get(guild_key, {}).get(channel_key, False)
        except:
            return False
    
    def set_enabled(self, guild_id, channel_id, enabled):
        """Enable or disable AI chat for a channel"""
        try:
            with open(self.storage_file, 'r') as f:
                settings = json.load(f)
            
            guild_key = str(guild_id)
            channel_key = str(channel_id)
            
            if guild_key not in settings:
                settings[guild_key] = {}
            
            settings[guild_key][channel_key] = enabled
            
            with open(self.storage_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error updating AI chat settings: {e}")
            return False
    
    def get_enabled_channels(self, guild_id):
        """Get all enabled channels for a guild"""
        try:
            with open(self.storage_file, 'r') as f:
                settings = json.load(f)
            
            guild_key = str(guild_id)
            guild_settings = settings.get(guild_key, {})
            
            return [int(channel_id) for channel_id, enabled in guild_settings.items() if enabled]
        except:
            return []

# Global storage instance
ai_chat_storage = AIChattingStorage()

class AIChat(commands.Cog):
    """AI Chat Reply System with channel-specific controls"""
    
    def __init__(self, bot):
        self.bot = bot
        self.openai_client = None
        self.setup_openai()
        self.rate_limits = {}  # Simple rate limiting per user
    
    def setup_openai(self):
        """Initialize OpenAI client"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        else:
            logger.warning("OpenAI API key not found - AI chat will be disabled")
    
    async def get_ai_response(self, message_content, user_name, channel_name):
        """Get AI response using OpenAI"""
        if not self.openai_client:
            return "❌ AI chat is not configured properly. Missing API key."
        
        try:
            # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a helpful Discord bot assistant. You're chatting in #{channel_name}. Keep responses conversational, friendly, and under 2000 characters. Don't mention that you're an AI unless directly asked."
                    },
                    {
                        "role": "user", 
                        "content": f"{user_name}: {message_content}"
                    }
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return "❌ Sorry, I'm having trouble thinking right now. Please try again later."
    
    def should_respond_to_message(self, message):
        """Check if bot should respond to this message"""
        # Don't respond to bots
        if message.author.bot:
            return False
        
        # Don't respond in DMs
        if not message.guild:
            return False
        
        # Check if AI chat is enabled for this channel
        if not ai_chat_storage.is_enabled(message.guild.id, message.channel.id):
            return False
        
        # Simple rate limiting - max 1 response per user per 10 seconds
        user_id = message.author.id
        current_time = asyncio.get_event_loop().time()
        
        if user_id in self.rate_limits:
            if current_time - self.rate_limits[user_id] < 10:
                return False
        
        # Bot should respond if:
        # 1. Bot is mentioned
        # 2. Message is a reply to bot
        # 3. Random chance (20%) for natural conversation
        bot_mentioned = self.bot.user in message.mentions
        is_reply_to_bot = (message.reference and 
                          message.reference.message_id and 
                          message.reference.cached_message and 
                          message.reference.cached_message.author == self.bot.user)
        
        if bot_mentioned or is_reply_to_bot:
            return True
        
        # 20% chance to respond naturally (but not too spammy)
        import random
        return random.random() < 0.2
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages and respond with AI when appropriate"""
        if not self.should_respond_to_message(message):
            return
        
        # Update rate limit
        self.rate_limits[message.author.id] = asyncio.get_event_loop().time()
        
        # Show typing indicator
        async with message.channel.typing():
            # Get AI response
            ai_response = await self.get_ai_response(
                message.content,
                message.author.display_name,
                message.channel.name
            )
            
            # Small delay to seem more natural
            await asyncio.sleep(1)
            
            # Send response
            try:
                await message.reply(ai_response, mention_author=False)
                logger.info(f"AI responded to {message.author} in #{message.channel.name}")
            except discord.HTTPException as e:
                logger.error(f"Failed to send AI response: {e}")
        
        await self.bot.process_commands(message)
    
    @commands.hybrid_command(name='ai-enable')
    @app_commands.describe(channel="Channel to enable AI chat in (default: current channel)")
    @commands.guild_only()
    async def enable_ai_chat(self, ctx, channel: discord.TextChannel = None):
        """Enable AI chat replies in a channel"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to manage AI chat settings.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        target_channel = channel or ctx.channel
        
        # Check if already enabled
        if ai_chat_storage.is_enabled(ctx.guild.id, target_channel.id):
            embed = discord.Embed(
                title="ℹ️ Already Enabled",
                description=f"AI chat is already enabled in {target_channel.mention}.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Enable AI chat
        success = ai_chat_storage.set_enabled(ctx.guild.id, target_channel.id, True)
        
        if success:
            embed = discord.Embed(
                title="✅ AI Chat Enabled",
                description=f"AI chat replies are now enabled in {target_channel.mention}.\n\nThe bot will respond to:\n• Direct mentions\n• Replies to bot messages\n• Random messages (20% chance)",
                color=discord.Color.green()
            )
            embed.set_footer(text="Use /ai-disable to turn off AI chat in this channel")
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} enabled AI chat in #{target_channel.name} ({ctx.guild.name})")
        else:
            embed = discord.Embed(
                title="❌ Failed to Enable",
                description="Failed to enable AI chat. Please try again.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name='ai-disable')
    @app_commands.describe(channel="Channel to disable AI chat in (default: current channel)")
    @commands.guild_only()
    async def disable_ai_chat(self, ctx, channel: discord.TextChannel = None):
        """Disable AI chat replies in a channel"""
        # Permission check
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need moderator permissions to manage AI chat settings.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        target_channel = channel or ctx.channel
        
        # Check if already disabled
        if not ai_chat_storage.is_enabled(ctx.guild.id, target_channel.id):
            embed = discord.Embed(
                title="ℹ️ Already Disabled",
                description=f"AI chat is already disabled in {target_channel.mention}.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Disable AI chat
        success = ai_chat_storage.set_enabled(ctx.guild.id, target_channel.id, False)
        
        if success:
            embed = discord.Embed(
                title="✅ AI Chat Disabled",
                description=f"AI chat replies are now disabled in {target_channel.mention}.",
                color=discord.Color.green()
            )
            embed.set_footer(text="Use /ai-enable to turn on AI chat in this channel")
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} disabled AI chat in #{target_channel.name} ({ctx.guild.name})")
        else:
            embed = discord.Embed(
                title="❌ Failed to Disable",
                description="Failed to disable AI chat. Please try again.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name='ai-status')
    @commands.guild_only()
    async def ai_chat_status(self, ctx):
        """Show AI chat status for all channels in the server"""
        enabled_channels = ai_chat_storage.get_enabled_channels(ctx.guild.id)
        
        embed = discord.Embed(
            title="🤖 AI Chat Status",
            description=f"AI chat settings for **{ctx.guild.name}**",
            color=discord.Color.blue()
        )
        
        if enabled_channels:
            channel_mentions = []
            for channel_id in enabled_channels:
                channel = ctx.guild.get_channel(channel_id)
                if channel:
                    channel_mentions.append(channel.mention)
            
            if channel_mentions:
                embed.add_field(
                    name="✅ Enabled Channels",
                    value="\n".join(channel_mentions),
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ No Valid Channels",
                    value="AI chat is enabled for some channels but they no longer exist.",
                    inline=False
                )
        else:
            embed.add_field(
                name="❌ No Enabled Channels",
                value="AI chat is not enabled in any channels.",
                inline=False
            )
        
        embed.add_field(
            name="🔧 Commands",
            value="`/ai-enable` - Enable AI chat in a channel\n`/ai-disable` - Disable AI chat in a channel",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AIChat(bot))