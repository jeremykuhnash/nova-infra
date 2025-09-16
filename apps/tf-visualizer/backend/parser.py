"""Terraform configuration parser that extracts entities and relationships."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import hcl2
import lark


@dataclass
class TerraformEntity:
    """Represents a Terraform entity (resource, data source, module, etc.)."""

    id: str
    type: str
    category: str  # resource, data, module, variable, output, provider
    name: str
    provider: str | None
    attributes: dict[str, Any]
    dependencies: list[str]
    position: dict[str, int] | None = None


class TerraformParser:
    """Parses Terraform configuration files and extracts entities and relationships."""

    def __init__(self, terraform_dir: str):
        """Initialize parser with terraform directory path."""
        self.terraform_dir = Path(terraform_dir)
        self.entities: dict[str, TerraformEntity] = {}
        self.relationships: list[dict[str, str]] = []

    def parse_directory(self) -> dict[str, Any]:
        """Parse all .tf files in the directory and return entities and relationships."""
        tf_files = list(self.terraform_dir.rglob("*.tf"))

        for tf_file in tf_files:
            self._parse_file(tf_file)

        return {
            "entities": [asdict(e) for e in self.entities.values()],
            "relationships": self.relationships,
            "metadata": {
                "total_files": len(tf_files),
                "total_entities": len(self.entities),
                "total_relationships": len(self.relationships),
            },
        }

    def _parse_file(self, file_path: Path) -> None:
        """Parse a single Terraform file."""
        try:
            with open(file_path) as f:
                content = f.read()

            # Parse HCL content
            parsed = hcl2.loads(content)

            # Extract resources
            if "resource" in parsed:
                self._extract_resources(parsed["resource"])

            # Extract data sources
            if "data" in parsed:
                self._extract_data_sources(parsed["data"])

            # Extract modules
            if "module" in parsed:
                self._extract_modules(parsed["module"])

            # Extract variables
            if "variable" in parsed:
                self._extract_variables(parsed["variable"])

            # Extract outputs
            if "output" in parsed:
                self._extract_outputs(parsed["output"])

            # Extract providers
            if "provider" in parsed:
                self._extract_providers(parsed["provider"])

        except (lark.exceptions.LarkError, json.JSONDecodeError) as e:
            print(f"Error parsing {file_path}: {e}")

    def _extract_resources(self, resources: list[dict]) -> None:
        """Extract resource entities from parsed HCL."""
        for resource in resources:
            for resource_type, instances in resource.items():
                for name, config in instances.items():
                    entity_id = f"resource.{resource_type}.{name}"

                    # Extract provider from resource type
                    provider = resource_type.split("_")[0]

                    # Extract dependencies
                    deps = self._extract_dependencies(config)

                    entity = TerraformEntity(
                        id=entity_id,
                        type=resource_type,
                        category="resource",
                        name=name,
                        provider=provider,
                        attributes=config,
                        dependencies=deps,
                    )

                    self.entities[entity_id] = entity

                    # Create relationships
                    for dep in deps:
                        self.relationships.append(
                            {"source": entity_id, "target": dep, "type": "depends_on"}
                        )

    def _extract_data_sources(self, data_sources: list[dict]) -> None:
        """Extract data source entities from parsed HCL."""
        for data in data_sources:
            for data_type, instances in data.items():
                for name, config in instances.items():
                    entity_id = f"data.{data_type}.{name}"

                    # Extract provider from data source type
                    provider = data_type.split("_")[0]

                    # Extract dependencies
                    deps = self._extract_dependencies(config)

                    entity = TerraformEntity(
                        id=entity_id,
                        type=data_type,
                        category="data",
                        name=name,
                        provider=provider,
                        attributes=config,
                        dependencies=deps,
                    )

                    self.entities[entity_id] = entity

                    # Create relationships
                    for dep in deps:
                        self.relationships.append(
                            {"source": entity_id, "target": dep, "type": "depends_on"}
                        )

    def _extract_modules(self, modules: list[dict]) -> None:
        """Extract module entities from parsed HCL."""
        for module in modules:
            for name, config in module.items():
                entity_id = f"module.{name}"

                # Extract dependencies
                deps = self._extract_dependencies(config)

                entity = TerraformEntity(
                    id=entity_id,
                    type="module",
                    category="module",
                    name=name,
                    provider=None,
                    attributes=config,
                    dependencies=deps,
                )

                self.entities[entity_id] = entity

                # Create relationships
                for dep in deps:
                    self.relationships.append(
                        {"source": entity_id, "target": dep, "type": "depends_on"}
                    )

    def _extract_variables(self, variables: list[dict]) -> None:
        """Extract variable entities from parsed HCL."""
        for var in variables:
            for name, config in var.items():
                entity_id = f"var.{name}"

                entity = TerraformEntity(
                    id=entity_id,
                    type="variable",
                    category="variable",
                    name=name,
                    provider=None,
                    attributes=config,
                    dependencies=[],
                )

                self.entities[entity_id] = entity

    def _extract_outputs(self, outputs: list[dict]) -> None:
        """Extract output entities from parsed HCL."""
        for output in outputs:
            for name, config in output.items():
                entity_id = f"output.{name}"

                # Extract dependencies from value references
                deps = self._extract_dependencies(config)

                entity = TerraformEntity(
                    id=entity_id,
                    type="output",
                    category="output",
                    name=name,
                    provider=None,
                    attributes=config,
                    dependencies=deps,
                )

                self.entities[entity_id] = entity

                # Create relationships
                for dep in deps:
                    self.relationships.append(
                        {"source": entity_id, "target": dep, "type": "references"}
                    )

    def _extract_providers(self, providers: list[dict]) -> None:
        """Extract provider entities from parsed HCL."""
        for provider in providers:
            for name, config in provider.items():
                entity_id = f"provider.{name}"

                entity = TerraformEntity(
                    id=entity_id,
                    type="provider",
                    category="provider",
                    name=name,
                    provider=name,
                    attributes=config,
                    dependencies=[],
                )

                self.entities[entity_id] = entity

    def _extract_dependencies(self, config: dict[str, Any]) -> list[str]:
        """Extract dependencies from configuration references."""
        deps = []

        # Check explicit depends_on
        if "depends_on" in config:
            for dep in config["depends_on"]:
                if isinstance(dep, str):
                    deps.append(dep)

        # Parse references in string values (simplified)
        for _key, value in config.items():
            if isinstance(value, str):
                # Look for terraform references like ${resource.type.name}
                refs = self._find_references(value)
                deps.extend(refs)
            elif isinstance(value, dict):
                # Recursively check nested dictionaries
                nested_deps = self._extract_dependencies(value)
                deps.extend(nested_deps)
            elif isinstance(value, list):
                # Check items in lists
                for item in value:
                    if isinstance(item, str):
                        refs = self._find_references(item)
                        deps.extend(refs)
                    elif isinstance(item, dict):
                        nested_deps = self._extract_dependencies(item)
                        deps.extend(nested_deps)

        return list(set(deps))  # Remove duplicates

    def _find_references(self, text: str) -> list[str]:
        """Find Terraform references in text."""
        import re

        refs = []

        # Handle ${} syntax and regular references
        text = text.replace("${", "").replace("}", "")

        # Match patterns for Terraform references
        patterns = [
            # AWS resources without explicit 'resource' prefix
            (r"(aws_\w+)\.(\w+)", "resource"),
            (r"(azurerm_\w+)\.(\w+)", "resource"),
            (r"(google_\w+)\.(\w+)", "resource"),
            # Explicit resource references
            (r"resource\.(\w+)\.(\w+)", "resource"),
            # Data sources
            (r"data\.(\w+)\.(\w+)", "data"),
            # Modules
            (r"module\.(\w+)", "module"),
            # Variables
            (r"var\.(\w+)", "var"),
            # Locals
            (r"local\.(\w+)", "local"),
            # Outputs
            (r"output\.(\w+)", "output"),
        ]

        for pattern, prefix_type in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    # Two-part reference (resource/data)
                    if prefix_type == "resource" and not pattern.startswith(
                        r"resource"
                    ):
                        # AWS/Azure/Google resource without 'resource' prefix
                        refs.append(f"resource.{match[0]}.{match[1]}")
                    else:
                        refs.append(f"{prefix_type}.{match[0]}.{match[1]}")
                elif isinstance(match, str):
                    # Single-part reference (module/var/local/output)
                    refs.append(f"{prefix_type}.{match}")

        return list(set(refs))  # Remove duplicates

    def calculate_layout(self) -> None:
        """Calculate positions for entities for visualization."""
        # Simple grid layout
        categories: dict[str, list[TerraformEntity]] = {}
        for entity in self.entities.values():
            if entity.category not in categories:
                categories[entity.category] = []
            categories[entity.category].append(entity)

        x_offset = 0
        for _category, entities in categories.items():
            y_offset = 0
            for entity in entities:
                entity.position = {"x": x_offset * 250, "y": y_offset * 150}
                y_offset += 1
            x_offset += 1

    def save_to_json(self, output_path: str) -> None:
        """Save parsed entities and relationships to JSON file."""
        self.calculate_layout()

        result = self.parse_directory()

        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(result, f, indent=2, default=str)

        print(f"Terraform entities saved to {output_path}")


def parse_terraform(
    terraform_dir: str, output_path: str = "work/build/tf_entities.json"
) -> dict[str, Any]:
    """Main function to parse Terraform configuration."""
    parser = TerraformParser(terraform_dir)
    parser.save_to_json(output_path)
    return parser.parse_directory()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        tf_dir = sys.argv[1]
    else:
        tf_dir = "./terraform"

    output = sys.argv[2] if len(sys.argv) > 2 else "work/build/tf_entities.json"

    result = parse_terraform(tf_dir, output)
    print(
        f"Parsed {result['metadata']['total_entities']} entities and {result['metadata']['total_relationships']} relationships"
    )
