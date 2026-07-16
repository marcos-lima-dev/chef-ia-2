from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseSpecialist(ABC):
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executa a análise e retorna um dicionário com: analysis, warnings, suggestions, events."""
        pass