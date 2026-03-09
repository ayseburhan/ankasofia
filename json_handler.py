import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path


class JSONHandler:
    """Basit ve güvenli JSON yönetimi"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "backups").mkdir(exist_ok=True)
    
    def read_json(self, filepath):
        """JSON oku, yoksa boş dict döndür"""
        full_path = self.data_dir / filepath
        try:
            if not full_path.exists():
                return {}
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def write_json(self, filepath, data):
        """Atomic write: önce temp'e yaz, sonra taşı"""
        full_path = self.data_dir / filepath
        try:
            # Backup al
            if full_path.exists():
                backup_name = f"{full_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{full_path.suffix}"
                shutil.copy(full_path, self.data_dir / "backups" / backup_name)
            
            # Atomic write
            temp_fd, temp_path = tempfile.mkstemp(dir=full_path.parent)
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            shutil.move(temp_path, full_path)
            return True
        except:
            return False
    
    def load_settings(self):
        """Ayarları yükle"""
        defaults = {
            "theme": "turbo_pascal_blue",
            "font_size": 16,
            "font_family": "Consolas, monospace",
            "auto_save": True,
            "line_numbers": True,
            "word_wrap": True
        }
        saved = self.read_json("settings.json")
        return {**defaults, **saved}
    
    def save_settings(self, settings):
        """Ayarları kaydet"""
        return self.write_json("settings.json", settings)
    
    def load_tasks(self):
        """Görevleri yükle"""
        defaults = {"tasks": []}
        saved = self.read_json("tasks.json")
        return {**defaults, **saved}
    
    def save_tasks(self, tasks):
        """Görevleri kaydet"""
        return self.write_json("tasks.json", tasks)