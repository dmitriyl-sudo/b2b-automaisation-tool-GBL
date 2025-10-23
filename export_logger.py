#!/usr/bin/env python3
"""
Система логирования экспортов для Telegram бота
"""

import json
import os
from datetime import datetime, date
from typing import List, Dict, Optional
import logging

class ExportLogger:
    """Класс для логирования экспортов Google Sheets"""
    
    def __init__(self, log_file: str = "exports_log.json"):
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)
    
    def log_export(self, project: str, geo: str = None, env: str = "prod", export_type: str = "single", sheet_url: str = None):
        """
        Логирует экспорт в файл
        
        Args:
            project: Название проекта
            geo: GEO (для single экспорта)
            env: Окружение (prod/stage)
            export_type: Тип экспорта (single/multi/full)
            sheet_url: URL Google Sheets файла
        """
        try:
            # Создаем запись
            export_record = {
                "timestamp": datetime.now().isoformat(),
                "date": date.today().isoformat(),
                "project": project,
                "geo": geo,
                "env": env,
                "export_type": export_type,
                "sheet_url": sheet_url
            }
            
            # Читаем существующие записи
            exports = self._read_exports()
            
            # Добавляем новую запись
            exports.append(export_record)
            
            # Сохраняем обратно
            self._write_exports(exports)
            
            self.logger.info(f"📊 Экспорт залогирован: {project} - {export_type} ({env})")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка логирования экспорта: {e}")
    
    def get_today_exports(self) -> List[Dict]:
        """Получает все экспорты за сегодня"""
        try:
            exports = self._read_exports()
            today_str = date.today().isoformat()
            
            today_exports = [
                export for export in exports 
                if export.get("date") == today_str
            ]
            
            return today_exports
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения экспортов за сегодня: {e}")
            return []
    
    def get_exports_by_date(self, target_date: date) -> List[Dict]:
        """Получает все экспорты за указанную дату"""
        try:
            exports = self._read_exports()
            date_str = target_date.isoformat()
            
            date_exports = [
                export for export in exports 
                if export.get("date") == date_str
            ]
            
            return date_exports
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения экспортов за {target_date}: {e}")
            return []
    
    def get_today_summary(self) -> Dict:
        """Получает сводку экспортов за сегодня"""
        try:
            today_exports = self.get_today_exports()
            
            if not today_exports:
                return {
                    "total": 0,
                    "projects": [],
                    "by_type": {},
                    "by_env": {},
                    "exports": []
                }
            
            # Подсчитываем статистику
            projects = list(set(export["project"] for export in today_exports))
            
            by_type = {}
            by_env = {}
            
            for export in today_exports:
                export_type = export.get("export_type", "unknown")
                env = export.get("env", "unknown")
                
                by_type[export_type] = by_type.get(export_type, 0) + 1
                by_env[env] = by_env.get(env, 0) + 1
            
            return {
                "total": len(today_exports),
                "projects": sorted(projects),
                "by_type": by_type,
                "by_env": by_env,
                "exports": today_exports
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения сводки за сегодня: {e}")
            return {"total": 0, "projects": [], "by_type": {}, "by_env": {}, "exports": []}
    
    def _read_exports(self) -> List[Dict]:
        """Читает экспорты из файла"""
        if not os.path.exists(self.log_file):
            return []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _write_exports(self, exports: List[Dict]):
        """Записывает экспорты в файл"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(exports, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"❌ Ошибка записи в файл логов: {e}")
    
    def get_latest_sheets_by_project(self) -> Dict[str, Dict]:
        """Получает последние Google Sheets ссылки для каждого проекта"""
        try:
            exports = self._read_exports()
            
            if not exports:
                return {}
            
            # Группируем по проектам и находим последние экспорты
            project_latest = {}
            
            for export in exports:
                project = export.get("project")
                sheet_url = export.get("sheet_url")
                timestamp = export.get("timestamp")
                
                if not project or not sheet_url or not timestamp:
                    continue
                
                # Если проект еще не добавлен или найден более новый экспорт
                if (project not in project_latest or 
                    timestamp > project_latest[project]["timestamp"]):
                    
                    project_latest[project] = {
                        "sheet_url": sheet_url,
                        "timestamp": timestamp,
                        "date": export.get("date"),
                        "geo": export.get("geo"),
                        "env": export.get("env"),
                        "export_type": export.get("export_type")
                    }
            
            return project_latest
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения последних ссылок: {e}")
            return {}

    def cleanup_old_exports(self, days_to_keep: int = 30):
        """Удаляет старые экспорты (старше указанного количества дней)"""
        try:
            exports = self._read_exports()
            
            # Вычисляем дату отсечения
            from datetime import timedelta
            cutoff_date = (date.today() - timedelta(days=days_to_keep)).isoformat()
            
            # Фильтруем экспорты
            filtered_exports = [
                export for export in exports
                if export.get("date", "1970-01-01") >= cutoff_date
            ]
            
            # Сохраняем отфильтрованные экспорты
            self._write_exports(filtered_exports)
            
            removed_count = len(exports) - len(filtered_exports)
            if removed_count > 0:
                self.logger.info(f"🧹 Удалено {removed_count} старых записей экспортов")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка очистки старых экспортов: {e}")

# Глобальный экземпляр логгера
export_logger = ExportLogger()

def log_export(project: str, geo: str = None, env: str = "prod", export_type: str = "single", sheet_url: str = None):
    """Удобная функция для логирования экспорта"""
    export_logger.log_export(project, geo, env, export_type, sheet_url)

def get_today_exports_summary() -> Dict:
    """Удобная функция для получения сводки за сегодня"""
    return export_logger.get_today_summary()
