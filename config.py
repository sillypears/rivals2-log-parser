import configparser
import os
import sys

class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        config_path = self._get_config_path()
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        self.config.read(config_path)
    
    def _get_config_path(self):
        """Get the correct path to config.ini whether running as script or exe"""
        if getattr(sys, 'frozen', False):
            # Running as exe - config should be next to the executable
            return os.path.join(os.path.dirname(sys.executable), 'config.ini')
        else:
            # Running as script
            return os.path.join(os.path.dirname(__file__), 'config.ini')
    
    # Logging settings
    @property
    def app_log_dir(self):
        if getattr(sys, 'frozen', False):
            # Running as exe - logs next to executable
            return os.path.join(os.path.dirname(sys.executable), self.config['logging']['app_log_dir'])
        else:
            # Running as script
            return os.path.abspath(os.path.join(os.path.dirname(__file__), self.config['logging']['app_log_dir']))
    
    @property
    def app_log_file(self):
        return self.config['logging']['app_file']
    
    @property
    def max_log_size(self):
        return int(self.config['logging']['max_size'])
    
    @property
    def backup_count(self):
        return int(self.config['logging']['backup_count'])
    
    @property
    def game_log_file(self):
        return self.config['game']['game_log_file']

    # Paths
    @property
    def replay_folder(self):
        return self.config['paths']['replay_folder']
    
    # Backend settings
    @property
    def be_host(self):
        return self.config['backend']['host']
    
    @property
    def be_port(self):
        return int(self.config['backend']['port'])
    
    # WebSocket settings
    @property
    def ws_host(self):
        return self.config['websocket']['host']
    
    @property
    def ws_port(self):
        return int(self.config['websocket']['port'])
    
    # App settings
    @property
    def debug(self):
        return bool(int(self.config['app']['debug']))

    @property
    def opp_dir(self):
        return int(self.config['app']['opp_default'])