#!/usr/bin/env python3
"""
Standalone Manifest Testing Script
Tests manifests in test_against_manifest/ directory without needing Docker services
"""

import sys
import os
from pathlib import Path
import yaml
from typing import Dict, Any, List
import json

# Add services to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "manifest_ingestion"))

from models.manifest_models import AgentManifest, ToolManifest, RelicManifest, WorkflowManifest

class ManifestTester:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.results = {
            "passed": [],
            "failed": [],
            "total": 0
        }
    
    def find_manifests(self) -> List[Path]:
        """Find all YAML manifests in the test directory"""
        manifests = []
        for pattern in ["**/*.yml", "**/*.yaml"]:
            manifests.extend(self.base_path.glob(pattern))
        # Filter out docker-compose files
        return [m for m in manifests if "docker-compose" not in m.name]
    
    def validate_manifest(self, manifest_path: Path) -> Dict[str, Any]:
        """Validate a single manifest file"""
        try:
            with open(manifest_path, 'r') as f:
                raw_data = yaml.safe_load(f)
            
            if not raw_data or not isinstance(raw_data, dict):
                return {
                    "path": str(manifest_path.relative_to(self.base_path)),
                    "status": "failed",
                    "error": "Invalid YAML format"
                }
            
            kind = raw_data.get('kind')
            name = raw_data.get('name', 'unknown')
            
            # Validate based on kind
            if kind == "Agent":
                model = AgentManifest(**raw_data)
            elif kind == "Tool":
                model = ToolManifest(**raw_data)
            elif kind == "Relic":
                model = RelicManifest(**raw_data)
            elif kind == "Workflow":
                model = WorkflowManifest(**raw_data)
            else:
                return {
                    "path": str(manifest_path.relative_to(self.base_path)),
                    "status": "skipped",
                    "error": f"Unknown kind: {kind}"
                }
            
            # Check imports exist if specified
            warnings = []
            if hasattr(model, 'import_'):
                warnings = self.check_imports(manifest_path, model.import_)
            
            return {
                "path": str(manifest_path.relative_to(self.base_path)),
                "kind": kind,
                "name": name,
                "status": "passed",
                "warnings": warnings
            }
            
        except Exception as e:
            return {
                "path": str(manifest_path.relative_to(self.base_path)),
                "status": "failed",
                "error": str(e)
            }
    
    def check_imports(self, manifest_path: Path, imports: Any) -> List[str]:
        """Check if imported files exist"""
        warnings = []
        manifest_dir = manifest_path.parent
        
        if hasattr(imports, 'tools'):
            for tool_path in imports.tools or []:
                if not tool_path.startswith('$'):
                    full_path = manifest_dir / tool_path
                    if not full_path.exists():
                        warnings.append(f"Tool import not found: {tool_path}")
        
        if hasattr(imports, 'agents'):
            for agent_path in imports.agents or []:
                if not agent_path.startswith('$'):
                    full_path = manifest_dir / agent_path
                    if not full_path.exists():
                        warnings.append(f"Agent import not found: {agent_path}")
        
        if hasattr(imports, 'relics'):
            for relic_path in imports.relics or []:
                if not relic_path.startswith('$'):
                    full_path = manifest_dir / relic_path
                    if not full_path.exists():
                        warnings.append(f"Relic import not found: {relic_path}")
        
        return warnings
    
    def run_tests(self) -> Dict[str, Any]:
        """Run all manifest tests"""
        manifests = self.find_manifests()
        print(f"\n{'='*70}")
        print(f"🧪 Testing Manifests in: {self.base_path}")
        print(f"{'='*70}\n")
        print(f"Found {len(manifests)} manifest files\n")
        
        for manifest_path in manifests:
            result = self.validate_manifest(manifest_path)
            self.results["total"] += 1
            
            if result["status"] == "passed":
                self.results["passed"].append(result)
                status_icon = "✅"
                status_color = "\033[92m"
            elif result["status"] == "skipped":
                status_icon = "⏭️ "
                status_color = "\033[93m"
            else:
                self.results["failed"].append(result)
                status_icon = "❌"
                status_color = "\033[91m"
            
            print(f"{status_icon} {status_color}{result['path']}\033[0m")
            
            if result["status"] == "passed":
                print(f"   Kind: {result.get('kind')}, Name: {result.get('name')}")
                if result.get("warnings"):
                    for warning in result["warnings"]:
                        print(f"   ⚠️  {warning}")
            elif result["status"] == "failed":
                print(f"   Error: {result.get('error')}")
            
            print()
        
        return self.results
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*70}")
        print("📊 Test Summary")
        print(f"{'='*70}")
        print(f"Total:  {self.results['total']}")
        print(f"✅ Passed: {len(self.results['passed'])}")
        print(f"❌ Failed: {len(self.results['failed'])}")
        
        if self.results["failed"]:
            print(f"\n{'='*70}")
            print("❌ Failed Manifests:")
            print(f"{'='*70}")
            for failed in self.results["failed"]:
                print(f"  - {failed['path']}")
                print(f"    Error: {failed['error']}")
        
        print(f"{'='*70}\n")
        
        return len(self.results["failed"]) == 0


def main():
    # Test the test_against_manifest directory
    base_path = Path(__file__).parent / "test_against_manifest"
    
    if not base_path.exists():
        print(f"❌ Error: {base_path} does not exist")
        sys.exit(1)
    
    tester = ManifestTester(base_path)
    tester.run_tests()
    success = tester.print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
