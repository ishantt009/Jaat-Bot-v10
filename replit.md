# Discord Bot Development Environment

## Overview

A comprehensive Discord bot framework built with Python and discord.py, featuring a modular cog-based architecture. The project provides a complete foundation for building Discord bots with built-in moderation tools, event handling, logging systems, and extensible command structures. The bot supports both development and production deployments with configurable features and robust error handling.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure
The bot follows a modular architecture pattern using discord.py's cog system:

- **Main Bot Class (`bot/bot.py`)**: Central bot instance that manages initialization, event setup, and cog loading
- **Configuration Management (`bot/config.py`)**: Centralized configuration using environment variables with validation and type checking
- **Modular Commands**: Organized into separate cogs for different functionality domains (general, moderation, events)
- **Utility Layer**: Shared helper functions and logging infrastructure

### Command Organization
Commands are organized into logical cogs:

- **General Cog**: Basic utility commands (ping, info, stats)
- **Moderation Cog**: Administrative commands with permission checking and role hierarchy validation
- **Events Cog**: Discord event handlers for member join/leave, message events, and server activities

### Logging System
Comprehensive logging architecture with:

- **Dual Output**: Both console and file logging support
- **Structured Formatting**: Different formatters for console vs file output
- **Configurable Levels**: Environment-controlled log levels
- **Centralized Management**: Single setup function for consistent logging across all modules

### Security & Permissions
- **Environment-based Configuration**: Sensitive data stored in environment variables
- **Permission Validation**: Role-based permission checking for moderation commands
- **Hierarchy Enforcement**: Prevents users from moderating higher-ranked members

### Error Handling
- **Graceful Degradation**: Proper error handling for missing permissions or invalid operations
- **User-friendly Messages**: Clear feedback for command failures
- **Comprehensive Logging**: Detailed error tracking for debugging

## External Dependencies

### Core Framework
- **discord.py**: Primary Discord API library for bot functionality
- **python-dotenv**: Environment variable management from .env files

### System Utilities
- **psutil**: System information gathering for bot stats and monitoring
- **asyncio**: Asynchronous programming support for Discord operations

### Development Tools
- **logging**: Python's built-in logging framework for comprehensive log management
- **pathlib**: Modern path handling for cross-platform file operations

### Discord Integration
- **Discord Intents**: Message content, member, and guild intents for full functionality
- **Bot Permissions**: Configurable permission system for moderation features
- **Event Handling**: Real-time Discord event processing and response