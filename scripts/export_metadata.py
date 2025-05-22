import os
import xml.etree.ElementTree as ET
import json

PROJECTS_DIR = "./cloned_repos"

def extract_metadata(pom_file):
    """Extract metadata with improved XML handling"""
    try:
        with open(pom_file, "r", encoding="utf-8") as file:
            tree = ET.parse(file)
        root = tree.getroot()

        # Namespace handling
        ns = "{http://maven.apache.org/POM/4.0.0}"

        metadata = {
            "repository_name": os.path.basename(os.path.dirname(pom_file)),
            "project_name": root.find(f"{ns}artifactId").text if root.find(f"{ns}artifactId") is not None else "Unknown",
            "group_id": root.find(f"{ns}groupId").text if root.find(f"{ns}groupId") is not None else "Unknown",
            "version": root.find(f"{ns}version").text if root.find(f"{ns}version") is not None else "Unknown",
            "dependencies": []
        }

        # Handle missing groupId/version in <parent>
        if metadata["group_id"] == "Unknown":
            parent = root.find(f"{ns}parent")
            if parent is not None and parent.find(f"{ns}groupId") is not None:
                metadata["group_id"] = parent.find(f"{ns}groupId").text

        if metadata["version"] == "Unknown":
            parent = root.find(f"{ns}parent")
            if parent is not None and parent.find(f"{ns}version") is not None:
                metadata["version"] = parent.find(f"{ns}version").text

        # Extract dependencies
        dependencies = root.find(f"{ns}dependencies")
        if dependencies is not None:
            for dep in dependencies.findall(f"{ns}dependency"):
                dep_info = {
                    "group_id": dep.find(f"{ns}groupId").text if dep.find(f"{ns}groupId") is not None else "Unknown",
                    "artifact_id": dep.find(f"{ns}artifactId").text if dep.find(f"{ns}artifactId") is not None else "Unknown",
                    "version": dep.find(f"{ns}version").text if dep.find(f"{ns}version") is not None else "Unknown"
                }
                metadata["dependencies"].append(dep_info)

        return metadata
    except Exception as e:
        print(f"Error parsing {pom_file}: {e}")
        return None

def process_repositories(directory):
    """Process all cloned repositories to extract metadata"""
    results = []
    
    for repo in os.listdir(directory):
        repo_path = os.path.join(directory, repo)
        pom_file = os.path.join(repo_path, "pom.xml")

        if os.path.exists(pom_file):
            metadata = extract_metadata(pom_file)
            if metadata:
                results.append(metadata)

    return results

# Process repositories and save metadata
metadata_list = process_repositories(PROJECTS_DIR)

json_path = "java_maven_projects.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(metadata_list, f, indent=4)

print(f"Metadata extraction completed! Saved to {json_path}")
