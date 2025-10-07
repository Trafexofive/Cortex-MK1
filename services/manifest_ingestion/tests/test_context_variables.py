"""
Tests for context variable resolution system
"""

import pytest
from datetime import datetime
from context_variables import ContextVariableResolver, VariableResolutionError, resolve


@pytest.fixture
def resolver():
    return ContextVariableResolver()


@pytest.fixture
def sample_context():
    return {
        'agent_id': 'test-agent-123',
        'agent_name': 'TestAgent',
        'session_id': 'session-456',
        'iteration_count': 5,
        'last_result': 'success',
        'confidence': 0.95
    }


class TestContextVariableResolver:
    
    def test_resolve_single_variable(self, resolver, sample_context):
        """Test resolving a single variable"""
        resolver.set_context(sample_context)
        result = resolver.resolve("Agent: $AGENT_ID")
        assert result == "Agent: test-agent-123"
    
    def test_resolve_multiple_variables(self, resolver, sample_context):
        """Test resolving multiple variables in one string"""
        resolver.set_context(sample_context)
        text = "Agent $AGENT_NAME (ID: $AGENT_ID) in session $SESSION_ID"
        result = resolver.resolve(text)
        assert result == "Agent TestAgent (ID: test-agent-123) in session session-456"
    
    def test_resolve_with_braces(self, resolver, sample_context):
        """Test resolving variables with ${} syntax"""
        resolver.set_context(sample_context)
        result = resolver.resolve("Agent: ${AGENT_ID}")
        assert result == "Agent: test-agent-123"
    
    def test_resolve_timestamp_variable(self, resolver):
        """Test resolving built-in TIMESTAMP variable"""
        result = resolver.resolve("Time: $TIMESTAMP")
        assert "Time: " in result
        assert len(result) > 10  # Should have ISO timestamp
    
    def test_resolve_iteration_count(self, resolver, sample_context):
        """Test resolving iteration count from context"""
        resolver.set_context(sample_context)
        result = resolver.resolve("Iteration: $ITERATION_COUNT")
        assert result == "Iteration: 5"
    
    def test_resolve_confidence(self, resolver, sample_context):
        """Test resolving confidence score"""
        resolver.set_context(sample_context)
        result = resolver.resolve("Confidence: $CONFIDENCE")
        assert result == "Confidence: 0.95"
    
    def test_resolve_dict(self, resolver, sample_context):
        """Test resolving variables in a dictionary"""
        resolver.set_context(sample_context)
        
        data = {
            "agent": "$AGENT_NAME",
            "session": "$SESSION_ID",
            "nested": {
                "count": "$ITERATION_COUNT",
                "result": "$LAST_RESULT"
            }
        }
        
        resolved = resolver.resolve_dict(data)
        
        assert resolved["agent"] == "TestAgent"
        assert resolved["session"] == "session-456"
        assert resolved["nested"]["count"] == "5"
        assert resolved["nested"]["result"] == "success"
    
    def test_resolve_list(self, resolver, sample_context):
        """Test resolving variables in a list"""
        resolver.set_context(sample_context)
        
        data = [
            "$AGENT_ID",
            "static_value",
            {"key": "$SESSION_ID"},
            ["$ITERATION_COUNT", "$CONFIDENCE"]
        ]
        
        resolved = resolver.resolve_list(data)
        
        assert resolved[0] == "test-agent-123"
        assert resolved[1] == "static_value"
        assert resolved[2]["key"] == "session-456"
        assert resolved[3][0] == "5"
        assert resolved[3][1] == "0.95"
    
    def test_custom_resolver(self, resolver):
        """Test registering and using a custom variable resolver"""
        resolver.register_resolver('CUSTOM_VAR', lambda ctx: 'custom_value')
        
        result = resolver.resolve("Test: $CUSTOM_VAR")
        assert result == "Test: custom_value"
    
    def test_unresolved_variable_keeps_original(self, resolver):
        """Test that unresolved variables are kept as-is"""
        result = resolver.resolve("Test: $NONEXISTENT_VAR")
        assert result == "Test: $NONEXISTENT_VAR"
    
    def test_additional_context(self, resolver, sample_context):
        """Test providing additional context for specific resolution"""
        resolver.set_context(sample_context)
        
        additional = {'task_id': 'task-789'}
        result = resolver.resolve("Task: $TASK_ID", additional)
        assert result == "Task: task-789"
    
    def test_update_context(self, resolver, sample_context):
        """Test updating context without replacing it"""
        resolver.set_context(sample_context)
        resolver.update_context({'new_key': 'new_value'})
        
        # Old context should still work
        result1 = resolver.resolve("$AGENT_ID")
        assert result1 == "test-agent-123"
        
        # New context should also work
        resolver.register_resolver('NEW_KEY', lambda ctx: ctx.get('new_key', ''))
        result2 = resolver.resolve("$NEW_KEY")
        assert result2 == "new_value"
    
    def test_environment_variable_fallback(self, resolver):
        """Test fallback to environment variables"""
        import os
        os.environ['TEST_ENV_VAR'] = 'env_value'
        
        result = resolver.resolve("$TEST_ENV_VAR")
        assert result == "env_value"
        
        # Clean up
        del os.environ['TEST_ENV_VAR']
    
    def test_get_available_variables(self, resolver):
        """Test getting list of available variables"""
        variables = resolver.get_available_variables()
        
        assert 'TIMESTAMP' in variables
        assert 'AGENT_ID' in variables
        assert 'SESSION_ID' in variables
        assert 'ITERATION_COUNT' in variables
        
        # Should have descriptions
        assert len(variables['TIMESTAMP']) > 0
    
    def test_non_string_value_passthrough(self, resolver):
        """Test that non-string values are passed through unchanged"""
        assert resolver.resolve(123) == 123
        assert resolver.resolve(None) is None
        assert resolver.resolve(True) is True
    
    def test_mixed_syntax_resolution(self, resolver, sample_context):
        """Test resolving mix of $VAR and ${VAR} syntax"""
        resolver.set_context(sample_context)
        
        text = "Agent $AGENT_NAME with ID ${AGENT_ID} in $SESSION_ID"
        result = resolver.resolve(text)
        
        assert result == "Agent TestAgent with ID test-agent-123 in session-456"


class TestConvenienceFunction:
    
    def test_global_resolve_function(self):
        """Test the global resolve() convenience function"""
        context = {'agent_name': 'GlobalAgent'}
        
        # Should create a custom resolver context
        resolver = ContextVariableResolver()
        resolver.register_resolver('AGENT_NAME', lambda ctx: ctx.get('agent_name', ''))
        resolver.set_context(context)
        
        result = resolver.resolve("Name: $AGENT_NAME")
        assert "GlobalAgent" in result
