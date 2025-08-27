# Discord Moderation Bot

## Overview

A comprehensive Discord moderation bot built with Python using the discord.py library. The bot provides essential moderation commands like kick, ban, mute, warn, and purge, with features including role hierarchy enforcement, persistent data storage, logging capabilities, and 24/7 uptime support. Designed specifically for deployment on Replit with a keep-alive mechanism to ensure continuous operation.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Core Technology**: Python with discord.py library for Discord API integration
- **Command System**: Uses discord.py's commands extension with prefix-based commands (default: `!`)
- **Intents Configuration**: Configured with message content, members, and guilds intents for full functionality

### Modular Design
- **Cog-based Architecture**: Separates moderation functionality into dedicated cogs for better organization and maintainability
- **Database Abstraction**: Dedicated database module handles all data persistence operations
- **Utility Functions**: Common helper functions centralized in utils module for duration parsing, embed creation, and formatting

### Data Persistence
- **Database**: SQLite with aiosqlite for asynchronous operations
- **Schema Design**: 
  - Moderation logs table for tracking all moderation actions
  - Warnings table for user warning system with active/inactive status
- **Connection Management**: Singleton pattern for database connections with proper connection lifecycle management

### Logging and Monitoring
- **Multi-level Logging**: File and console logging with configurable levels
- **Action Logging**: All moderation actions logged to database and optional Discord log channels
- **Error Handling**: Comprehensive error handling with graceful degradation for failed operations

### Deployment Architecture
- **Keep-alive System**: Flask web server prevents Replit from sleeping the application
- **Environment Configuration**: Uses environment variables for sensitive configuration like bot tokens
- **24/7 Operation**: Designed for continuous operation with automatic restart capabilities

### Permission System
- **Role Hierarchy**: Enforces Discord role hierarchy to prevent unauthorized moderation actions
- **Permission Checks**: Validates both user and bot permissions before executing commands
- **Security**: Prevents privilege escalation through role position validation

## External Dependencies

### Core Dependencies
- **discord.py**: Primary Discord API wrapper for bot functionality
- **aiosqlite**: Asynchronous SQLite database operations
- **python-dotenv**: Environment variable loading for configuration management

### Web Server
- **Flask**: Lightweight web server for keep-alive functionality and status monitoring
- **Threading**: Background thread management for concurrent web server operation

### Discord Platform
- **Discord Developer Portal**: Bot registration and token management
- **Discord Permissions**: Requires specific server permissions (kick, ban, moderate members, manage messages)
- **Discord Channels**: Integration with mod-logs channels for action logging

### Replit Platform
- **Environment Variables**: Secure storage of bot tokens and configuration
- **File System**: Persistent storage for SQLite database and log files
- **Network Access**: Outbound connections to Discord API and webhook endpoints