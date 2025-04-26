import os
import logging
import tempfile
import shutil
import time

logger = logging.getLogger(__name__)

def process_mp3(input_file):
    """Process MP3 file"""
    try:
        # Validate file format
        if not input_file.lower().endswith('.mp3'):
            raise Exception("Only MP3 format is supported")
            
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"temp_audio_{int(time.time())}.mp3")
        
        # Copy file to temporary directory
        shutil.copy2(input_file, temp_file)
        
        # Validate file
        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
            return temp_file
        else:
            raise Exception("File processing failed")
            
    except Exception as e:
        logger.error(f"MP3 file processing failed: {str(e)}")
        raise 