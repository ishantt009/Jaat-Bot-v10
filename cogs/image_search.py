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
    """Google image and video search functionality"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='image', description='Search for images on Google')
    @app_commands.describe(query='What image to search for')
    async def image_search(self, interaction: discord.Interaction, query: str):
        """Search for images using Google"""
        
        # Check if user has mod permissions (only in guilds)
        if not interaction.guild:
            embed = discord.Embed(
                title="❌ Server Only",
                description="This command can only be used in servers.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Convert User to Member if needed
        member = interaction.user
        if not isinstance(member, discord.Member):
            member = interaction.guild.get_member(interaction.user.id)
            if not member:
                embed = discord.Embed(
                    title="❌ Member Not Found",
                    description="Could not verify your server membership.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        if not has_mod_permissions(member, interaction.guild):
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
    
    @app_commands.command(name='video', description='Search for videos on YouTube/Google')
    @app_commands.describe(query='What video to search for')
    async def video_search(self, interaction: discord.Interaction, query: str):
        """Search for videos using Google/YouTube"""
        
        # Check if user has mod permissions (only in guilds)
        if not interaction.guild:
            embed = discord.Embed(
                title="❌ Server Only",
                description="This command can only be used in servers.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Convert User to Member if needed
        member = interaction.user
        if not isinstance(member, discord.Member):
            member = interaction.guild.get_member(interaction.user.id)
            if not member:
                embed = discord.Embed(
                    title="❌ Member Not Found",
                    description="Could not verify your server membership.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        if not has_mod_permissions(member, interaction.guild):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You need moderator permissions to use video search.",
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
        query = query.strip()[:100]
        
        try:
            await interaction.response.defer()
            
            # Search for videos
            video_results = await self.search_google_videos(query)
            
            if not video_results:
                embed = discord.Embed(
                    title="❌ No Results",
                    description=f"No videos found for: `{query}`\n\nThis could be due to:\n• Google blocking the request\n• No valid video URLs found\n• Video search temporarily unavailable",
                    color=discord.Color.orange()
                )
                embed.set_footer(text="Try a different search term or try again later")
                await interaction.followup.send(embed=embed)
                return
            
            # Create embed with video result
            video = video_results[0]
            embed = discord.Embed(
                title="🎬 Video Search",
                description=f"**{query}**",
                color=discord.Color.red()  # YouTube red
            )
            
            # Add video information
            if video.get('title'):
                embed.add_field(name="📺 Title", value=video['title'][:100], inline=False)
            
            if video.get('url'):
                embed.add_field(name="🔗 Link", value=f"[Watch Video]({video['url']})", inline=True)
            
            if video.get('duration'):
                embed.add_field(name="⏱️ Duration", value=video['duration'], inline=True)
            
            # Set thumbnail if available
            if video.get('thumbnail'):
                embed.set_image(url=video['thumbnail'])
            
            embed.set_footer(text=f"Requested by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
            logger.info(f"Video search performed by {interaction.user} for: {query}")
            
        except Exception as e:
            logger.error(f"Error in video search: {e}")
            
            embed = discord.Embed(
                title="❌ Search Error",
                description="An error occurred while searching for videos. Please try again later.",
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
            
            # Google Images search URL with better parameters (no safe search)
            url = f"https://www.google.com/search?q={encoded_query}&tbm=isch&tbs=isz:m"
            
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
    
    async def search_google_videos(self, query: str, max_results: int = 1):
        """Search for videos using Google/YouTube"""
        try:
            # Encode the search query
            encoded_query = urllib.parse.quote_plus(query)
            
            # Google Video search URL (no safe search)
            url = f"https://www.google.com/search?q={encoded_query}&tbm=vid"
            
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
                        logger.warning(f"Google Videos returned status {response.status}")
                        return []
                    
                    html = await response.text()
                    
                    # Extract video information
                    videos = []
                    
                    # Updated patterns to find YouTube videos and other video sources
                    youtube_patterns = [
                        r'href="(/url\?q=https://www\.youtube\.com/watch\?v=([^"&]+))',
                        r'"https://www\.youtube\.com/watch\?v=([^"&]+)"',
                        r'/watch\?v=([^"&\s]+)',
                        r'watch\?v=([A-Za-z0-9_-]{11})'
                    ]
                    
                    title_patterns = [
                        r'<h3[^>]*><a[^>]*>([^<]+)</a></h3>',
                        r'"title":"([^"]+)"',
                        r'<a[^>]*title="([^"]+)"[^>]*>'
                    ]
                    
                    duration_pattern = r'<span[^>]*>(\d+:\d+)</span>'
                    thumbnail_pattern = r'<img[^>]*src="(https://i\.ytimg\.com/[^"]+)"'
                    
                    # Find YouTube URLs using multiple patterns
                    youtube_matches = []
                    video_ids = set()  # To avoid duplicates
                    
                    for pattern in youtube_patterns:
                        matches = re.findall(pattern, html)
                        for match in matches:
                            if isinstance(match, tuple):
                                video_id = match[1] if len(match) > 1 else match[0]
                            else:
                                video_id = match
                            
                            if len(video_id) == 11 and video_id not in video_ids:  # YouTube video IDs are 11 chars
                                video_ids.add(video_id)
                                youtube_matches.append(('', video_id))
                    
                    # Find titles using multiple patterns
                    titles = []
                    for pattern in title_patterns:
                        found_titles = re.findall(pattern, html, re.DOTALL)
                        titles.extend(found_titles)
                        if len(titles) >= len(youtube_matches):
                            break
                    
                    durations = re.findall(duration_pattern, html)
                    thumbnails = re.findall(thumbnail_pattern, html)
                    
                    # Combine results
                    for i, (url_part, video_id) in enumerate(youtube_matches[:max_results]):
                        video_data = {
                            'url': f'https://www.youtube.com/watch?v={video_id}',
                            'title': titles[i] if i < len(titles) else 'Video',
                            'duration': durations[i] if i < len(durations) else None,
                            'thumbnail': thumbnails[i] if i < len(thumbnails) else None,
                            'platform': 'YouTube'
                        }
                        videos.append(video_data)
                        
                        if len(videos) >= max_results:
                            break
                    
                    # If no YouTube results, try direct YouTube search or fallback
                    if not videos and query:
                        # Create a fallback YouTube search URL
                        fallback_video = {
                            'url': f'https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}',
                            'title': f'YouTube search for "{query}"',
                            'duration': None,
                            'thumbnail': None,
                            'platform': 'YouTube Search'
                        }
                        videos.append(fallback_video)
                        logger.info(f"Using fallback YouTube search for '{query}'")
                        
                    # Also try other video platforms if still no results
                    if len(videos) == 0:
                        general_patterns = [
                            r'href="([^"]*(?:vimeo\.com|dailymotion\.com|twitch\.tv)[^"]*)"',
                            r'"(https://[^"]*\.(?:mp4|avi|mov|wmv|flv|webm))"'
                        ]
                        
                        for pattern in general_patterns:
                            matches = re.findall(pattern, html, re.IGNORECASE)
                            for match in matches:
                                if self.is_valid_video_url(match):
                                    video_data = {
                                        'url': match,
                                        'title': f'Video for "{query}"',
                                        'duration': None,
                                        'thumbnail': None,
                                        'platform': 'Other'
                                    }
                                    videos.append(video_data)
                                    if len(videos) >= max_results:
                                        break
                            if len(videos) >= max_results:
                                break
                    
                    # Debug logging
                    logger.info(f"Video search for '{query}': Found {len(youtube_matches)} video IDs, {len(titles)} titles")
                    if videos:
                        logger.info(f"Found {len(videos)} video results for '{query}': {videos[0]['url']}")
                    else:
                        logger.warning(f"No valid video results found for '{query}' - debug info: {len(video_ids)} unique IDs found")
                    
                    return videos
                    
        except Exception as e:
            logger.error(f"Error searching Google Videos: {e}")
            return []
    
    def is_valid_video_url(self, url: str) -> bool:
        """Check if URL is a valid video URL"""
        try:
            if not url or len(url) < 10:
                return False
            
            if not url.startswith(('http://', 'https://')):
                return False
            
            # Video platforms
            video_domains = [
                'youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com',
                'twitch.tv', 'facebook.com/watch', 'instagram.com/p/',
                'tiktok.com', 'streamable.com'
            ]
            
            # Video file extensions
            video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
            
            url_lower = url.lower()
            
            # Check for video platforms
            for domain in video_domains:
                if domain in url_lower:
                    return True
            
            # Check for video file extensions
            for ext in video_extensions:
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
    
    @commands.hybrid_command(name='video-search')
    async def video_search_prefix(self, ctx, *, query: str):
        """Prefix version of video search command"""
        
        # Check permissions
        if not has_mod_permissions(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You need moderator permissions to use video search.",
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
                # Search for videos
                video_results = await self.search_google_videos(query)
                
                if not video_results:
                    embed = discord.Embed(
                        title="❌ No Results",
                        description=f"No videos found for: `{query}`\n\nThis could be due to:\n• Google blocking the request\n• No valid video URLs found\n• Video search temporarily unavailable",
                        color=discord.Color.orange()
                    )
                    embed.set_footer(text="Try a different search term or try again later")
                    await ctx.send(embed=embed)
                    return
                
                # Create embed with video result
                video = video_results[0]
                embed = discord.Embed(
                    title="🎬 Video Search",
                    description=f"**{query}**",
                    color=discord.Color.red()  # YouTube red
                )
                
                # Add video information
                if video.get('title'):
                    embed.add_field(name="📺 Title", value=video['title'][:100], inline=False)
                
                if video.get('url'):
                    embed.add_field(name="🔗 Link", value=f"[Watch Video]({video['url']})", inline=True)
                
                if video.get('duration'):
                    embed.add_field(name="⏱️ Duration", value=video['duration'], inline=True)
                
                # Set thumbnail if available
                if video.get('thumbnail'):
                    embed.set_image(url=video['thumbnail'])
                
                embed.set_footer(text=f"Requested by {ctx.author.display_name}")
                
                await ctx.send(embed=embed)
                
                logger.info(f"Video search performed by {ctx.author} for: {query}")
                
        except Exception as e:
            logger.error(f"Error in video search: {e}")
            
            embed = discord.Embed(
                title="❌ Search Error",
                description="An error occurred while searching for videos. Please try again later.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    """Setup function to add the cog to the bot"""
    await bot.add_cog(ImageSearch(bot))