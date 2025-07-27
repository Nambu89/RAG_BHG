# src/utils/logger.py

import logging
import colorlog
from pathlib import Path
from datetime import datetime
import json
from typing import Any, Dict, Optional
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import traceback

from ..config.settings import settings

# Crear directorio de logs si no existe
log_dir = Path(settings.logging.log_file).parent
log_dir.mkdir(parents=True, exist_ok=True)

# Configuración de formato para consola (con colores)
console_formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
)

# Configuración de formato para archivo (sin colores)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Formato JSON para logs estructurados
class JSONFormatter(logging.Formatter):
    """Formateador JSON para logs estructurados"""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'process_id': record.process,
            'thread_id': record.thread,
        }
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_obj['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        # Agregar campos personalizados si existen
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info']:
                log_obj[key] = value
                
        return json.dumps(log_obj, ensure_ascii=False)

# Configuración global del logger
def setup_logging():
    """Configura el sistema de logging global"""
    
    # Logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.logging.log_level))
    
    # Limpiar handlers existentes
    root_logger.handlers = []
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(getattr(logging, settings.logging.log_level))
    root_logger.addHandler(console_handler)
    
    # Handler para archivo principal (rotación por tamaño)
    file_handler = RotatingFileHandler(
        settings.logging.log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    
    # Handler para archivo de errores
    error_handler = RotatingFileHandler(
        settings.logging.log_file.replace('.log', '_error.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setFormatter(file_formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)
    
    # Handler para logs JSON (opcional, para análisis)
    if settings.logging.enable_metrics:
        json_handler = TimedRotatingFileHandler(
            settings.logging.log_file.replace('.log', '_json.log'),
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        json_handler.setFormatter(JSONFormatter())
        json_handler.setLevel(logging.INFO)
        root_logger.addHandler(json_handler)
    
    # Configurar niveles para librerías externas
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('chromadb').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.INFO)
    logging.getLogger('streamlit').setLevel(logging.WARNING)
    
    return root_logger

# Inicializar logging al importar
setup_logging()

# Clase personalizada de Logger con funcionalidades extra
class AtheneaLogger:
    """Logger personalizado con funcionalidades adicionales"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = {}
        
    def set_context(self, **kwargs):
        """Establece contexto para todos los logs siguientes"""
        self.context.update(kwargs)
        
    def clear_context(self):
        """Limpia el contexto"""
        self.context = {}
        
    def _log_with_context(self, level: int, msg: str, *args, **kwargs):
        """Log con contexto adicional"""
        extra = kwargs.get('extra', {})
        extra.update(self.context)
        kwargs['extra'] = extra
        self.logger.log(level, msg, *args, **kwargs)
        
    def debug(self, msg: str, *args, **kwargs):
        self._log_with_context(logging.DEBUG, msg, *args, **kwargs)
        
    def info(self, msg: str, *args, **kwargs):
        self._log_with_context(logging.INFO, msg, *args, **kwargs)
        
    def warning(self, msg: str, *args, **kwargs):
        self._log_with_context(logging.WARNING, msg, *args, **kwargs)
        
    def error(self, msg: str, *args, **kwargs):
        self._log_with_context(logging.ERROR, msg, *args, **kwargs)
        
    def critical(self, msg: str, *args, **kwargs):
        self._log_with_context(logging.CRITICAL, msg, *args, **kwargs)
        
    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log de rendimiento con métricas"""
        extra = {
            'operation': operation,
            'duration_seconds': duration,
            'performance_metric': True,
            **kwargs
        }
        self.info(f"Performance: {operation} completed in {duration:.3f}s", extra=extra)
        
    def log_api_call(self, 
                    service: str, 
                    endpoint: str, 
                    status_code: Optional[int] = None,
                    duration: Optional[float] = None,
                    **kwargs):
        """Log de llamadas API"""
        extra = {
            'api_service': service,
            'api_endpoint': endpoint,
            'api_status_code': status_code,
            'api_duration': duration,
            'api_call': True,
            **kwargs
        }
        
        if status_code and status_code >= 400:
            self.error(f"API call failed: {service} {endpoint} - Status: {status_code}", extra=extra)
        else:
            self.info(f"API call: {service} {endpoint} - Status: {status_code}", extra=extra)
            
    def log_query(self, query: str, results_count: int, duration: float, **kwargs):
        """Log de consultas"""
        extra = {
            'query': query[:100],  # Limitar longitud
            'results_count': results_count,
            'query_duration': duration,
            'query_metric': True,
            **kwargs
        }
        self.info(f"Query processed: {results_count} results in {duration:.3f}s", extra=extra)
        
    def log_document_processing(self, 
                              doc_name: str,
                              doc_type: str,
                              chunks_created: int,
                              processing_time: float,
                              **kwargs):
        """Log de procesamiento de documentos"""
        extra = {
            'document_name': doc_name,
            'document_type': doc_type,
            'chunks_created': chunks_created,
            'processing_time': processing_time,
            'document_metric': True,
            **kwargs
        }
        self.info(
            f"Document processed: {doc_name} - {chunks_created} chunks in {processing_time:.3f}s", 
            extra=extra
        )
        
    def log_validation(self,
                      validation_type: str,
                      is_valid: bool,
                      confidence: float,
                      issues_count: int = 0,
                      **kwargs):
        """Log de validaciones"""
        extra = {
            'validation_type': validation_type,
            'is_valid': is_valid,
            'confidence': confidence,
            'issues_count': issues_count,
            'validation_metric': True,
            **kwargs
        }
        
        level = logging.INFO if is_valid else logging.WARNING
        self.log(
            level,
            f"Validation {validation_type}: {'PASSED' if is_valid else 'FAILED'} "
            f"(confidence: {confidence:.2f}, issues: {issues_count})",
            extra=extra
        )

# Función helper para obtener logger
def get_logger(name: str) -> AtheneaLogger:
    """Obtiene un logger personalizado para el módulo"""
    return AtheneaLogger(name)

# Utilidades de logging
class LogContext:
    """Context manager para logging con contexto temporal"""
    
    def __init__(self, logger: AtheneaLogger, **context):
        self.logger = logger
        self.context = context
        self.old_context = {}
        
    def __enter__(self):
        self.old_context = self.logger.context.copy()
        self.logger.set_context(**self.context)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.context = self.old_context
        
        if exc_type is not None:
            self.logger.error(
                f"Exception in context: {exc_type.__name__}: {str(exc_val)}",
                exc_info=True
            )
            
        return False

# Decorador para logging de funciones
def log_execution(logger: Optional[AtheneaLogger] = None):
    """Decorador para loggear ejecución de funciones"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
                
            start_time = datetime.now()
            func_name = func.__name__
            
            logger.debug(f"Starting execution of {func_name}")
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.log_performance(
                    f"Function {func_name}",
                    duration,
                    function_name=func_name,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.error(
                    f"Error in {func_name}: {str(e)}",
                    exc_info=True,
                    extra={
                        'function_name': func_name,
                        'duration': duration,
                        'success': False,
                        'error_type': type(e).__name__
                    }
                )
                raise
                
        return wrapper
    return decorator

# Función para analizar logs y generar métricas
def analyze_logs(log_file: str = None) -> Dict[str, Any]:
    """Analiza logs y genera métricas"""
    if log_file is None:
        log_file = settings.logging.log_file.replace('.log', '_json.log')
        
    metrics = {
        'total_logs': 0,
        'by_level': {},
        'performance_metrics': [],
        'api_metrics': [],
        'query_metrics': [],
        'errors': []
    }
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    metrics['total_logs'] += 1
                    
                    # Contar por nivel
                    level = log_entry.get('level', 'UNKNOWN')
                    metrics['by_level'][level] = metrics['by_level'].get(level, 0) + 1
                    
                    # Métricas de rendimiento
                    if log_entry.get('performance_metric'):
                        metrics['performance_metrics'].append({
                            'operation': log_entry.get('operation'),
                            'duration': log_entry.get('duration_seconds'),
                            'timestamp': log_entry.get('timestamp')
                        })
                        
                    # Métricas de API
                    if log_entry.get('api_call'):
                        metrics['api_metrics'].append({
                            'service': log_entry.get('api_service'),
                            'endpoint': log_entry.get('api_endpoint'),
                            'status': log_entry.get('api_status_code'),
                            'duration': log_entry.get('api_duration'),
                            'timestamp': log_entry.get('timestamp')
                        })
                        
                    # Métricas de queries
                    if log_entry.get('query_metric'):
                        metrics['query_metrics'].append({
                            'query': log_entry.get('query'),
                            'results': log_entry.get('results_count'),
                            'duration': log_entry.get('query_duration'),
                            'timestamp': log_entry.get('timestamp')
                        })
                        
                    # Errores
                    if level == 'ERROR':
                        metrics['errors'].append({
                            'message': log_entry.get('message'),
                            'module': log_entry.get('module'),
                            'function': log_entry.get('function'),
                            'timestamp': log_entry.get('timestamp')
                        })
                        
                except json.JSONDecodeError:
                    continue
                    
    except FileNotFoundError:
        logger = get_logger(__name__)
        logger.warning(f"Log file not found: {log_file}")
        
    return metrics

# Inicializar logger para este módulo
logger = get_logger(__name__)
logger.info("Sistema de logging inicializado")