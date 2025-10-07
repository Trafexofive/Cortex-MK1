"""
Tests for the manifest parser
"""

import pytest
import yaml
from pathlib import Path

from parsers.manifest_parser import ManifestParser, ManifestParsingError


@pytest.fixture
def parser():
    return ManifestParser()


@pytest.fixture
def sample_agent_yaml():
    return """
kind: Agent
version: "1.0"
name: "test_agent"
summary: "A test agent for validation"
author: "PRAETORIAN_CHIMERA"
state: "unstable"

persona:
  agent: "./prompts/test_agent.md"

agency_level: "strict"
grade: "common"
iteration_cap: 5

cognitive_engine:
  primary:
    provider: "google"
    model: "gemini-1.5-flash"
  parameters:
    temperature: 0.7
    max_tokens: 4096

import:
  tools:
    - "filesystem"
    - "./tools/test_tool/tool.yml"

environment:
  variables:
    TEST_VAR: "test_value"
"""


@pytest.fixture
def sample_markdown_with_frontmatter():
    return """---
kind: Agent
version: "1.0"
name: "markdown_agent"
summary: "Agent defined in markdown with frontmatter"
author: "PRAETORIAN_CHIMERA"
---

# Test Agent

This is the markdown content describing the agent.

## Purpose

This agent is for testing markdown parsing.
"""


class TestManifestParser:
    
    @pytest.mark.asyncio
    async def test_parse_yaml_content(self, parser, sample_agent_yaml):
        """Test parsing pure YAML content"""
        result = await parser.parse_manifest_content(sample_agent_yaml)
        
        assert result["kind"] == "Agent"
        assert result["name"] == "test_agent"
        assert result["version"] == "1.0"
        assert "cognitive_engine" in result
        
    @pytest.mark.asyncio
    async def test_parse_markdown_with_frontmatter(self, parser, sample_markdown_with_frontmatter):
        """Test parsing markdown with YAML frontmatter"""
        result = await parser.parse_manifest_content(sample_markdown_with_frontmatter)
        
        assert result["kind"] == "Agent"
        assert result["name"] == "markdown_agent"
        assert "_markdown_content" in result
        assert "This agent is for testing" in result["_markdown_content"]
        
    @pytest.mark.asyncio
    async def test_validate_manifest_structure_valid(self, parser, sample_agent_yaml):
        """Test validation of valid manifest structure"""
        data = await parser.parse_manifest_content(sample_agent_yaml)
        is_valid, errors = await parser.validate_manifest_structure(data)
        
        assert is_valid
        assert len(errors) == 0
        
    @pytest.mark.asyncio
    async def test_validate_manifest_structure_invalid(self, parser):
        """Test validation of invalid manifest structure"""
        invalid_data = {
            "kind": "InvalidKind",
            "version": "invalid_version",
            "name": "123invalid_name"
        }
        
        is_valid, errors = await parser.validate_manifest_structure(invalid_data)
        
        assert not is_valid
        assert len(errors) > 0
        assert any("Missing required field: summary" in error for error in errors)
        assert any("Invalid kind" in error for error in errors)
        
    @pytest.mark.asyncio
    async def test_extract_dependencies(self, parser, sample_agent_yaml):
        """Test extraction of dependencies from manifest"""
        data = await parser.parse_manifest_content(sample_agent_yaml)
        dependencies = await parser.extract_dependencies(data)
        
        assert "filesystem" in dependencies
        assert "./tools/test_tool/tool.yml" in dependencies
        
    @pytest.mark.asyncio
    async def test_create_typed_manifest(self, parser, sample_agent_yaml):
        """Test creation of typed Pydantic manifest"""
        data = await parser.parse_manifest_content(sample_agent_yaml)
        
        # Fill in required fields for AgentManifest
        data["cognitive_engine"]["fallback"] = {
            "provider": "ollama",
            "model": "llama3.1:8b"
        }
        
        typed_manifest = await parser.create_typed_manifest(data)
        
        assert typed_manifest.kind == "Agent"
        assert typed_manifest.name == "test_agent"
        assert typed_manifest.agency_level == "strict"
        assert typed_manifest.cognitive_engine.primary.provider == "google"
        
    @pytest.mark.asyncio
    async def test_invalid_yaml_raises_error(self, parser):
        """Test that invalid YAML raises appropriate error"""
        invalid_yaml = """
        kind: Agent
        invalid_yaml: [
        """
        
        with pytest.raises(ManifestParsingError):
            await parser.parse_manifest_content(invalid_yaml)
            
    @pytest.mark.asyncio
    async def test_missing_frontmatter_raises_error(self, parser):
        """Test that markdown without frontmatter raises error"""
        invalid_markdown = """
        # Just a markdown file
        
        With no frontmatter.
        """
        
        with pytest.raises(ManifestParsingError):
            await parser.parse_manifest_content(invalid_markdown)
    
    @pytest.mark.asyncio
    async def test_variable_resolution_in_manifest(self, parser):
        """Test that context variables are resolved in manifests"""
        manifest_yaml = """
kind: Agent
version: "1.0"
name: "test_agent"
summary: "Agent created at $TIMESTAMP"
author: "PRAETORIAN_CHIMERA"
state: "unstable"

persona:
  agent: "./prompts/test_agent.md"

agency_level: "strict"
grade: "common"
iteration_cap: 5

cognitive_engine:
  primary:
    provider: "google"
    model: "gemini-1.5-flash"

environment:
  variables:
    AGENT_HOME: "$HOME/agents/$AGENT_NAME"
    SESSION: "$SESSION_ID"
"""
        
        context = {
            'HOME': '/home/cortex',
            'SESSION_ID': 'test-session-123'
        }
        
        result = await parser.parse_manifest_content(manifest_yaml, variable_context=context)
        
        # Check that variables were resolved
        assert '$TIMESTAMP' not in result['summary']
        assert len(result['summary']) > len("Agent created at ")
        assert result['environment']['variables']['AGENT_HOME'] == '/home/cortex/agents/test_agent'
        assert result['environment']['variables']['SESSION'] == 'test-session-123'
    
    @pytest.mark.asyncio
    async def test_disable_variable_resolution(self, parser):
        """Test disabling variable resolution"""
        parser.enable_variable_resolution(False)
        
        manifest_yaml = """
kind: Agent
name: "test"
summary: "Test $TIMESTAMP"
"""
        
        result = await parser.parse_manifest_content(manifest_yaml)
        
        # Variables should NOT be resolved
        assert '$TIMESTAMP' in result['summary']
        
        # Re-enable for other tests
        parser.enable_variable_resolution(True)