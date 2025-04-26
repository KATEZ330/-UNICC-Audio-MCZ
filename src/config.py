import os
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Set local ffmpeg path
FFMPEG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg.exe')

# Analysis types
ANALYSIS_TYPES = {
    'sensitive': 'Sensitive Content Detection',
    'porn': 'Pornographic Content Detection',
    'abuse': 'Abusive Content Detection'
}

def load_api_config():
    """Load iFlytek API configuration from JSON file"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Validate required fields
        required_fields = ['app_id', 'api_key', 'api_secret']
        for field in required_fields:
            if field not in config or not config[field]:
                raise ValueError(f"Missing or empty required field: {field}")
                
        logging.info("API configuration loaded successfully")
        return config
        
    except FileNotFoundError:
        logging.error("API configuration file not found")
        raise
    except json.JSONDecodeError:
        logging.error("Invalid JSON format in API configuration file")
        raise
    except Exception as e:
        logging.error(f"Error loading API configuration: {str(e)}")
        raise 