"""
==============================================================================
CONTEXT VARIABLE SYSTEM v1.0
==============================================================================
Dynamic runtime variable resolution for Cortex-Prime manifests.

Enables intelligent agents through runtime state awareness via $(var) syntax.

Philosophy:
- Dynamic Intelligence: Agents reason about runtime state, not static scripts
- Scoped Context: Variables scoped to global, session, agent, and task levels
- Extensible: Easy to add new variable sources and resolvers
==============================================================================
"""

import re
import os
from typing import Dict, Any, Optional, Callable, Pattern
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger


class VariableResolutionError(Exception):
    """Raised when variable resolution fails"""
    pass


class ContextVariableResolver:
    """
    Resolves $(variable_name) syntax in manifest strings with runtime values.
    
    Supports:
    - Core system variables: $TIMESTAMP, $AGENT_ID, $SESSION_ID
    - Environment variables: $HOME, $USER, etc.
    - Agent state variables: $LAST_RESULT, $ITERATION_COUNT, $CONFIDENCE
    - Custom variable sources via resolvers
    """
    
    # Regex pattern for matching $(variable_name) or ${variable_name}
    VARIABLE_PATTERN: Pattern = re.compile(r'\$\{?([A-Z_][A-Z0-9_]*)\}?')
    
    def __init__(self):
        """Initialize the variable resolver with default resolvers"""
        self._resolvers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._context: Dict[str, Any] = {}
        
        # Register default variable resolvers
        self._register_default_resolvers()
    
    def _register_default_resolvers(self):
        """Register built-in variable resolvers"""
        
        # === CORE SYSTEM VARIABLES ===
        self._resolvers['TIMESTAMP'] = lambda ctx: datetime.now(timezone.utc).isoformat()
        self._resolvers['TIMESTAMP_UNIX'] = lambda ctx: int(datetime.now(timezone.utc).timestamp())
        self._resolvers['DATE'] = lambda ctx: datetime.now(timezone.utc).strftime('%Y-%m-%d')
        self._resolvers['TIME'] = lambda ctx: datetime.now(timezone.utc).strftime('%H:%M:%S')
        self._resolvers['DATETIME'] = lambda ctx: datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        # === AGENT IDENTITY VARIABLES ===
        self._resolvers['AGENT_ID'] = lambda ctx: ctx.get('agent_id', 'unknown')
        self._resolvers['AGENT_NAME'] = lambda ctx: ctx.get('agent_name', 'unknown')
        self._resolvers['AGENT_VERSION'] = lambda ctx: ctx.get('agent_version', '1.0')
        
        # === SESSION VARIABLES ===
        self._resolvers['SESSION_ID'] = lambda ctx: ctx.get('session_id', 'unknown')
        self._resolvers['USER_ID'] = lambda ctx: ctx.get('user_id', 'default')
        self._resolvers['USER_INTENT'] = lambda ctx: ctx.get('user_intent', '')
        
        # === EXECUTION STATE VARIABLES ===
        self._resolvers['ITERATION_COUNT'] = lambda ctx: str(ctx.get('iteration_count', 0))
        self._resolvers['LAST_RESULT'] = lambda ctx: str(ctx.get('last_result', ''))
        self._resolvers['CONFIDENCE'] = lambda ctx: str(ctx.get('confidence', 0.0))
        self._resolvers['ERROR_COUNT'] = lambda ctx: str(ctx.get('error_count', 0))
        
        # === ENVIRONMENT VARIABLES (fallback to OS env) ===
        self._resolvers['HOME'] = lambda ctx: ctx.get('HOME', os.getenv('HOME', '/home/cortex'))
        self._resolvers['USER'] = lambda ctx: ctx.get('USER', os.getenv('USER', 'cortex'))
        self._resolvers['PWD'] = lambda ctx: ctx.get('PWD', os.getenv('PWD', '/'))
        self._resolvers['HOSTNAME'] = lambda ctx: ctx.get('HOSTNAME', os.getenv('HOSTNAME', 'cortex-prime'))
        
        # === TASK VARIABLES ===
        self._resolvers['TASK_ID'] = lambda ctx: ctx.get('task_id', 'unknown')
        self._resolvers['TASK_STATUS'] = lambda ctx: ctx.get('task_status', 'pending')
        self._resolvers['TASK_PRIORITY'] = lambda ctx: ctx.get('task_priority', 'normal')
        
        logger.debug(f"Registered {len(self._resolvers)} default variable resolvers")
    
    def register_resolver(self, variable_name: str, resolver: Callable[[Dict[str, Any]], Any]):
        """
        Register a custom variable resolver.
        
        Args:
            variable_name: Name of the variable (without $ prefix)
            resolver: Function that takes context dict and returns resolved value
        """
        self._resolvers[variable_name.upper()] = resolver
        logger.debug(f"Registered custom resolver for: ${variable_name}")
    
    def set_context(self, context: Dict[str, Any]):
        """
        Set the current resolution context.
        
        Args:
            context: Dictionary of context values for variable resolution
        """
        self._context = context.copy()
    
    def update_context(self, updates: Dict[str, Any]):
        """
        Update specific context values without replacing the entire context.
        
        Args:
            updates: Dictionary of values to update
        """
        self._context.update(updates)
    
    def resolve(self, text: str, additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Resolve all $(variable) references in a string.
        
        Args:
            text: String containing variable references
            additional_context: Optional additional context for this resolution
            
        Returns:
            String with all variables resolved
            
        Raises:
            VariableResolutionError: If a required variable cannot be resolved
        """
        if not isinstance(text, str):
            return text
        
        # Merge context
        context = self._context.copy()
        if additional_context:
            context.update(additional_context)
        
        # Track unresolved variables
        unresolved = []
        
        def replace_variable(match: re.Match) -> str:
            """Replace a single variable match"""
            var_name = match.group(1)
            
            # Try resolver first
            if var_name in self._resolvers:
                try:
                    value = self._resolvers[var_name](context)
                    return str(value) if value is not None else ''
                except Exception as e:
                    logger.error(f"Error resolving ${var_name}: {e}")
                    unresolved.append(var_name)
                    return match.group(0)  # Keep original
            
            # Try context direct lookup
            if var_name in context:
                value = context[var_name]
                return str(value) if value is not None else ''
            
            # Try environment variable
            env_value = os.getenv(var_name)
            if env_value is not None:
                return env_value
            
            # Variable not found
            unresolved.append(var_name)
            logger.warning(f"Unresolved variable: ${var_name}")
            return match.group(0)  # Keep original
        
        # Perform replacement
        resolved = self.VARIABLE_PATTERN.sub(replace_variable, text)
        
        # Log unresolved variables
        if unresolved:
            logger.warning(f"Unresolved variables in text: {unresolved}")
        
        return resolved
    
    def resolve_dict(
        self, 
        data: Dict[str, Any], 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Recursively resolve all variables in a dictionary structure.
        
        Args:
            data: Dictionary that may contain variable references
            additional_context: Optional additional context
            
        Returns:
            Dictionary with all variables resolved
        """
        result = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Resolve string values
                result[key] = self.resolve(value, additional_context)
            elif isinstance(value, dict):
                # Recursively resolve nested dicts
                result[key] = self.resolve_dict(value, additional_context)
            elif isinstance(value, list):
                # Resolve lists
                result[key] = self.resolve_list(value, additional_context)
            else:
                # Keep other types as-is
                result[key] = value
        
        return result
    
    def resolve_list(
        self, 
        data: list, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> list:
        """
        Recursively resolve all variables in a list.
        
        Args:
            data: List that may contain variable references
            additional_context: Optional additional context
            
        Returns:
            List with all variables resolved
        """
        result = []
        
        for item in data:
            if isinstance(item, str):
                result.append(self.resolve(item, additional_context))
            elif isinstance(item, dict):
                result.append(self.resolve_dict(item, additional_context))
            elif isinstance(item, list):
                result.append(self.resolve_list(item, additional_context))
            else:
                result.append(item)
        
        return result
    
    def get_available_variables(self) -> Dict[str, str]:
        """
        Get a list of all available variables and their descriptions.
        
        Returns:
            Dictionary mapping variable names to descriptions
        """
        return {
            # Core system
            'TIMESTAMP': 'Current UTC timestamp (ISO 8601)',
            'TIMESTAMP_UNIX': 'Current Unix timestamp',
            'DATE': 'Current date (YYYY-MM-DD)',
            'TIME': 'Current time (HH:MM:SS)',
            'DATETIME': 'Current date and time',
            
            # Agent identity
            'AGENT_ID': 'Unique agent identifier',
            'AGENT_NAME': 'Agent name',
            'AGENT_VERSION': 'Agent version',
            
            # Session
            'SESSION_ID': 'Current session identifier',
            'USER_ID': 'User identifier',
            'USER_INTENT': 'User\'s stated intent/goal',
            
            # Execution state
            'ITERATION_COUNT': 'Current iteration number',
            'LAST_RESULT': 'Result of last operation',
            'CONFIDENCE': 'Confidence score (0.0-1.0)',
            'ERROR_COUNT': 'Number of errors in session',
            
            # Environment
            'HOME': 'Home directory path',
            'USER': 'System user name',
            'PWD': 'Present working directory',
            'HOSTNAME': 'System hostname',
            
            # Task
            'TASK_ID': 'Current task identifier',
            'TASK_STATUS': 'Current task status',
            'TASK_PRIORITY': 'Task priority level',
        }


# Global singleton instance for easy access
_global_resolver: Optional[ContextVariableResolver] = None


def get_resolver() -> ContextVariableResolver:
    """Get or create the global variable resolver instance"""
    global _global_resolver
    if _global_resolver is None:
        _global_resolver = ContextVariableResolver()
    return _global_resolver


def resolve(text: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Convenience function to resolve variables using the global resolver.
    
    Args:
        text: String containing variable references
        context: Optional context for resolution
        
    Returns:
        String with variables resolved
    """
    resolver = get_resolver()
    if context:
        resolver.set_context(context)
    return resolver.resolve(text)
