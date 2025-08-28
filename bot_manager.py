import os
import subprocess
import threading
import time
import psutil
from datetime import datetime
import signal

class BotManager:
    def __init__(self, socketio):
        self.socketio = socketio
        self.process = None
        self.log_thread = None
        self.running = False
        self.start_time = None
        self.environment_vars = {}
        self.current_file = None
        
    def start_bot(self, main_file, token):
        """Start the Discord bot process"""
        if self.is_running():
            return {'error': 'Bot is already running'}
        
        main_file_path = os.path.join('uploads', main_file)
        if not os.path.exists(main_file_path):
            return {'error': f'Main file {main_file} not found'}
        
        try:
            # Prepare environment variables
            env = os.environ.copy()
            env['DISCORD_BOT_TOKEN'] = token
            env.update(self.environment_vars)
            
            # Start the bot process
            self.process = subprocess.Popen(
                ['python', main_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                env=env,
                cwd='uploads'
            )
            
            self.running = True
            self.start_time = datetime.now()
            self.current_file = main_file
            
            # Start log monitoring thread
            self.log_thread = threading.Thread(target=self._monitor_logs)
            self.log_thread.daemon = True
            self.log_thread.start()
            
            # Emit status update
            self.socketio.emit('bot_status', self.get_status())
            
            return {
                'message': f'Bot started successfully with {main_file}',
                'pid': self.process.pid,
                'status': 'running'
            }
            
        except Exception as e:
            self.running = False
            return {'error': f'Failed to start bot: {str(e)}'}
    
    def stop_bot(self):
        """Stop the Discord bot process"""
        if not self.is_running():
            return {'message': 'Bot is not running'}
        
        try:
            # Terminate the process gracefully
            if self.process:
                self.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    self.process.kill()
                    self.process.wait()
            
            self.running = False
            self.process = None
            self.start_time = None
            
            # Emit status update
            self.socketio.emit('bot_status', self.get_status())
            self.socketio.emit('bot_log', {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': 'Bot stopped by user'
            })
            
            return {'message': 'Bot stopped successfully'}
            
        except Exception as e:
            return {'error': f'Failed to stop bot: {str(e)}'}
    
    def is_running(self):
        """Check if bot process is running"""
        if not self.process:
            return False
        
        # Check if process is still alive
        if self.process.poll() is not None:
            self.running = False
            return False
        
        return self.running
    
    def get_status(self):
        """Get current bot status and statistics"""
        status = {
            'running': self.is_running(),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'current_file': self.current_file,
            'pid': self.process.pid if self.process else None,
            'uptime': None,
            'memory_usage': None,
            'cpu_usage': None
        }
        
        if self.is_running() and self.process:
            # Calculate uptime
            if self.start_time:
                uptime_seconds = (datetime.now() - self.start_time).total_seconds()
                status['uptime'] = int(uptime_seconds)
            
            # Get resource usage
            try:
                process = psutil.Process(self.process.pid)
                status['memory_usage'] = process.memory_info().rss / 1024 / 1024  # MB
                status['cpu_usage'] = process.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return status
    
    def set_environment_variables(self, env_vars):
        """Set environment variables for bot execution"""
        self.environment_vars = env_vars.copy()
    
    def _monitor_logs(self):
        """Monitor bot process logs and emit them via WebSocket"""
        if not self.process:
            return
        
        try:
            if self.process.stdout:
                for line in iter(self.process.stdout.readline, ''):
                    if not line:
                        break
                    
                    # Parse log line and emit
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'level': self._detect_log_level(line),
                        'message': line.strip()
                    }
                    
                    self.socketio.emit('bot_log', log_entry)
                    
                    # Check if process is still running
                    if self.process.poll() is not None:
                        break
            
            # Process has ended
            if self.is_running():
                self.running = False
                self.socketio.emit('bot_status', self.get_status())
                self.socketio.emit('bot_log', {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'WARNING',
                    'message': 'Bot process ended unexpectedly'
                })
                
        except Exception as e:
            self.socketio.emit('bot_log', {
                'timestamp': datetime.now().isoformat(),
                'level': 'ERROR',
                'message': f'Log monitoring error: {str(e)}'
            })
    
    def _detect_log_level(self, line):
        """Detect log level from log line"""
        line_upper = line.upper()
        if 'ERROR' in line_upper or 'EXCEPTION' in line_upper:
            return 'ERROR'
        elif 'WARNING' in line_upper or 'WARN' in line_upper:
            return 'WARNING'
        elif 'INFO' in line_upper:
            return 'INFO'
        elif 'DEBUG' in line_upper:
            return 'DEBUG'
        else:
            return 'INFO'