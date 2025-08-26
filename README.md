# Discord Moderation Bot

A comprehensive Discord bot built with Python and discord.py that provides moderation commands and mass DM functionality.

## Features

### 🤖 General Commands
- `!ping` - Check bot latency
- `!hello` - Greet the bot
- `!help [command]` - Show help information
- `!info` - Display bot information and statistics
- `!uptime` - Show bot uptime

### 🔨 Moderation Commands
- `!kick <user> [reason]` - Kick a user from the server
- `!ban <user> [reason]` - Ban a user from the server
- `!unban <user>` - Unban a user from the server
- `!mute <user> [reason]` - Mute a user (creates/uses "Muted" role)
- `!unmute <user>` - Unmute a user

### 📨 Mass DM Commands
- `!massdm <message>` - Send a DM to all server members (Admin only)
- `!massrole <role> <message>` - Send a DM to all members with a specific role (Admin only)

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- A Discord bot token from the [Discord Developer Portal](https://discord.com/developers/applications)

### 2. Installation

Clone or download this project and install the required dependencies:

```bash
# Install required packages
pip install discord.py python-dotenv psutil
