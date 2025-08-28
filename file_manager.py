import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

class FileManager:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        
    def list_files(self):
        """List all files in the upload directory with metadata"""
        files = []
        
        try:
            for filename in os.listdir(self.upload_folder):
                filepath = os.path.join(self.upload_folder, filename)
                
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    file_info = {
                        'name': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'type': self._get_file_type(filename),
                        'is_python': filename.endswith('.py')
                    }
                    files.append(file_info)
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            raise Exception(f"Failed to list files: {str(e)}")
        
        return files
    
    def read_file(self, filename):
        """Read file content"""
        secure_name = secure_filename(filename)
        filepath = os.path.join(self.upload_folder, secure_name)
        
        if not os.path.exists(filepath):
            raise Exception(f"File {filename} not found")
        
        if not os.path.isfile(filepath):
            raise Exception(f"{filename} is not a file")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding for binary files
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Failed to read file {filename}: {str(e)}")
    
    def write_file(self, filename, content):
        """Write content to file"""
        secure_name = secure_filename(filename)
        filepath = os.path.join(self.upload_folder, secure_name)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Failed to write file {filename}: {str(e)}")
    
    def delete_file(self, filename):
        """Delete a file"""
        secure_name = secure_filename(filename)
        filepath = os.path.join(self.upload_folder, secure_name)
        
        if not os.path.exists(filepath):
            raise Exception(f"File {filename} not found")
        
        try:
            os.remove(filepath)
        except Exception as e:
            raise Exception(f"Failed to delete file {filename}: {str(e)}")
    
    def create_file(self, filename, content=""):
        """Create a new file"""
        secure_name = secure_filename(filename)
        filepath = os.path.join(self.upload_folder, secure_name)
        
        if os.path.exists(filepath):
            raise Exception(f"File {filename} already exists")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Failed to create file {filename}: {str(e)}")
    
    def _get_file_type(self, filename):
        """Determine file type based on extension"""
        if '.' not in filename:
            return 'unknown'
        
        extension = filename.rsplit('.', 1)[1].lower()
        
        type_mapping = {
            'py': 'python',
            'txt': 'text',
            'json': 'json',
            'yaml': 'yaml',
            'yml': 'yaml',
            'md': 'markdown',
            'requirements': 'requirements'
        }
        
        return type_mapping.get(extension, extension)