"""Flask API for Terraform parser."""

import json
import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from .parser import TerraformParser

# Initialize Flask app
app = Flask(__name__, static_folder="../frontend/build", static_url_path="/")
CORS(app)


def parse_terraform(directory: str, output_path: str) -> dict:
    """Parse Terraform files from a directory."""
    parser = TerraformParser(directory)
    result = parser.parse_directory()
    parser.save_to_json(output_path)
    return result


@app.route("/")
@app.route("/<path:path>")
def serve_frontend(path=""):
    """Serve the React frontend."""
    if (
        path
        and app.static_folder
        and os.path.exists(os.path.join(app.static_folder, path))
    ):
        return send_from_directory(app.static_folder, path)
    if app.static_folder:
        return send_from_directory(app.static_folder, "index.html")
    return jsonify({"error": "Frontend not configured"}), 404


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {"status": "healthy", "service": "tf-visualizer", "version": "1.0.0"}
    )


@app.route("/api/parse", methods=["POST"])
def parse_terraform_files():
    """Parse uploaded Terraform files."""
    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")

    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    # Create temporary directory for uploaded files
    temp_dir = Path("work/uploads")
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Save uploaded files
        for file in files:
            if file.filename and file.filename.endswith(".tf"):
                file_path = temp_dir / file.filename
                file.save(str(file_path))

        # Parse the files
        output_path = "work/build/tf_entities.json"
        result = parse_terraform(str(temp_dir), output_path)

        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        # Clean up temporary files
        for file_path in temp_dir.glob("*.tf"):
            file_path.unlink()


@app.route("/api/parse-directory", methods=["POST"])
def parse_terraform_directory():
    """Parse Terraform files from a directory path."""
    data = request.get_json()

    if not data or "directory" not in data:
        return jsonify({"error": "No directory path provided"}), 400

    directory = data["directory"]

    # Map relative paths to container paths
    path_mappings = {
        "terraform": "/app/project/terraform",
        "helm": "/app/project/helm",
        "test": "/app/test-terraform",
    }

    # If it's a known alias, map it
    if directory in path_mappings:
        directory = path_mappings[directory]
    # If it's a relative path starting with project/, prepend /app/
    elif directory.startswith("project/"):
        directory = f"/app/{directory}"

    if not os.path.exists(directory):
        return jsonify({"error": f"Directory {directory} does not exist"}), 404

    try:
        output_path = "work/build/tf_entities.json"
        result = parse_terraform(directory, output_path)

        return jsonify({"success": True, "data": result, "source": directory})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/entities", methods=["GET"])
def get_entities():
    """Get cached entities from last parse."""
    entities_file = "work/build/tf_entities.json"

    if not os.path.exists(entities_file):
        # Try to parse from configured paths or defaults
        scan_paths = os.environ.get(
            "TF_SCAN_PATHS",
            "/app/terraform-examples,/app/project/terraform,/app/project/helm",
        ).split(",")

        for path in scan_paths:
            path = path.strip()
            if os.path.exists(path):
                try:
                    result = parse_terraform(path, entities_file)
                    return jsonify({"success": True, "data": result, "source": path})
                except Exception:
                    continue  # Try next path

        # Fallback to test data if no project files found
        if os.path.exists("/app/test-terraform"):
            try:
                result = parse_terraform("/app/test-terraform", entities_file)
                return jsonify({"success": True, "data": result, "source": "test-data"})
            except Exception:
                pass

        # If nothing works, check old default
        if os.path.exists("./terraform"):
            try:
                result = parse_terraform("./terraform", entities_file)
                return jsonify({"success": True, "data": result})
            except Exception as e:
                return jsonify(
                    {
                        "success": False,
                        "error": f"Failed to parse terraform directory: {str(e)}",
                    }
                ), 500
        else:
            return jsonify(
                {
                    "success": False,
                    "error": "No terraform files found. Please upload or specify a directory.",
                }
            ), 404

    # Load cached entities
    try:
        with open(entities_file, "r") as f:
            data = json.load(f)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify(
            {"success": False, "error": f"Failed to load entities: {str(e)}"}
        ), 500


@app.route("/api/sample", methods=["GET"])
def get_sample_data():
    """Get sample data for testing."""
    sample_data = {
        "entities": [
            {
                "id": "provider.aws",
                "type": "provider",
                "name": "aws",
                "provider": "aws",
                "category": "provider",
                "attributes": {"region": "us-east-1"},
                "dependencies": [],
                "position": {"x": 0, "y": 0},
            },
            {
                "id": "resource.aws_vpc.main",
                "type": "aws_vpc",
                "name": "main",
                "provider": "aws",
                "category": "network",
                "attributes": {
                    "cidr_block": "10.0.0.0/16",
                    "enable_dns_hostnames": True,
                },
                "dependencies": ["provider.aws"],
                "position": {"x": 200, "y": 0},
            },
            {
                "id": "resource.aws_subnet.public",
                "type": "aws_subnet",
                "name": "public",
                "provider": "aws",
                "category": "network",
                "attributes": {
                    "cidr_block": "10.0.1.0/24",
                    "availability_zone": "us-east-1a",
                },
                "dependencies": ["resource.aws_vpc.main"],
                "position": {"x": 400, "y": 0},
            },
        ],
        "relationships": [
            {
                "source": "provider.aws",
                "target": "resource.aws_vpc.main",
                "type": "provides",
            },
            {
                "source": "resource.aws_vpc.main",
                "target": "resource.aws_subnet.public",
                "type": "contains",
            },
        ],
        "metadata": {
            "total_entities": 3,
            "total_relationships": 2,
            "providers": ["aws"],
            "resource_types": ["aws_vpc", "aws_subnet"],
        },
    }

    return jsonify({"success": True, "data": sample_data})


@app.route("/api/scan-paths", methods=["GET"])
def get_scan_paths():
    """Get available directories to scan."""
    paths = []

    # Check configured paths
    scan_paths = os.environ.get(
        "TF_SCAN_PATHS", "/app/project/terraform,/app/project/helm"
    ).split(",")

    for path in scan_paths:
        path = path.strip()
        if os.path.exists(path):
            # Count .tf files in the directory
            tf_files = list(Path(path).rglob("*.tf"))
            paths.append(
                {
                    "path": path,
                    "name": os.path.basename(path),
                    "exists": True,
                    "file_count": len(tf_files),
                }
            )

    # Add test data if available
    if os.path.exists("/app/test-terraform"):
        tf_files = list(Path("/app/test-terraform").rglob("*.tf"))
        paths.append(
            {
                "path": "/app/test-terraform",
                "name": "test-terraform",
                "exists": True,
                "file_count": len(tf_files),
                "is_test": True,
            }
        )

    return jsonify({"success": True, "paths": paths})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
