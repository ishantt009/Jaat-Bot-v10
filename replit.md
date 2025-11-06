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
- Copy all channels from one server to another
- Copy roles between servers
- Automatic permission mapping by role names
- Support for all channel types: text, voice, stage, categories, and forums
- Administrator permission requirements for both source and target servers
- Commands:
  - `/copy_channel`: Copy a single channel to another server
  - `/copy_all_channels`: Copy all channels from source to target server
  - `/copy_roles`: Copy all roles from source to target server

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