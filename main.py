import discord
from discord.ext import commands
import os
import asyncio
import logging
from dotenv import load_dotenv
from utils.logging_config import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    def __init__(self):
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for message commands
        intents.members = True          # Required for member operations
        intents.guilds = True           # Required for guild operations
        
        # Get command prefix from environment
        prefix = os.getenv('COMMAND_PREFIX', '!')
        
        super().__init__(
            command_prefix=prefix,
            intents=intents,
            help_command=None,  # We'll create a custom help command
            case_insensitive=True
        )
        
    async def setup_hook(self):
        """Load cogs when bot starts"""
        try:
            await self.load_extension('cogs.general')
            await self.load_extension('cogs.moderation')
            await self.load_extension('cogs.mass_dm')
            await self.load_extension('cogs.giveaways')
            await self.load_extension('cogs.spinwheel')
            await self.load_extension('cogs.warnings')
            await self.load_extension('cogs.afk')
            await self.load_extension('cogs.roles')
            await self.load_extension('cogs.settings')
            await self.load_extension('cogs.embed_builder')
            await self.load_extension('cogs.quota_system')
            await self.load_extension('cogs.sensitive')
            # await self.load_extension('cogs.ai_reply')  # Temporarily disabled to fix duplicate help responses
            logger.info("All cogs loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load cogs: {e}")
    
    async def on_ready(self):
        """Event fired when bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{os.getenv('COMMAND_PREFIX', '!')}help | /help"
            )
        )
        
        # Log guild information
        for guild in self.guilds:
            logger.info(f'Connected to guild: {guild.name} (ID: {guild.id})')
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Arguments",
                description=f"Missing required argument: `{error.param.name}`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                title="❌ Bot Missing Permissions",
                description="I don't have the required permissions to execute this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        
        else:
            logger.error(f"Unhandled error in command {ctx.command}: {error}")
            embed = discord.Embed(
                title="❌ An Error Occurred",
                description="An unexpected error occurred while processing this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

# Create and run bot
async def main():
    bot = DiscordBot()
    
    # Get Discord token from environment
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables!")
        return
    
    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid Discord token!")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
