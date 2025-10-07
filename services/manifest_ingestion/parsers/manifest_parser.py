"""
==============================================================================
MANIFEST PARSER v1.0
==============================================================================
Intelligent parser for Cortex-Prime manifest formats.
Supports YAML manifests with embedded markdown sections.
Includes automatic context variable resolution for dynamic manifests.
==============================================================================
"""

import re
import yaml
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from loguru import logger

from models.manifest_models import ManifestKind, create_manifest_from_dict
from context_variables import ContextVariableResolver


class ManifestParsingError(Exception):
    """Raised when manifest parsing fails"""
    pass


class ManifestParser:
    """
    Intelligent parser for Cortex-Prime manifest files.
    
    Handles:
    - Pure YAML manifests  
    - Markdown files with YAML frontmatter
    - Mixed format files with embedded markdown sections
    """
    
    def __init__(self):
        self.supported_extensions = {'.yml', '.yaml', '.md', '.markdown'}
        self.variable_resolver = ContextVariableResolver()
        self._enable_variable_resolution = True
        
    async def parse_manifest_content(
        self, 
        content: str, 
        filename: Optional[str] = None,
        variable_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse manifest content from string.
        
        Args:
            content: Raw file content
            filename: Optional filename for error reporting
            variable_context: Optional context for variable resolution
            
        Returns:
            Parsed manifest dictionary with variables resolved
            
        Raises:
            ManifestParsingError: If parsing fails
        """
        try:
            # Check for markdown with frontmatter FIRST (before YAML check)
            # because frontmatter also starts with YAML-like syntax
            if self._looks_like_markdown_with_frontmatter(content):
                manifest_data = await self._parse_markdown_with_frontmatter(content)
            elif self._looks_like_yaml(content):
                manifest_data = await self._parse_yaml_content(content)
            else:
                # Try YAML parsing as fallback
                manifest_data = await self._parse_yaml_content(content)
            
            # Resolve context variables if enabled
            if self._enable_variable_resolution:
                manifest_data = self._resolve_variables(manifest_data, variable_context)
            
            return manifest_data
                
        except Exception as e:
            error_msg = f"Failed to parse manifest"
            if filename:
                error_msg += f" '{filename}'"
            error_msg += f": {str(e)}"
            logger.error(error_msg)
            raise ManifestParsingError(error_msg)
    
    async def parse_manifest_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse manifest from file path.
        
        Args:
            file_path: Path to manifest file (string or Path object)
            
        Returns:
            Parsed manifest dictionary
        """
        file_path = Path(file_path)  # Convert string to Path object
        if not file_path.exists():
            raise ManifestParsingError(f"Manifest file not found: {file_path}")
            
        if file_path.suffix.lower() not in self.supported_extensions:
            raise ManifestParsingError(
                f"Unsupported file extension: {file_path.suffix}. "
                f"Supported: {', '.join(self.supported_extensions)}"
            )
        
        try:
            content = file_path.read_text(encoding='utf-8')
            return await self.parse_manifest_content(content, str(file_path))
        except Exception as e:
            raise ManifestParsingError(f"Failed to read file {file_path}: {str(e)}")
    
    def _looks_like_yaml(self, content: str) -> bool:
        """Check if content looks like YAML"""
        content = content.strip()
        
        # Check for YAML-like patterns
        yaml_patterns = [
            r'^kind:\s*\w+',
            r'^version:\s*["\']?\d+\.\d+["\']?',
            r'^name:\s*["\']?\w+["\']?',
        ]
        
        for pattern in yaml_patterns:
            if re.search(pattern, content, re.MULTILINE):
                return True
        
        # If it starts with common YAML structures
        if content.startswith(('kind:', 'version:', 'name:', 'apiVersion:')):
            return True
            
        return False
    
    def _looks_like_markdown_with_frontmatter(self, content: str) -> bool:
        """Check if content is markdown with YAML frontmatter"""
        # Must start with --- and have a closing --- followed by markdown content
        pattern = r'^---\s*\n.*?\n---\s*\n'
        return bool(re.match(pattern, content, re.DOTALL))
    
    async def _parse_yaml_content(self, content: str) -> Dict[str, Any]:
        """Parse pure YAML content"""
        try:
            # Handle multiple YAML documents (separated by ---)
            documents = list(yaml.safe_load_all(content))
            
            # Filter out None documents
            documents = [doc for doc in documents if doc is not None]
            
            if len(documents) == 0:
                raise ManifestParsingError("No valid YAML documents found in content")
            elif len(documents) == 1:
                if not isinstance(documents[0], dict):
                    raise ManifestParsingError("Manifest must be a YAML dictionary")
                return documents[0]
            elif len(documents) > 1:
                # If multiple documents, look for the main manifest
                for doc in documents:
                    if isinstance(doc, dict) and 'kind' in doc:
                        return doc
                # If no manifest found, return the first document
                if not isinstance(documents[0], dict):
                    raise ManifestParsingError("Manifest must be a YAML dictionary")
                return documents[0]
                
        except yaml.YAMLError as e:
            raise ManifestParsingError(f"YAML parsing error: {str(e)}")
    
    async def _parse_markdown_with_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse markdown file with YAML frontmatter"""
        try:
            # Extract frontmatter
            frontmatter_match = re.match(
                r'^---\s*\n(.*?)\n---\s*\n(.*)$', 
                content, 
                re.DOTALL
            )
            
            if not frontmatter_match:
                raise ManifestParsingError("No valid YAML frontmatter found")
            
            frontmatter_content = frontmatter_match.group(1)
            markdown_content = frontmatter_match.group(2)
            
            # Parse the YAML frontmatter
            manifest_data = yaml.safe_load(frontmatter_content)
            
            if not isinstance(manifest_data, dict):
                raise ManifestParsingError("Frontmatter must be a YAML dictionary")
            
            # Store markdown content for reference
            manifest_data['_markdown_content'] = markdown_content.strip()
            
            return manifest_data
            
        except yaml.YAMLError as e:
            raise ManifestParsingError(f"YAML frontmatter parsing error: {str(e)}")
    
    def _resolve_variables(
        self, 
        manifest_data: Dict[str, Any],
        variable_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resolve context variables in manifest data.
        
        Args:
            manifest_data: Parsed manifest dictionary
            variable_context: Optional additional context for resolution
            
        Returns:
            Manifest data with all variables resolved
        """
        try:
            # Build resolution context from manifest metadata
            context = {
                'manifest_kind': manifest_data.get('kind', 'unknown'),
                'manifest_name': manifest_data.get('name', 'unknown'),
                'manifest_version': manifest_data.get('version', '1.0'),
                # Populate agent context from manifest
                'agent_name': manifest_data.get('name', 'unknown'),
                'agent_id': manifest_data.get('name', 'unknown'),
            }
            
            # Add any additional context (this takes precedence)
            if variable_context:
                context.update(variable_context)
                # Also map common uppercase keys to lowercase for resolver compatibility
                if 'SESSION_ID' in variable_context:
                    context['session_id'] = variable_context['SESSION_ID']
                if 'AGENT_ID' in variable_context:
                    context['agent_id'] = variable_context['AGENT_ID']
                if 'AGENT_NAME' in variable_context:
                    context['agent_name'] = variable_context['AGENT_NAME']
            
            # Set context and resolve
            self.variable_resolver.set_context(context)
            resolved_data = self.variable_resolver.resolve_dict(manifest_data)
            
            logger.debug(f"Resolved variables in manifest: {manifest_data.get('kind')}/{manifest_data.get('name')}")
            return resolved_data
            
        except Exception as e:
            logger.warning(f"Variable resolution failed, using unresolved manifest: {e}")
            return manifest_data
    
    def set_variable_context(self, context: Dict[str, Any]):
        """Set the default variable resolution context"""
        self.variable_resolver.set_context(context)
    
    def enable_variable_resolution(self, enabled: bool = True):
        """Enable or disable automatic variable resolution"""
        self._enable_variable_resolution = enabled
    
    async def validate_manifest_structure(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate basic manifest structure.
        
        Args:
            data: Parsed manifest dictionary
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        required_fields = ['kind', 'name', 'version', 'summary']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate kind
        if 'kind' in data:
            try:
                ManifestKind(data['kind'])
            except ValueError:
                valid_kinds = [k.value for k in ManifestKind]
                errors.append(
                    f"Invalid kind '{data['kind']}'. Valid kinds: {', '.join(valid_kinds)}"
                )
        
        # Validate version format
        if 'version' in data:
            version = str(data['version'])
            if not re.match(r'^\d+\.\d+(\.\d+)?$', version):
                errors.append(f"Invalid version format: '{version}'. Use semantic versioning (e.g., '1.0' or '1.0.0')")
        
        # Validate name format
        if 'name' in data:
            name = data['name']
            if not isinstance(name, str) or not name.strip():
                errors.append("Name must be a non-empty string")
            elif not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', name):
                errors.append("Name must start with a letter and contain only letters, numbers, hyphens, and underscores")
        
        return len(errors) == 0, errors
    
    async def create_typed_manifest(self, data: Dict[str, Any]):
        """
        Create a strongly-typed Pydantic manifest object.
        
        Args:
            data: Parsed manifest dictionary
            
        Returns:
            Typed manifest object
        """
        try:
            return create_manifest_from_dict(data)
        except Exception as e:
            raise ManifestParsingError(f"Failed to create typed manifest: {str(e)}")
    
    async def extract_dependencies(self, data: Dict[str, Any]) -> List[str]:
        """
        Extract all dependencies from a manifest.
        
        Args:
            data: Parsed manifest dictionary
            
        Returns:
            List of dependency identifiers
        """
        dependencies = []
        
        # Look in common dependency fields
        if 'import' in data:
            import_section = data['import']
            for category in ['agents', 'tools', 'relics', 'workflows', 'monuments', 'amulets']:
                if category in import_section:
                    dependencies.extend(import_section[category])
        
        if 'dependencies' in data:
            dependencies.extend(data['dependencies'])
        
        return list(set(dependencies))  # Remove duplicates
    
    async def resolve_relative_paths(
        self, 
        data: Dict[str, Any], 
        base_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Resolve relative paths in manifest to absolute paths.
        
        Args:
            data: Manifest dictionary
            base_path: Base directory for relative path resolution
            
        Returns:
            Manifest with resolved paths
        """
        if base_path is None:
            return data
        
        # Create a deep copy to avoid modifying original
        import copy
        resolved_data = copy.deepcopy(data)
        
        # Resolve paths in persona section (for agents)
        if 'persona' in resolved_data:
            persona = resolved_data['persona']
            for key in ['agent', 'user', 'system', 'knowledge']:
                if key in persona and isinstance(persona[key], str):
                    if persona[key].startswith('./'):
                        persona[key] = str(base_path / persona[key][2:])
        
        # Resolve paths in import section
        if 'import' in resolved_data:
            import_section = resolved_data['import']
            for category in ['agents', 'tools', 'relics', 'workflows']:
                if category in import_section:
                    resolved_items = []
                    for item in import_section[category]:
                        if isinstance(item, str) and item.startswith('./'):
                            resolved_items.append(str(base_path / item[2:]))
                        else:
                            resolved_items.append(item)
                    import_section[category] = resolved_items
        
        return resolved_data