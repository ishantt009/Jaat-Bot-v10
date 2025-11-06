# Discord Bot

## Overview

A Python-based Discord bot built with the discord.py library featuring comprehensive command handling, event management, and server management capabilities. The bot provides extensive functionality including server cloning, moderation tools, mass messaging, giveaways, role management, AI chat integration, and more. The architecture follows a modular cog-based design pattern with each feature organized into separate cogs for maintainability.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure
The bot follows a modular cog-based architecture with clear separation of concerns:
- **Main Entry Point** (`main.py`): Custom bot class extending discord.py's commands.Bot with proper intent configuration and cog loading
- **Cogs System** (`cogs/`): Each feature is organized into separate cog files:
  - `server_clone.py`: Server channel and permission cloning between servers
  - `moderation.py`: Moderation tools (kick, ban, timeout, purge)
  - `roles.py`: Role management and mass role assignment
  - `mass_dm.py`: Mass messaging capabilities
  - `giveaways.py`: Giveaway management system
  - `warnings.py`: User warning system
  - `afk.py`: AFK status management
  - `ai_chat.py`: AI chat integration with OpenAI
  - `embed_builder.py`: Custom embed creation
  - `quota_system.py`: Staff quota tracking
  - `sensitive.py`: Sensitive content management
  - `image_search.py`: Image and video search functionality
  - `spinwheel.py`: Spinwheel feature
  - `settings.py`: Server settings management
  - `general.py`: General utility commands
- **Utilities** (`utils/`): Shared utility functions and logging configuration

### Framework Choice
Built on discord.py library which provides:
- Robust async/await pattern for handling Discord's WebSocket connections
- Built-in command framework with decorators for easy command registration
- Comprehensive event system for reacting to Discord events
- Built-in error handling and rate limiting

### Configuration Management
Uses python-dotenv for environment variable management:
- Bot token and sensitive data stored in environment variables
- Configurable command prefixes and bot settings
- Configuration validation to ensure required settings are present

### Logging Architecture
Implements dual logging approach:
- File-based logging (`bot.log`) for persistent storage
- Console logging for real-time monitoring during development
- Structured logging format with timestamps and log levels

### Command System
Uses discord.py's slash command framework with:
- App command (slash command) registration via `@app_commands.command()` decorators
- Embed-based responses for rich message formatting
- Permission checks and validation built into command structure
- Modular cog-based organization for easy maintenance and hot-reloading

### Recent Features (November 2025)

**Server Cloning System** (`cogs/server_clone.py`):
- Copy individual channels between servers with full permission preservation
- Copy all channels from one server to another with automatic role copying
- Copy roles between servers
- Case-insensitive role name mapping for accurate permission preservation
- Role hierarchy preservation to maintain permission inheritance
- Support for all channel types: text, voice, stage, categories, and forums
- Administrator permission requirements for both source and target servers
- Commands:
  - `/copy-channel`: Copy a single channel to another server
  - `/copy-all-channels`: Copy all channels and roles from a source server (by ID) to the current server
  - `/copy-roles`: Copy all roles from source to target server

**Per-Guild Embed Storage System** (`cogs/embed_builder.py`):
- Embed IDs are now saved separately for each server instead of globally
- New embeds are automatically stored in the server where they're created
- Old embeds remain accessible through backwards-compatible fallback to "global" namespace
- Commands that use embeds:
  - `/embed`: Create and customize embeds with interactive builder
  - `/embeds`: List all embeds saved in the current server
  - `/viewembed`: View a specific saved embed
  - `/deleteembed`: Delete a saved embed
  - `/say`: Send a message or embed as the bot
  - `/saychannel`: Send a message or embed to a specific channel
  - `/dm`: Send a DM to a user

**November 6, 2025 Updates**:
- Fixed `/copy-all-channels` to correctly treat the provided server ID as the SOURCE and the execution location as the TARGET
- Added automatic role copying before channel copying to ensure all permissions are preserved
- Implemented case-insensitive role name matching to handle role name variations
- Added role position preservation to maintain role hierarchy and permission inheritance
- Updated command descriptions for clarity
- Implemented per-guild embed storage with backwards compatibility for legacy embeds

### Event Handling
Event-driven architecture handling:
- Guild join events with automatic welcome messages
- Message processing and bot mentions
- Graceful error handling for permission issues

## External Dependencies

### Core Libraries
- **discord.py**: Primary Discord API wrapper and bot framework
- **python-dotenv**: Environment variable management for configuration

### Discord API Integration
- Discord Developer Portal for bot token generation
- Discord Gateway WebSocket for real-time event handling
- Discord REST API for message sending and guild management

### Runtime Environment
- Python 3.8+ requirement for async/await and modern language features
- File system access for logging and configuration files
- Environment variable system for secure credential management