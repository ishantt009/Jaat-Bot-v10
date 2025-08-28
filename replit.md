# Discord Bot

## Overview

A Python-based Discord bot built with the discord.py library featuring basic command handling, event management, and message processing capabilities. The bot provides essential functionality including ping commands, help systems, welcome messages, and comprehensive logging. The architecture follows a modular design pattern separating configuration, commands, events, and main application logic into distinct modules.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure
The bot follows a modular architecture with clear separation of concerns:
- **Main Entry Point** (`main.py`): Custom bot class extending discord.py's commands.Bot with proper intent configuration
- **Commands Module** (`bot/commands.py`): Centralized command handlers using discord.py's command framework
- **Events Module** (`bot/events.py`): Event listeners for Discord events like guild joins and message handling
- **Configuration Module** (`bot/config.py`): Environment-based configuration management with validation

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
Uses discord.py's command framework with:
- Decorator-based command registration
- Embed-based responses for rich message formatting
- Error handling and validation built into command structure
- Modular command organization for easy maintenance

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