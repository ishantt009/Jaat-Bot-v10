import os
import json
import threading
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from bot_manager import BotManager
from file_manager import FileManager

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize managers
bot_manager = BotManager(socketio)
file_manager = FileManager(app.config['UPLOAD_FOLDER'])

# Allowed extensions
ALLOWED_EXTENSIONS = {'py', 'txt', 'json', 'yaml', 'yml', 'md'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        uploaded_files = []
        
        for file in files:
            if file.filename == '':
                continue
                
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                uploaded_files.append({
                    'name': filename,
                    'size': os.path.getsize(filepath),
                    'type': filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
                })
            else:
                return jsonify({'error': f'File type not allowed: {file.filename}'}), 400
        
        return jsonify({
            'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
            'files': uploaded_files
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    try:
        files = file_manager.list_files()
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<filename>', methods=['GET'])
def get_file_content(filename):
    try:
        content = file_manager.read_file(filename)
        return jsonify({'content': content, 'filename': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<filename>', methods=['PUT'])
def save_file_content(filename):
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'No content provided'}), 400
        
        file_manager.write_file(filename, data['content'])
        return jsonify({'message': f'File {filename} saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        file_manager.delete_file(filename)
        return jsonify({'message': f'File {filename} deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    try:
        data = request.get_json()
        main_file = data.get('main_file', 'main.py')
        token = data.get('token') or os.getenv('DISCORD_BOT_TOKEN')
        
        if not token:
            return jsonify({'error': 'No bot token provided'}), 400
        
        result = bot_manager.start_bot(main_file, token)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    try:
        result = bot_manager.stop_bot()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/status', methods=['GET'])
def bot_status():
    try:
        status = bot_manager.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/environment', methods=['POST'])
def set_environment():
    try:
        data = request.get_json()
        env_vars = data.get('variables', {})
        
        # Update environment variables for bot execution
        bot_manager.set_environment_variables(env_vars)
        
        return jsonify({'message': 'Environment variables updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    # Send current bot status to newly connected client
    status = bot_manager.get_status()
    emit('bot_status', status)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'bot_running': bot_manager.is_running()})

if __name__ == '__main__':
    print("Starting Discord Bot Development Environment...")
    print("Server will be available at http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, log_output=True)