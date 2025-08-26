import discord
import os

def has_mod_permissions(member: discord.Member, guild: discord.Guild) -> bool:
    """Check if a member has moderation permissions"""
    # Server owner always has permissions
    if member == guild.owner:
        return True
    
    # Check for administrator permission
    if member.guild_permissions.administrator:
        return True
    
    # Check for specific moderation permissions
    mod_perms = [
        member.guild_permissions.kick_members,
        member.guild_permissions.ban_members,
        member.guild_permissions.manage_messages,
        member.guild_permissions.manage_roles
    ]
    
    if any(mod_perms):
        return True
    
    # Check for moderator role
    mod_role_name = os.getenv('MODERATOR_ROLE_NAME', 'Moderator')
    mod_role = discord.utils.get(guild.roles, name=mod_role_name)
    if mod_role and mod_role in member.roles:
        return True
    
    # Check for admin role
    admin_role_name = os.getenv('ADMIN_ROLE_NAME', 'Admin')
    admin_role = discord.utils.get(guild.roles, name=admin_role_name)
    if admin_role and admin_role in member.roles:
        return True
    
    return False

def has_admin_permissions(member: discord.Member, guild: discord.Guild) -> bool:
    """Check if a member has administrator permissions"""
    # Server owner always has permissions
    if member == guild.owner:
        return True
    
    # Check for administrator permission
    if member.guild_permissions.administrator:
        return True
    
    # Check for admin role
    admin_role_name = os.getenv('ADMIN_ROLE_NAME', 'Admin')
    admin_role = discord.utils.get(guild.roles, name=admin_role_name)
    if admin_role and admin_role in member.roles:
        return True
    
    return False

def can_moderate_member(moderator: discord.Member, target: discord.Member, guild: discord.Guild) -> bool:
    """Check if a moderator can moderate a target member based on role hierarchy"""
    # Server owner can moderate anyone
    if moderator == guild.owner:
        return True
    
    # Cannot moderate yourself
    if moderator == target:
        return False
    
    # Cannot moderate the server owner
    if target == guild.owner:
        return False
    
    # Check role hierarchy
    if moderator.top_role <= target.top_role:
        return False
    
    return True
