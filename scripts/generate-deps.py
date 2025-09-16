#!/usr/bin/env python3
"""
Dependency Graph Generator for Nova Infrastructure Project

Analyzes project dependencies and generates visual representations:
- Python imports → call graph
- JS/TS imports → dependency tree
- Makefile targets → execution flow
- Terraform modules → resource graph
- Docker layers → build dependencies

Outputs:
- GraphViz DOT file
- Mermaid diagram
- JSON dependency manifest
"""

import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any
import argparse


class DependencyAnalyzer:
    """Main dependency analysis coordinator"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.dependencies = {
            "python": {},
            "javascript": {},
            "makefile": {},
            "terraform": {},
            "docker": {},
            "github_actions": {},
        }

    def analyze_all(self) -> Dict[str, Any]:
        """Run all dependency analyses"""
        print("🔍 Analyzing project dependencies...")

        self.analyze_python_imports()
        self.analyze_javascript_imports()
        self.analyze_makefile_targets()
        self.analyze_terraform_modules()
        self.analyze_docker_dependencies()
        self.analyze_github_actions()

        return self.dependencies

    def analyze_python_imports(self):
        """Analyze Python import dependencies"""
        print("🐍 Analyzing Python imports...")

        python_files = list(self.project_root.rglob("*.py"))

        for py_file in python_files:
            if self._should_skip_path(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)
                imports = self._extract_python_imports(tree)

                rel_path = str(py_file.relative_to(self.project_root))
                self.dependencies["python"][rel_path] = imports

            except Exception as e:
                print(f"⚠️  Error parsing {py_file}: {e}")

    def analyze_javascript_imports(self):
        """Analyze JavaScript/TypeScript import dependencies"""
        print("📦 Analyzing JavaScript/TypeScript imports...")

        js_files = (
            list(self.project_root.rglob("*.js"))
            + list(self.project_root.rglob("*.ts"))
            + list(self.project_root.rglob("*.tsx"))
            + list(self.project_root.rglob("*.jsx"))
        )

        for js_file in js_files:
            if self._should_skip_path(js_file):
                continue

            try:
                with open(js_file, "r", encoding="utf-8") as f:
                    content = f.read()

                imports = self._extract_js_imports(content)

                rel_path = str(js_file.relative_to(self.project_root))
                self.dependencies["javascript"][rel_path] = imports

            except Exception as e:
                print(f"⚠️  Error parsing {js_file}: {e}")

    def analyze_makefile_targets(self):
        """Analyze Makefile target dependencies"""
        print("🔨 Analyzing Makefile targets...")

        makefiles = list(self.project_root.rglob("Makefile")) + list(
            self.project_root.rglob("*.mk")
        )

        for makefile in makefiles:
            try:
                with open(makefile, "r", encoding="utf-8") as f:
                    content = f.read()

                targets = self._extract_makefile_targets(content)

                rel_path = str(makefile.relative_to(self.project_root))
                self.dependencies["makefile"][rel_path] = targets

            except Exception as e:
                print(f"⚠️  Error parsing {makefile}: {e}")

    def analyze_terraform_modules(self):
        """Analyze Terraform module dependencies"""
        print("🏗️  Analyzing Terraform modules...")

        tf_files = list(self.project_root.rglob("*.tf"))

        for tf_file in tf_files:
            if self._should_skip_path(tf_file):
                continue

            try:
                with open(tf_file, "r", encoding="utf-8") as f:
                    content = f.read()

                modules = self._extract_terraform_modules(content)

                rel_path = str(tf_file.relative_to(self.project_root))
                self.dependencies["terraform"][rel_path] = modules

            except Exception as e:
                print(f"⚠️  Error parsing {tf_file}: {e}")

    def analyze_docker_dependencies(self):
        """Analyze Docker build dependencies"""
        print("🐳 Analyzing Docker dependencies...")

        dockerfiles = list(self.project_root.rglob("Dockerfile*"))

        for dockerfile in dockerfiles:
            try:
                with open(dockerfile, "r", encoding="utf-8") as f:
                    content = f.read()

                deps = self._extract_docker_dependencies(content)

                rel_path = str(dockerfile.relative_to(self.project_root))
                self.dependencies["docker"][rel_path] = deps

            except Exception as e:
                print(f"⚠️  Error parsing {dockerfile}: {e}")

    def analyze_github_actions(self):
        """Analyze GitHub Actions workflow dependencies"""
        print("⚙️  Analyzing GitHub Actions workflows...")

        workflow_files = list(
            (self.project_root / ".github" / "workflows").rglob("*.yml")
        ) + list((self.project_root / ".github" / "workflows").rglob("*.yaml"))

        for workflow_file in workflow_files:
            try:
                with open(workflow_file, "r", encoding="utf-8") as f:
                    content = f.read()

                deps = self._extract_github_actions_deps(content)

                rel_path = str(workflow_file.relative_to(self.project_root))
                self.dependencies["github_actions"][rel_path] = deps

            except Exception as e:
                print(f"⚠️  Error parsing {workflow_file}: {e}")

    def _should_skip_path(self, path: Path) -> bool:
        """Check if path should be skipped"""
        skip_patterns = [
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "node_modules",
            ".terraform",
            "work",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            "coverage",
            "dist",
            "build",
        ]

        return any(pattern in str(path) for pattern in skip_patterns)

    def _extract_python_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from Python AST"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return sorted(set(imports))

    def _extract_js_imports(self, content: str) -> List[str]:
        """Extract import statements from JavaScript/TypeScript"""
        imports = []

        # ES6 imports
        import_pattern = r"import.*?from\s+['\"]([^'\"]+)['\"]"
        imports.extend(re.findall(import_pattern, content))

        # CommonJS requires
        require_pattern = r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
        imports.extend(re.findall(require_pattern, content))

        return sorted(set(imports))

    def _extract_makefile_targets(self, content: str) -> Dict[str, List[str]]:
        """Extract Makefile targets and their dependencies"""
        targets = {}

        # Match target lines: target: dependencies
        target_pattern = r"^([a-zA-Z0-9_-]+)\s*:\s*([^#\n]*)"

        for match in re.finditer(target_pattern, content, re.MULTILINE):
            target = match.group(1).strip()
            deps = [dep.strip() for dep in match.group(2).split() if dep.strip()]
            targets[target] = deps

        return targets

    def _extract_terraform_modules(self, content: str) -> List[str]:
        """Extract Terraform module sources"""
        modules = []

        # Match module blocks
        module_pattern = r'module\s+"[^"]+"\s*\{[^}]*source\s*=\s*"([^"]+)"'
        modules.extend(re.findall(module_pattern, content, re.DOTALL))

        return sorted(set(modules))

    def _extract_docker_dependencies(self, content: str) -> Dict[str, List[str]]:
        """Extract Docker build dependencies"""
        deps = {"base_images": [], "copied_files": [], "stages": []}

        # Base images
        from_pattern = r"FROM\s+([^\s]+)"
        deps["base_images"] = re.findall(from_pattern, content)

        # Copied files
        copy_pattern = r"COPY\s+([^\s]+)"
        deps["copied_files"] = re.findall(copy_pattern, content)

        # Multi-stage build stages
        stage_pattern = r"FROM\s+[^\s]+\s+AS\s+([^\s]+)"
        deps["stages"] = re.findall(stage_pattern, content)

        return deps

    def _extract_github_actions_deps(self, content: str) -> Dict[str, List[str]]:
        """Extract GitHub Actions dependencies"""
        deps = {"actions": [], "workflows": [], "secrets": []}

        # GitHub Actions used
        action_pattern = r"uses:\s*([^\s]+)"
        deps["actions"] = re.findall(action_pattern, content)

        # Workflow calls
        workflow_pattern = r"workflow_call|workflow_dispatch"
        deps["workflows"] = re.findall(workflow_pattern, content)

        # Secrets referenced
        secret_pattern = r"\$\{\{\s*secrets\.([^}]+)\s*\}\}"
        deps["secrets"] = re.findall(secret_pattern, content)

        return deps


class OutputGenerator:
    """Generate various output formats from dependency data"""

    def __init__(self, dependencies: Dict[str, Any], output_dir: Path):
        self.dependencies = dependencies
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

    def generate_all(self):
        """Generate all output formats"""
        print("📊 Generating dependency outputs...")

        self.generate_json()
        self.generate_dot()
        self.generate_mermaid()
        self.generate_summary()

    def generate_json(self):
        """Generate JSON dependency manifest"""
        output_file = self.output_dir / "dependencies.json"

        with open(output_file, "w") as f:
            json.dump(self.dependencies, f, indent=2)

        print(f"📄 JSON manifest: {output_file}")

    def generate_dot(self):
        """Generate GraphViz DOT file"""
        output_file = self.output_dir / "dependencies.dot"

        with open(output_file, "w") as f:
            f.write("digraph ProjectDependencies {\n")
            f.write("  rankdir=LR;\n")
            f.write("  node [shape=box];\n\n")

            # Python dependencies
            self._write_python_dot(f)

            # Makefile dependencies
            self._write_makefile_dot(f)

            # Terraform dependencies
            self._write_terraform_dot(f)

            f.write("}\n")

        print(f"🔗 GraphViz DOT: {output_file}")

        # Try to generate PNG if graphviz is available
        try:
            subprocess.run(
                [
                    "dot",
                    "-Tpng",
                    str(output_file),
                    "-o",
                    str(output_file.with_suffix(".png")),
                ],
                check=True,
                capture_output=True,
            )
            print(f"🖼️  PNG diagram: {output_file.with_suffix('.png')}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("ℹ️  Install graphviz to generate PNG diagrams")

    def generate_mermaid(self):
        """Generate Mermaid diagram"""
        output_file = self.output_dir / "dependencies.mmd"

        with open(output_file, "w") as f:
            f.write("graph TD\n")

            # Makefile targets
            for makefile, targets in self.dependencies["makefile"].items():
                makefile_node = self._mermaid_safe(makefile)
                for target, deps in targets.items():
                    target_node = self._mermaid_safe(f"{makefile}::{target}")
                    f.write(f"  {makefile_node} --> {target_node}\n")

                    for dep in deps:
                        dep_node = self._mermaid_safe(f"{makefile}::{dep}")
                        f.write(f"  {dep_node} --> {target_node}\n")

        print(f"🧜 Mermaid diagram: {output_file}")

    def generate_summary(self):
        """Generate dependency summary report"""
        output_file = self.output_dir / "dependency-summary.md"

        with open(output_file, "w") as f:
            f.write("# Project Dependency Summary\n\n")
            f.write(f"Generated: {self._get_timestamp()}\n\n")

            # Statistics
            f.write("## Statistics\n\n")
            total_files = sum(len(deps) for deps in self.dependencies.values())
            f.write(f"- **Total files analyzed**: {total_files}\n")

            for dep_type, deps in self.dependencies.items():
                f.write(f"- **{dep_type.title()} files**: {len(deps)}\n")

            f.write("\n")

            # Detailed breakdown
            for dep_type, deps in self.dependencies.items():
                if not deps:
                    continue

                f.write(f"## {dep_type.title()} Dependencies\n\n")

                for file_path, file_deps in deps.items():
                    f.write(f"### `{file_path}`\n\n")

                    if isinstance(file_deps, dict):
                        for key, values in file_deps.items():
                            if values:
                                f.write(f"**{key}**: {', '.join(map(str, values))}\n\n")
                    elif isinstance(file_deps, list):
                        if file_deps:
                            f.write(f"Dependencies: {', '.join(file_deps)}\n\n")

                f.write("\n")

        print(f"📋 Summary report: {output_file}")

    def _write_python_dot(self, f):
        """Write Python dependencies to DOT file"""
        if not self.dependencies["python"]:
            return

        f.write("  // Python Dependencies\n")
        for py_file, imports in self.dependencies["python"].items():
            safe_file = self._dot_safe(py_file)
            f.write(f'  "{safe_file}" [color=blue];\n')

            for import_name in imports:
                safe_import = self._dot_safe(import_name)
                f.write(f'  "{safe_import}" -> "{safe_file}" [color=blue];\n')

        f.write("\n")

    def _write_makefile_dot(self, f):
        """Write Makefile dependencies to DOT file"""
        if not self.dependencies["makefile"]:
            return

        f.write("  // Makefile Dependencies\n")
        for makefile, targets in self.dependencies["makefile"].items():
            for target, deps in targets.items():
                safe_target = self._dot_safe(f"{makefile}::{target}")
                f.write(f'  "{safe_target}" [color=green];\n')

                for dep in deps:
                    safe_dep = self._dot_safe(f"{makefile}::{dep}")
                    f.write(f'  "{safe_dep}" -> "{safe_target}" [color=green];\n')

        f.write("\n")

    def _write_terraform_dot(self, f):
        """Write Terraform dependencies to DOT file"""
        if not self.dependencies["terraform"]:
            return

        f.write("  // Terraform Dependencies\n")
        for tf_file, modules in self.dependencies["terraform"].items():
            safe_file = self._dot_safe(tf_file)
            f.write(f'  "{safe_file}" [color=orange];\n')

            for module in modules:
                safe_module = self._dot_safe(module)
                f.write(f'  "{safe_module}" -> "{safe_file}" [color=orange];\n')

        f.write("\n")

    def _dot_safe(self, text: str) -> str:
        """Make text safe for DOT format"""
        return text.replace('"', '\\"').replace("\n", "\\n")

    def _mermaid_safe(self, text: str) -> str:
        """Make text safe for Mermaid format"""
        return re.sub(r"[^a-zA-Z0-9_]", "_", text)

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate dependency graphs for Nova Infrastructure project"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() / "work" / "dependencies",
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--format",
        choices=["json", "dot", "mermaid", "summary", "all"],
        default="all",
        help="Output format (default: all)",
    )

    args = parser.parse_args()

    # Ensure we're in a project directory
    if not (args.project_root / ".git").exists():
        print("❌ Not a git repository. Please run from project root.")
        sys.exit(1)

    # Run analysis
    analyzer = DependencyAnalyzer(args.project_root)
    dependencies = analyzer.analyze_all()

    # Generate outputs
    generator = OutputGenerator(dependencies, args.output_dir)

    if args.format == "all":
        generator.generate_all()
    else:
        method_name = f"generate_{args.format}"
        if hasattr(generator, method_name):
            getattr(generator, method_name)()
        else:
            print(f"❌ Unknown format: {args.format}")
            sys.exit(1)

    print("✅ Dependency analysis complete!")


if __name__ == "__main__":
    main()
