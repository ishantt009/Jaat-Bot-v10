# Overview

This is a Discord bot development environment built with Python and discord.py. It provides a complete, production-ready foundation for creating Discord bots with both text commands (prefix-based) and slash commands support. The project emphasizes modularity, proper error handling, and development-friendly features like hot reloading and comprehensive logging.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Bot Architecture
- **Main Bot Class**: `DiscordBot` extends `commands.Bot` with enhanced functionality and configuration management
- **Modular Design**: Commands and events are organized into separate cogs (modules) for better maintainability
- **Dual Command System**: Supports both traditional text commands (`!ping`) and modern slash commands (`/ping`)
- **Configuration Management**: Environment-based configuration using `Config` class with `.env` file support

## Command Structure
- **Cog-based Organization**: Commands are grouped into logical categories (basic, admin) using discord.py's Cog system
- **Permission Handling**: Built-in permission checks, especially for admin commands
- **Error Handling**: Comprehensive error handling with user-friendly error messages and logging

## Event System
- **Event Handlers**: Organized into separate modules (ready, message, error events)
- **Automatic Processing**: Message events automatically process both regular messages and commands
- **Bot Mentions**: Special handling for when the bot is mentioned in messages
- **Guild Management**: Tracks bot joining/leaving servers with proper logging

## Logging System
- **Structured Logging**: Multi-level logging (DEBUG, INFO, WARNING, ERROR, CRITICAL) with timestamps
- **Bot-specific Logger**: Custom `BotLogger` class for Discord-specific events
- **Console and File Output**: Configurable output to console and optional file logging
- **Debug Mode**: Enhanced logging and error reporting in development mode

## Configuration Management
- **Environment Variables**: All sensitive data (tokens, URLs) stored in environment variables
- **Development vs Production**: Different behaviors based on debug flag
- **Validation**: Configuration validation to ensure required settings are present
- **Extensible Settings**: Easy to add new configuration options

## Entry Points
- **Multiple Entry Points**: Both `main.py` and `run.py` for flexibility in deployment
- **Graceful Startup**: Proper initialization sequence with validation and error handling
- **Clean Shutdown**: Handles interrupts and errors gracefully

# External Dependencies

## Core Framework
- **discord.py**: Primary Discord API wrapper for bot functionality
- **asyncio**: Built-in Python library for asynchronous programming

## Configuration Management
- **python-dotenv**: Loads environment variables from `.env` files for local development

## Logging
- **Built-in logging**: Uses Python's standard logging module with custom formatting

## Development Tools
- **Hot Reloading**: Built-in extension reloading for development
- **Debug Mode**: Enhanced error reporting and logging during development

## Discord Integration
- **Bot Intents**: Configured for message content, guild access, and message handling
- **Application Commands**: Full slash command support with Discord's application command system
- **Presence Management**: Dynamic presence updates showing server count and help information