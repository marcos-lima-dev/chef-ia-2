class ChefeIAException(Exception):
    """Exceção base da aplicação."""
    pass

class InvalidTransitionError(ChefeIAException):
    """Lançada quando uma transição de estado é inválida."""
    pass

class OrderNotFoundError(ChefeIAException):
    """Lançada quando um pedido não é encontrado."""
    pass

class InvalidStateError(ChefeIAException):
    """Lançada quando uma ação não é permitida no estado atual."""
    pass

class AgentExecutionError(ChefeIAException):
    """Lançada quando um agente falha na execução."""
    pass

