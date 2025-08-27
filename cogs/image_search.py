import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import re
import urllib.parse
import logging
from utils.permissions import has_mod_permissions

logger = logging.getLogger(__name__)

class ImageSearch(commands.Cog):
    """Google image search functionality"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='image', description='Search for images on Google')
    @app_commands.describe(query='What image to search for')
    async def image_search(self, interaction: discord.Interaction, query: str):
        """Search for images using Google"""
        
        # Check if user has mod permissions
        if not has_mod_permissions(interaction.user, interaction.guild):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You need moderator permissions to use image search.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Validate query
        if not query or len(query.strip()) < 2:
            embed = discord.Embed(
                title="❌ Invalid Query",
                description="Please provide a search query with at least 2 characters.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Clean and limit query
        query = query.strip()[:100]  # Limit query length
        
        try:
            await interaction.response.defer()
            
            # Search for images
            image_urls = await self.search_google_images(query)
            
            if not image_urls:
                embed = discord.Embed(
                    title="❌ No Results",
                    description=f"No images found for: `{query}`",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Create embed with results
            embed = discord.Embed(
                title="🖼️ Image Search Results",
                description=f"Found images for: **{query}**",
                color=discord.Color.blue()
            )
            
            # Add first image as main image
            embed.set_image(url=image_urls[0])
            
            # Add additional image links if available
            if len(image_urls) > 1:
                additional_links = []
                for i, url in enumerate(image_urls[1:4], 2):  # Show up to 3 more
                    additional_links.append(f"[Image {i}]({url})")
                
                if additional_links:
                    embed.add_field(
                        name="📎 More Results",
                        value=" • ".join(additional_links),
                        inline=False
                    )
            
            embed.set_footer(text=f"Requested by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
            logger.info(f"Image search performed by {interaction.user} for: {query}")
            
        except Exception as e:
            logger.error(f"Error in image search: {e}")
            
            embed = discord.Embed(
                title="❌ Search Error",
                description="An error occurred while searching for images. Please try again later.",
                color=discord.Color.red()
            )
            
            try:
                await interaction.followup.send(embed=embed)
            except:
                await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def search_google_images(self, query: str, max_results: int = 5):
        """Search for images using Google Images"""
        try:
            # Encode the search query
            encoded_query = urllib.parse.quote_plus(query)
            
            # Google Images search URL
            url = f"https://www.google.com/search?q={encoded_query}&tbm=isch&safe=active"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        return []
                    
                    html = await response.text()
                    
                    # Extract image URLs using regex
                    # Look for image URLs in the HTML
                    image_urls = []
                    
                    # Pattern to find image URLs
                    patterns = [
                        r'"(https?://[^"]*\.(?:jpg|jpeg|png|gif|webp))"',
                        r"'(https?://[^']*\.(?:jpg|jpeg|png|gif|webp))'",
                        r'src="(https?://[^"]*)"'
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, html, re.IGNORECASE)
                        for match in matches:
                            if self.is_valid_image_url(match):
                                image_urls.append(match)
                                if len(image_urls) >= max_results:
                                    break
                        if len(image_urls) >= max_results:
                            break
                    
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_urls = []
                    for url in image_urls:
                        if url not in seen:
                            seen.add(url)
                            unique_urls.append(url)
                    
                    return unique_urls[:max_results]
                    
        except Exception as e:
            logger.error(f"Error searching Google Images: {e}")
            return []
    
    def is_valid_image_url(self, url: str) -> bool:
        """Check if URL is a valid image URL"""
        try:
            # Basic URL validation
            if not url or len(url) < 10:
                return False
            
            # Must be HTTP/HTTPS
            if not url.startswith(('http://', 'https://')):
                return False
            
            # Must end with image extension
            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')
            url_lower = url.lower()
            
            # Check if URL contains image extension
            for ext in image_extensions:
                if ext in url_lower:
                    return True
            
            return False
            
        except Exception:
            return False
    
    @commands.hybrid_command(name='image-search')
    async def image_search_prefix(self, ctx, *, query: str):
        """Prefix version of image search command"""
        
        # Check permissions
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You need moderator permissions to use image search.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Validate query
        if not query or len(query.strip()) < 2:
            embed = discord.Embed(
                title="❌ Invalid Query",
                description="Please provide a search query with at least 2 characters.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Show typing indicator
            async with ctx.typing():
                # Search for images
                image_urls = await self.search_google_images(query)
                
                if not image_urls:
                    embed = discord.Embed(
                        title="❌ No Results",
                        description=f"No images found for: `{query}`",
                        color=discord.Color.orange()
                    )
                    await ctx.send(embed=embed)
                    return
                
                # Create embed with results
                embed = discord.Embed(
                    title="🖼️ Image Search Results",
                    description=f"Found images for: **{query}**",
                    color=discord.Color.blue()
                )
                
                # Add first image as main image
                embed.set_image(url=image_urls[0])
                
                # Add additional image links if available
                if len(image_urls) > 1:
                    additional_links = []
                    for i, url in enumerate(image_urls[1:4], 2):  # Show up to 3 more
                        additional_links.append(f"[Image {i}]({url})")
                    
                    if additional_links:
                        embed.add_field(
                            name="📎 More Results",
                            value=" • ".join(additional_links),
                            inline=False
                        )
                
                embed.set_footer(text=f"Requested by {ctx.author.display_name}")
                
                await ctx.send(embed=embed)
                
                logger.info(f"Image search performed by {ctx.author} for: {query}")
                
        except Exception as e:
            logger.error(f"Error in image search: {e}")
            
            embed = discord.Embed(
                title="❌ Search Error",
                description="An error occurred while searching for images. Please try again later.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    """Setup function to add the cog to the bot"""
    await bot.add_cog(ImageSearch(bot))