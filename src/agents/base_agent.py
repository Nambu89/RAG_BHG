from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import asyncio
from datetime import datetime
import uuid

from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger(__name__)

@dataclass
class AgentMessage:
    """Mensaje entre agentes"""
    id: str
    sender: str
    recipient: str
    message_type: str
    content: Any
    metadata: Dict[str, Any]
    timestamp: datetime
    
    @classmethod
    def create(cls, sender: str, recipient: str, message_type: str, content: Any, metadata: Dict = None):
        return cls(
            id=str(uuid.uuid4()),
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.now()
        )

@dataclass
class AgentState:
    """Estado del agente"""
    status: str  # 'idle', 'processing', 'waiting', 'error'
    current_task: Optional[str] = None
    last_action: Optional[str] = None
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {
                'tasks_completed': 0,
                'tasks_failed': 0,
                'avg_response_time': 0,
                'total_tokens_used': 0
            }

class BaseAgent(ABC):
    """Clase base para todos los agentes del sistema"""
    
    def __init__(self, name: str, description: str, capabilities: List[str]):
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.state = AgentState(status='idle')
        
        # Sistema de mensajería
        self.inbox: List[AgentMessage] = []
        self.outbox: List[AgentMessage] = []
        
        # Historial
        self.action_history: List[Dict[str, Any]] = []
        self.conversation_context: List[Dict[str, Any]] = []
        
        # Configuración
        self.max_retries = 3
        self.timeout = 30  # segundos
        
        logger.info(f"Agente {self.name} inicializado")
        
    @abstractmethod
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Procesa un mensaje entrante"""
        pass
        
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una tarea específica"""
        pass
        
    async def run(self):
        """Loop principal del agente"""
        logger.info(f"Agente {self.name} iniciado")
        
        while True:
            try:
                # Procesar mensajes entrantes
                if self.inbox:
                    message = self.inbox.pop(0)
                    self.state.status = 'processing'
                    self.state.current_task = f"Procesando mensaje de {message.sender}"
                    
                    response = await self.process_message(message)
                    
                    if response:
                        self.outbox.append(response)
                        
                    self.state.status = 'idle'
                    self.state.current_task = None
                    
                # Pequeña pausa para no consumir CPU
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error en agente {self.name}: {str(e)}")
                self.state.status = 'error'
                self.state.error_message = str(e)
                await asyncio.sleep(1)  # Pausa más larga en caso de error
                
    def send_message(self, recipient: str, message_type: str, content: Any, metadata: Dict = None):
        """Envía un mensaje a otro agente"""
        message = AgentMessage.create(
            sender=self.name,
            recipient=recipient,
            message_type=message_type,
            content=content,
            metadata=metadata
        )
        
        self.outbox.append(message)
        self._log_action('send_message', {
            'recipient': recipient,
            'message_type': message_type
        })
        
    def receive_message(self, message: AgentMessage):
        """Recibe un mensaje de otro agente"""
        self.inbox.append(message)
        self._log_action('receive_message', {
            'sender': message.sender,
            'message_type': message.message_type
        })
        
    def _log_action(self, action: str, details: Dict[str, Any] = None):
        """Registra una acción en el historial"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details or {},
            'state': self.state.status
        }
        
        self.action_history.append(entry)
        
        # Mantener historial limitado
        if len(self.action_history) > 1000:
            self.action_history = self.action_history[-500:]
            
    def update_metrics(self, metric: str, value: Any):
        """Actualiza métricas del agente"""
        if metric in self.state.metrics:
            if isinstance(value, (int, float)):
                if metric.startswith('avg_'):
                    # Promedio móvil
                    old_avg = self.state.metrics[metric]
                    count = self.state.metrics.get('tasks_completed', 1)
                    self.state.metrics[metric] = (old_avg * count + value) / (count + 1)
                else:
                    self.state.metrics[metric] += value
            else:
                self.state.metrics[metric] = value
                
    def add_to_context(self, entry: Dict[str, Any]):
        """Agrega información al contexto conversacional"""
        self.conversation_context.append({
            'timestamp': datetime.now().isoformat(),
            **entry
        })
        
        # Limitar contexto
        if len(self.conversation_context) > 20:
            self.conversation_context = self.conversation_context[-10:]
            
    def get_capabilities_prompt(self) -> str:
        """Genera un prompt describiendo las capacidades del agente"""
        return f"""
Agente: {self.name}
Descripción: {self.description}
Capacidades:
{chr(10).join(f'- {cap}' for cap in self.capabilities)}
"""

    def get_status_report(self) -> Dict[str, Any]:
        """Genera un reporte del estado actual del agente"""
        return {
            'name': self.name,
            'status': self.state.status,
            'current_task': self.state.current_task,
            'metrics': self.state.metrics,
            'inbox_size': len(self.inbox),
            'outbox_size': len(self.outbox),
            'last_actions': self.action_history[-5:] if self.action_history else []
        }
        
    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """Valida la entrada antes de procesarla"""
        pass
        
    @abstractmethod
    def format_output(self, output_data: Any) -> Any:
        """Formatea la salida del agente"""
        pass