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
                    description=f"No images found for: `{query}`\n\nThis could be due to:\n• Google blocking the request\n• No valid image URLs found\n• Image search temporarily unavailable",
                    color=discord.Color.orange()
                )
                embed.set_footer(text="Try a different search term or try again later")
                await interaction.followup.send(embed=embed)
                return
            
            # Create embed with single result
            embed = discord.Embed(
                title="🖼️ Image Search",
                description=f"**{query}**",
                color=discord.Color.blue()
            )
            
            # Add the image
            embed.set_image(url=image_urls[0])
            
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
    
    async def search_google_images(self, query: str, max_results: int = 1):
        """Search for images using Google Images"""
        try:
            # Encode the search query
            encoded_query = urllib.parse.quote_plus(query)
            
            # Google Images search URL with better parameters
            url = f"https://www.google.com/search?q={encoded_query}&tbm=isch&safe=active&tbs=isz:m"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.warning(f"Google Images returned status {response.status}")
                        return []
                    
                    html = await response.text()
                    
                    # Extract image URLs using improved regex patterns
                    image_urls = []
                    
                    # Primary pattern - looks for Google Images data structure
                    primary_patterns = [
                        r'"ou":"(https?://[^"]+\.(?:jpg|jpeg|png|gif|webp))"',
                        r'\["(https?://[^"]+\.(?:jpg|jpeg|png|gif|webp))",\d+,\d+\]',
                        r'"(https?://encrypted-tbn\d*\.gstatic\.com/images\?q=tbn:[^"&]+)"'
                    ]
                    
                    for pattern in primary_patterns:
                        matches = re.findall(pattern, html, re.IGNORECASE)
                        for match in matches:
                            if self.is_valid_search_image(match):
                                image_urls.append(match)
                                if len(image_urls) >= max_results * 3:  # Get more candidates
                                    break
                        if len(image_urls) >= max_results * 3:
                            break
                    
                    # Filter out Google UI elements and small images
                    filtered_urls = []
                    for url in image_urls:
                        if self.is_actual_search_result(url):
                            filtered_urls.append(url)
                            if len(filtered_urls) >= max_results:
                                break
                    
                    # Debug logging
                    if filtered_urls:
                        logger.info(f"Found {len(filtered_urls)} valid image URLs for '{query}': {filtered_urls[0][:80]}...")
                    else:
                        logger.warning(f"No valid search result images found for '{query}' from {len(image_urls)} total URLs")
                    
                    return filtered_urls[:max_results]
                    
        except Exception as e:
            logger.error(f"Error searching Google Images: {e}")
            return []
    
    def is_valid_search_image(self, url: str) -> bool:
        """Check if URL is a valid image URL for search results"""
        try:
            # Basic URL validation
            if not url or len(url) < 10:
                return False
            
            # Must be HTTP/HTTPS
            if not url.startswith(('http://', 'https://')):
                return False
            
            # Check for image extensions or known image domains
            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')
            image_domains = ('gstatic.com', 'googleusercontent.com', 'imgur.com', 'wikimedia.org')
            url_lower = url.lower()
            
            # Check if URL contains image extension
            for ext in image_extensions:
                if ext in url_lower:
                    return True
            
            # Check for known image hosting domains
            for domain in image_domains:
                if domain in url_lower:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def is_actual_search_result(self, url: str) -> bool:
        """Filter out Google UI elements and focus on actual search results"""
        try:
            url_lower = url.lower()
            
            # Skip Google's own UI icons and small images
            ui_indicators = [
                'al-icon', 'logo', 'btn_', 'arrow', 'close', 'menu',
                'search_', 'nav_', 'footer', 'header', 'spinner'
            ]
            
            for indicator in ui_indicators:
                if indicator in url_lower:
                    return False
            
            # Skip very small images (likely UI elements)
            if 'w=16' in url_lower or 'h=16' in url_lower:
                return False
            if 'w=24' in url_lower or 'h=24' in url_lower:
                return False
            
            # Prefer actual content domains
            good_domains = [
                'imgur.com', 'wikimedia.org', 'wordpress.com',
                'blogspot.com', 'amazonaws.com', 'cloudinary.com'
            ]
            
            # Accept Google thumbnail images (they're usually good)
            if 'encrypted-tbn' in url_lower and 'gstatic.com' in url_lower:
                return True
            
            # Check for good domains
            for domain in good_domains:
                if domain in url_lower:
                    return True
            
            # Accept if it has clear image extension and reasonable length
            if any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                if len(url) > 30:  # Reasonable URL length
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
                
                # Create embed with single result
                embed = discord.Embed(
                    title="🖼️ Image Search",
                    description=f"**{query}**",
                    color=discord.Color.blue()
                )
                
                # Add the image
                embed.set_image(url=image_urls[0])
                
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