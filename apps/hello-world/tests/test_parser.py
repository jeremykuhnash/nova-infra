"""Tests for Terraform parser module."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.parser import TerraformParser, parse_terraform  # noqa: E402


class TestTerraformParser:
    """Test suite for TerraformParser class."""

    @pytest.fixture
    def sample_terraform_config(self):
        """Create sample Terraform configuration for testing."""
        return """
        provider "aws" {
          region = "us-east-1"
        }

        variable "instance_type" {
          default = "t2.micro"
        }

        data "aws_ami" "ubuntu" {
          most_recent = true

          filter {
            name   = "name"
            values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
          }
        }

        resource "aws_vpc" "main" {
          cidr_block = "10.0.0.0/16"

          tags = {
            Name = "main-vpc"
          }
        }

        resource "aws_subnet" "public" {
          vpc_id     = aws_vpc.main.id
          cidr_block = "10.0.1.0/24"

          tags = {
            Name = "public-subnet"
          }
        }

        resource "aws_instance" "web" {
          ami           = data.aws_ami.ubuntu.id
          instance_type = var.instance_type
          subnet_id     = aws_subnet.public.id

          tags = {
            Name = "web-server"
          }
        }

        output "instance_id" {
          value = aws_instance.web.id
        }

        module "security" {
          source = "./modules/security"
          vpc_id = aws_vpc.main.id
        }
        """

    @pytest.fixture
    def temp_tf_dir(self, sample_terraform_config):
        """Create temporary directory with Terraform configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tf_file = Path(tmpdir) / "main.tf"
            tf_file.write_text(sample_terraform_config)
            yield tmpdir

    def test_parser_initialization(self, temp_tf_dir):
        """Test parser initialization."""
        parser = TerraformParser(temp_tf_dir)
        assert parser.terraform_dir == Path(temp_tf_dir)
        assert parser.entities == {}
        assert parser.relationships == []

    def test_parse_directory(self, temp_tf_dir):
        """Test parsing Terraform directory."""
        parser = TerraformParser(temp_tf_dir)
        result = parser.parse_directory()

        # Check structure
        assert "entities" in result
        assert "relationships" in result
        assert "metadata" in result

        # Check metadata
        assert result["metadata"]["total_files"] == 1
        assert result["metadata"]["total_entities"] > 0

        # Check for expected entities
        entity_ids = [e["id"] for e in result["entities"]]
        assert "resource.aws_vpc.main" in entity_ids
        assert "resource.aws_subnet.public" in entity_ids
        assert "resource.aws_instance.web" in entity_ids
        assert "data.aws_ami.ubuntu" in entity_ids
        assert "var.instance_type" in entity_ids
        assert "output.instance_id" in entity_ids
        assert "module.security" in entity_ids
        assert "provider.aws" in entity_ids

    def test_extract_resources(self, temp_tf_dir):
        """Test resource extraction."""
        parser = TerraformParser(temp_tf_dir)
        parser.parse_directory()

        # Check VPC resource
        vpc = parser.entities.get("resource.aws_vpc.main")
        assert vpc is not None
        assert vpc.type == "aws_vpc"
        assert vpc.category == "resource"
        assert vpc.name == "main"
        assert vpc.provider == "aws"

        # Check subnet resource
        subnet = parser.entities.get("resource.aws_subnet.public")
        assert subnet is not None
        assert subnet.type == "aws_subnet"
        assert "resource.aws_vpc.main" in subnet.dependencies

    def test_extract_data_sources(self, temp_tf_dir):
        """Test data source extraction."""
        parser = TerraformParser(temp_tf_dir)
        parser.parse_directory()

        ami = parser.entities.get("data.aws_ami.ubuntu")
        assert ami is not None
        assert ami.type == "aws_ami"
        assert ami.category == "data"
        assert ami.name == "ubuntu"

    def test_extract_variables(self, temp_tf_dir):
        """Test variable extraction."""
        parser = TerraformParser(temp_tf_dir)
        parser.parse_directory()

        var = parser.entities.get("var.instance_type")
        assert var is not None
        assert var.type == "variable"
        assert var.category == "variable"
        assert var.name == "instance_type"

    def test_extract_outputs(self, temp_tf_dir):
        """Test output extraction."""
        parser = TerraformParser(temp_tf_dir)
        parser.parse_directory()

        output = parser.entities.get("output.instance_id")
        assert output is not None
        assert output.type == "output"
        assert output.category == "output"
        assert "resource.aws_instance.web" in output.dependencies

    def test_extract_modules(self, temp_tf_dir):
        """Test module extraction."""
        parser = TerraformParser(temp_tf_dir)
        parser.parse_directory()

        module = parser.entities.get("module.security")
        assert module is not None
        assert module.type == "module"
        assert module.category == "module"
        assert "resource.aws_vpc.main" in module.dependencies

    def test_extract_relationships(self, temp_tf_dir):
        """Test relationship extraction."""
        parser = TerraformParser(temp_tf_dir)
        result = parser.parse_directory()

        relationships = result["relationships"]
        assert len(relationships) > 0

        # Check for expected relationships
        subnet_to_vpc = any(
            r["source"] == "resource.aws_subnet.public" and r["target"] == "resource.aws_vpc.main"
            for r in relationships
        )
        assert subnet_to_vpc

        instance_to_subnet = any(
            r["source"] == "resource.aws_instance.web"
            and r["target"] == "resource.aws_subnet.public"
            for r in relationships
        )
        assert instance_to_subnet

    def test_find_references(self, temp_tf_dir):
        """Test reference finding in text."""
        parser = TerraformParser(temp_tf_dir)

        # Test various reference patterns
        refs = parser._find_references("${aws_vpc.main.id}")
        assert "resource.aws_vpc.main" in refs

        refs = parser._find_references("data.aws_ami.ubuntu.id")
        assert "data.aws_ami.ubuntu" in refs

        refs = parser._find_references("var.instance_type")
        assert "var.instance_type" in refs

        refs = parser._find_references("module.security.output_value")
        assert "module.security" in refs

    def test_calculate_layout(self, temp_tf_dir):
        """Test layout calculation for visualization."""
        parser = TerraformParser(temp_tf_dir)
        parser.parse_directory()
        parser.calculate_layout()

        # Check that all entities have positions
        for entity in parser.entities.values():
            assert entity.position is not None
            assert "x" in entity.position
            assert "y" in entity.position
            assert isinstance(entity.position["x"], int)
            assert isinstance(entity.position["y"], int)

    def test_save_to_json(self, temp_tf_dir):
        """Test saving to JSON file."""
        parser = TerraformParser(temp_tf_dir)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            output_path = tmp.name

        try:
            parser.save_to_json(output_path)

            # Check file exists and is valid JSON
            assert Path(output_path).exists()

            with open(output_path) as f:
                data = json.load(f)

            assert "entities" in data
            assert "relationships" in data
            assert "metadata" in data

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_parse_terraform_function(self, temp_tf_dir):
        """Test main parse_terraform function."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            output_path = tmp.name

        try:
            result = parse_terraform(temp_tf_dir, output_path)

            assert "entities" in result
            assert "relationships" in result
            assert "metadata" in result

            # Check file was created
            assert Path(output_path).exists()

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_empty_directory(self):
        """Test parsing empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parser = TerraformParser(tmpdir)
            result = parser.parse_directory()

            assert result["metadata"]["total_files"] == 0
            assert result["metadata"]["total_entities"] == 0
            assert result["metadata"]["total_relationships"] == 0
            assert result["entities"] == []
            assert result["relationships"] == []

    def test_invalid_hcl(self):
        """Test handling of invalid HCL content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tf_file = Path(tmpdir) / "invalid.tf"
            tf_file.write_text("this is not valid HCL {{{")

            parser = TerraformParser(tmpdir)
            result = parser.parse_directory()

            # Should handle error gracefully
            assert result["metadata"]["total_files"] == 1
            assert result["metadata"]["total_entities"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
