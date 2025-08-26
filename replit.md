# Discord Moderation Bot

## Overview

This is a comprehensive Discord moderation bot built with Python using the discord.py library. The bot provides essential server management features including moderation commands (kick, ban, mute), mass DM functionality for administrators, and general utility commands. The application is designed with a modular cog-based architecture that separates functionality into logical components for maintainability and scalability.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Framework and Structure
- **Framework**: Built on discord.py with the commands extension for structured command handling
- **Architecture Pattern**: Modular cog-based design that separates functionality into distinct modules
- **Bot Class**: Custom `DiscordBot` class extending `commands.Bot` with automatic cog loading and configuration management

### Command Organization
The bot uses a cog system to organize commands into three main categories:
- **General Cogs** (`cogs/general.py`): Basic utility commands like ping, help, and bot information
- **Moderation Cogs** (`cogs/moderation.py`): Server management commands for kicking, banning, and muting users
- **Mass DM Cogs** (`cogs/mass_dm.py`): Bulk messaging functionality for administrators

### Permission System
- **Role-based Access Control**: Custom permission system in `utils/permissions.py` that checks for administrator and moderator permissions
- **Hierarchical Permissions**: Server owners have full access, followed by users with administrator permissions, then users with specific moderation permissions or designated roles
- **Environment-configurable Roles**: Admin and moderator role names can be customized via environment variables

### Configuration Management
- **Environment Variables**: Uses python-dotenv for configuration management including bot tokens, command prefixes, and role names
- **Rate Limiting**: Configurable rate limiting for mass DM operations to prevent API abuse
- **Intent Configuration**: Properly configured Discord intents for message content, member operations, and guild access

### Logging and Monitoring
- **Comprehensive Logging**: Multi-level logging system with separate handlers for console output, general logs, and error logs
- **Log Rotation**: Automatic log file rotation to prevent disk space issues
- **Structured Logging**: Consistent log formatting with timestamps, log levels, and module identification

### Error Handling and Safety
- **Permission Validation**: All moderation commands include permission checks before execution
- **Confirmation Systems**: Mass DM operations require explicit user confirmation to prevent accidental bulk messages
- **Role Management**: Automatic creation and configuration of muted roles with proper channel permissions

## External Dependencies

### Core Libraries
- **discord.py**: Primary Discord API wrapper for bot functionality and event handling
- **python-dotenv**: Environment variable management for secure configuration storage
- **psutil**: System monitoring for bot performance metrics and uptime tracking

### Discord API Integration
- **Bot Token Authentication**: Requires Discord bot token from Discord Developer Portal
- **Gateway Intents**: Uses message content, members, and guilds intents for full functionality
- **Rate Limiting Compliance**: Built-in respect for Discord API rate limits, especially for bulk operations

### Runtime Environment
- **Python 3.8+**: Minimum Python version requirement for async/await support and modern language features
- **File System**: Local file system used for log storage and rotation management
- **Process Monitoring**: Integration with system process monitoring for uptime and performance tracking