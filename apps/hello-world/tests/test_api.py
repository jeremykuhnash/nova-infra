"""Tests for Flask API module."""

import json
import os
import sys
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import app, parse_terraform  # noqa: E402


class TestFlaskAPI:
    """Test suite for Flask API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert data["service"] == "tf-visualizer"
        assert "version" in data

    def test_sample_data(self, client):
        """Test sample data endpoint."""
        response = client.get("/api/sample")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True
        assert "data" in data

        sample_data = data["data"]
        assert "entities" in sample_data
        assert "relationships" in sample_data
        assert "metadata" in sample_data

        # Check sample entities
        assert len(sample_data["entities"]) > 0
        assert len(sample_data["relationships"]) > 0

    def test_parse_directory_missing_data(self, client):
        """Test parse directory with missing data."""
        response = client.post("/api/parse-directory", json={})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data

    def test_parse_directory_invalid_path(self, client):
        """Test parse directory with invalid path."""
        response = client.post("/api/parse-directory", json={"directory": "/nonexistent/path"})
        assert response.status_code == 404

        data = json.loads(response.data)
        assert "error" in data

    def test_parse_files_no_files(self, client):
        """Test parse files without files."""
        response = client.post("/api/parse")
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "No files provided" in data["error"]

    def test_frontend_fallback(self, client):
        """Test frontend fallback behavior."""
        from pathlib import Path

        response = client.get("/")

        # Check if frontend build exists
        frontend_build = Path(__file__).parent.parent / "frontend" / "build" / "index.html"

        if frontend_build.exists():
            # When frontend exists, it should serve the index.html
            assert response.status_code == 200
            # The actual index.html content would be returned
        else:
            # When frontend build doesn't exist, API returns 404 with error message
            assert response.status_code == 404
            data = json.loads(response.data)
            assert data["error"] == "Frontend not configured"

    def test_parse_terraform_function(self, tmp_path):
        """Test the parse_terraform helper function."""
        # Create a test .tf file
        test_dir = tmp_path / "test_terraform"
        test_dir.mkdir()
        test_file = test_dir / "main.tf"
        test_file.write_text('resource "aws_instance" "test" {\n  ami = "ami-123"\n}')

        output_file = tmp_path / "output.json"

        result = parse_terraform(str(test_dir), str(output_file))

        assert "entities" in result
        assert "relationships" in result
        assert output_file.exists()

    def test_parse_files_with_uploaded_files(self, client, tmp_path):
        """Test parse files with actual uploaded files."""
        # Create test files using proper multipart format
        data = {}
        data["files"] = [
            (BytesIO(b'resource "aws_instance" "test" { ami = "ami-123" }'), "main.tf")
        ]

        with patch("backend.api.parse_terraform") as mock_parse:
            mock_parse.return_value = {"entities": [], "relationships": []}

            response = client.post("/api/parse", data=data, content_type="multipart/form-data")
            assert response.status_code == 200

            result = json.loads(response.data)
            assert result["success"] is True
            assert "data" in result
            mock_parse.assert_called_once()

    def test_parse_files_with_empty_file_list(self, client):
        """Test parse files with empty file list."""
        # Send request with files parameter but empty list
        data: dict = {"files": []}
        response = client.post("/api/parse", data=data)
        assert response.status_code == 400

        result = json.loads(response.data)
        assert "error" in result

    def test_parse_files_with_exception(self, client):
        """Test parse files when exception occurs."""
        data = {}
        data["files"] = [
            (BytesIO(b'resource "aws_instance" "test" { ami = "ami-123" }'), "main.tf")
        ]

        with patch("backend.api.parse_terraform") as mock_parse:
            mock_parse.side_effect = Exception("Parse error")

            response = client.post("/api/parse", data=data, content_type="multipart/form-data")
            assert response.status_code == 500

            result = json.loads(response.data)
            assert result["success"] is False
            assert "error" in result
            assert "Parse error" in result["error"]

    def test_parse_directory_with_path_mappings(self, client):
        """Test parse directory with various path mappings."""
        # Test with known alias
        with patch("backend.api.os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("backend.api.parse_terraform") as mock_parse:
                mock_parse.return_value = {"entities": [], "relationships": []}

                # Test with known alias "terraform"
                response = client.post("/api/parse-directory", json={"directory": "terraform"})
                assert response.status_code == 200
                mock_parse.assert_called_with(
                    "/app/project/terraform", "work/build/tf_entities.json"
                )

                # Test with project/ prefix
                response = client.post(
                    "/api/parse-directory", json={"directory": "project/some/path"}
                )
                assert response.status_code == 200
                mock_parse.assert_called_with(
                    "/app/project/some/path", "work/build/tf_entities.json"
                )

    def test_parse_directory_with_exception(self, client):
        """Test parse directory when exception occurs."""
        with patch("backend.api.os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("backend.api.parse_terraform") as mock_parse:
                mock_parse.side_effect = Exception("Directory parse error")

                response = client.post("/api/parse-directory", json={"directory": "/some/path"})
                assert response.status_code == 500

                data = json.loads(response.data)
                assert data["success"] is False
                assert "error" in data
                assert "Directory parse error" in data["error"]

    def test_get_entities_no_cache(self, client):
        """Test get entities when no cache exists."""
        with patch("backend.api.os.path.exists") as mock_exists:
            # First call for entities_file check
            mock_exists.side_effect = [False, True, False, False]

            with patch("backend.api.parse_terraform") as mock_parse:
                mock_parse.return_value = {"entities": ["test"], "relationships": []}

                with patch.dict(os.environ, {"TF_SCAN_PATHS": "/app/project/terraform"}):
                    response = client.get("/api/entities")
                    assert response.status_code == 200

                    data = json.loads(response.data)
                    assert data["success"] is True
                    assert "data" in data
                    assert "source" in data

    def test_get_entities_fallback_to_test_data(self, client):
        """Test get entities fallback to test data."""
        with patch("backend.api.os.path.exists") as mock_exists:
            # Simulate: no cache, scan paths don't exist, but test-terraform exists
            def exists_side_effect(path):
                if "tf_entities.json" in path:
                    return False
                if "/app/project/terraform" in path or "/app/project/helm" in path:
                    return False
                if "/app/test-terraform" in path:
                    return True
                return False

            mock_exists.side_effect = exists_side_effect

            with patch("backend.api.parse_terraform") as mock_parse:
                mock_parse.return_value = {"entities": ["test"], "relationships": []}

                response = client.get("/api/entities")
                assert response.status_code == 200

                data = json.loads(response.data)
                assert data["success"] is True
                assert data["source"] == "test-data"

    def test_get_entities_fallback_to_local_terraform(self, client):
        """Test get entities fallback to local terraform directory."""
        with patch("backend.api.os.path.exists") as mock_exists:
            # Simulate: no cache, no project paths, no test data, but local terraform exists
            mock_exists.side_effect = [False, False, False, True]

            with patch("backend.api.parse_terraform") as mock_parse:
                mock_parse.return_value = {"entities": ["local"], "relationships": []}

                response = client.get("/api/entities")
                assert response.status_code == 200

                data = json.loads(response.data)
                assert data["success"] is True

    def test_get_entities_no_terraform_found(self, client):
        """Test get entities when no terraform files found."""
        with patch("backend.api.os.path.exists") as mock_exists:
            # Everything returns False
            mock_exists.return_value = False

            response = client.get("/api/entities")
            assert response.status_code == 404

            data = json.loads(response.data)
            assert data["success"] is False
            assert "No terraform files found" in data["error"]

    def test_get_entities_parse_exception(self, client):
        """Test get entities when parsing fails."""
        with patch("backend.api.os.path.exists") as mock_exists:

            def exists_side_effect(path):
                if "tf_entities.json" in path:
                    return False
                if "/app/project" in path or "/app/test-terraform" in path:
                    return False
                if "./terraform" in path:
                    return True
                return False

            mock_exists.side_effect = exists_side_effect

            with patch("backend.api.parse_terraform") as mock_parse:
                mock_parse.side_effect = Exception("Parse failed")

                response = client.get("/api/entities")
                assert response.status_code == 500

                data = json.loads(response.data)
                assert data["success"] is False
                assert "Failed to parse terraform directory" in data["error"]

    def test_get_entities_with_cache(self, client, tmp_path):
        """Test get entities when cache exists."""
        # Create cache file
        cache_data = {"entities": ["cached"], "relationships": []}
        cache_file = tmp_path / "tf_entities.json"
        cache_file.write_text(json.dumps(cache_data))

        with patch("backend.api.os.path.exists") as mock_exists:
            mock_exists.return_value = True

            with patch("builtins.open") as mock_open:
                # Need to actually open the file we created
                mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
                    cache_data
                )

                response = client.get("/api/entities")
                assert response.status_code == 200

                data = json.loads(response.data)
                assert data["success"] is True
                assert data["data"]["entities"][0] == "cached"

    def test_get_entities_cache_read_error(self, client):
        """Test get entities when cache read fails."""
        with patch("backend.api.os.path.exists") as mock_exists:
            mock_exists.return_value = True

            with patch("builtins.open") as mock_open:
                mock_open.side_effect = Exception("Read error")

                response = client.get("/api/entities")
                assert response.status_code == 500

                data = json.loads(response.data)
                assert data["success"] is False
                assert "Failed to load entities" in data["error"]

    def test_get_scan_paths(self, client):
        """Test get scan paths endpoint."""
        with patch("backend.api.os.path.exists") as mock_exists:
            mock_exists.side_effect = [
                True,
                False,
                True,
            ]  # First path exists, second doesn't, test path exists

            with patch("backend.api.Path") as mock_path:
                # Mock Path.rglob to return some .tf files
                mock_path_instance = MagicMock()
                mock_path_instance.rglob.return_value = ["main.tf", "variables.tf"]
                mock_path.return_value = mock_path_instance

                with patch.dict(
                    os.environ, {"TF_SCAN_PATHS": "/app/project/terraform,/app/project/missing"}
                ):
                    response = client.get("/api/scan-paths")
                    assert response.status_code == 200

                    data = json.loads(response.data)
                    assert data["success"] is True
                    assert "paths" in data
                    assert len(data["paths"]) == 2  # One configured path + test path

                    # Check first path
                    assert data["paths"][0]["path"] == "/app/project/terraform"
                    assert data["paths"][0]["exists"] is True
                    assert data["paths"][0]["file_count"] == 2

                    # Check test path
                    assert data["paths"][1]["path"] == "/app/test-terraform"
                    assert data["paths"][1]["is_test"] is True

    def test_get_entities_test_data_parse_exception(self, client):
        """Test get entities when test data parsing fails silently."""
        with patch("backend.api.os.path.exists") as mock_exists:

            def exists_side_effect(path):
                if "tf_entities.json" in path:
                    return False
                if "/app/project" in path:
                    return False
                if "/app/test-terraform" in path:
                    return True
                if "./terraform" in path:
                    return False
                return False

            mock_exists.side_effect = exists_side_effect

            with patch("backend.api.parse_terraform") as mock_parse:
                # Test data parse fails, falls through to no files found
                mock_parse.side_effect = Exception("Test parse failed")

                response = client.get("/api/entities")
                assert response.status_code == 404

                data = json.loads(response.data)
                assert data["success"] is False
                assert "No terraform files found" in data["error"]

    def test_get_entities_scan_path_parse_exception(self, client):
        """Test get entities when scan path parsing fails but continues."""
        with patch("backend.api.os.path.exists") as mock_exists:
            # No cache, first scan path exists but fails, test path exists and works
            mock_exists.side_effect = [False, True, True]

            with patch("backend.api.parse_terraform") as mock_parse:
                # First call fails, second succeeds
                mock_parse.side_effect = [
                    Exception("Parse error"),
                    {"entities": ["test"], "relationships": []},
                ]

                with patch.dict(os.environ, {"TF_SCAN_PATHS": "/app/project/terraform"}):
                    response = client.get("/api/entities")
                    assert response.status_code == 200

                    data = json.loads(response.data)
                    assert data["success"] is True
                    assert data["source"] == "test-data"
