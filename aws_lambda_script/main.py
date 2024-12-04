import json
import csv
import os
from typing import Dict, List
import logging
from io import StringIO
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
SOURCE_BUCKET = os.environ.get("SOURCE_BUCKET", "sdp-dev-tech-audit-tool-api")
SOURCE_KEY = os.environ.get("SOURCE_KEY", "new_project_data.json")
DESTINATION_BUCKET = os.environ.get("DESTINATION_BUCKET", "sdp-dev-tech-radar")
DESTINATION_KEY = os.environ.get("DESTINATION_KEY", "onsTechDataAdoption.csv")


def get_json_from_s3(bucket: str, key: str) -> Dict:
    """Retrieve JSON data from S3 bucket"""
    try:
        s3_client = boto3.client("s3")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        json_data = json.loads(response["Body"].read().decode("utf-8"))
        return json_data
    except Exception as e:
        logger.error("Error retrieving JSON from S3: %s", str(e))
        raise


def process_project_data(project_data: Dict) -> List[Dict]:
    """Process project data into the required format"""
    processed_data = []

    projects = project_data.get("projects", [])
    logger.info("Processing %d projects from JSON data", len(projects))

    for project in projects:
        row = {
            "Project": project.get("details", [{}])[0].get("name", ""),
            "Project_Short": project.get("details", [{}])[0].get("short_name", ""),
            "Project_Area": "",
            "DST_Area": "",
            "Team": "",
            "Language_Main": ";".join(
                project.get("architecture", {}).get("languages", {}).get("main", [])
            ),
            "Language_Others": ";".join(
                project.get("architecture", {}).get("languages", {}).get("others", [])
            ),
            "Language_Frameworks": ";".join(
                project.get("architecture", {}).get("frameworks", {}).get("others", [])
            ),
            "Testing_Frameworks": "",
            "Hosted": ";".join(
                project.get("architecture", {}).get("hosting", {}).get("details", [])
            ),
            "Messaging_Type": "",
            "Containers": "",
            "Architectures": "",
            "Source_Control": project.get("source_control", [{}])[0].get("type", ""),
            "Branching_Strategy": "",
            "Repo": project.get("source_control", [{}])[0]
            .get("links", [{}])[0]
            .get("url", ""),
            "Static_Analysis": "",
            "Code_Formatter": "",
            "Package_Manager": "",
            "Security_Tools": "",
            "CICD": ";".join(
                project.get("architecture", {}).get("cicd", {}).get("others", [])
            ),
            "CICD_Orchestration": "",
            "Monitoring": "",
            "Datastores": ";".join(
                project.get("architecture", {}).get("database", {}).get("others", [])
            ),
        }
        processed_data.append(row)

    logger.info("Processed %d projects", len(processed_data))
    return processed_data


def write_to_s3_csv(data: List[Dict], bucket: str, key: str):
    """Write processed data to S3 as CSV"""
    try:
        s3_client = boto3.client("s3")

        if not data:
            logger.warning("No data to write to CSV")
            return

        csv_buffer = StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        # Upload to S3
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=csv_buffer.getvalue().encode("utf-8"),
            ContentType="text/csv",
        )
        logger.info("Successfully wrote CSV to %s/%s", bucket, key)
    except Exception as e:
        logger.error("Error writing CSV to S3: %s", str(e))
        raise


def get_existing_csv_data(bucket: str, key: str) -> List[Dict]:
    """Retrieve existing CSV data from S3 bucket"""
    try:
        s3_client = boto3.client("s3")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        csv_content = response["Body"].read().decode("utf-8")

        csv_buffer = StringIO(csv_content)
        reader = csv.DictReader(csv_buffer)
        return list(reader)
    except s3_client.exceptions.NoSuchKey:
        logger.info("No existing CSV found at %s/%s", bucket, key)
        return []
    except Exception as e:
        logger.error("Error retrieving CSV from S3: %s", str(e))
        raise


def merge_project_data(new_data: List[Dict], existing_data: List[Dict]) -> List[Dict]:
    """Merge new project data with existing CSV data"""
    logger.info("Found %d existing projects in CSV", len(existing_data))
    logger.info("Found %d projects in new data", len(new_data))

    existing_projects = {project["Project"]: project for project in existing_data}

    merged_data = existing_data.copy()
    new_projects_added = 0

    for new_project in new_data:
        if new_project["Project"] not in existing_projects:
            logger.info("Adding new project: %s", new_project["Project"])
            merged_data.append(new_project)
            new_projects_added += 1

    logger.info("Added %d new projects", new_projects_added)
    logger.info("Total projects after merge: %d", len(merged_data))
    return merged_data


def lambda_handler(event, context):
    """Main Lambda handler function"""
    try:
        if not DESTINATION_BUCKET:
            raise ValueError("DESTINATION_BUCKET environment variable is required")

        logger.info("Reading from %s/%s", SOURCE_BUCKET, SOURCE_KEY)
        logger.info("Writing to %s/%s", DESTINATION_BUCKET, DESTINATION_KEY)

        project_data = get_json_from_s3(SOURCE_BUCKET, SOURCE_KEY)
        logger.info("Successfully retrieved JSON data")

        new_processed_data = process_project_data(project_data)

        existing_data = get_existing_csv_data(DESTINATION_BUCKET, DESTINATION_KEY)

        merged_data = merge_project_data(new_processed_data, existing_data)

        write_to_s3_csv(merged_data, DESTINATION_BUCKET, DESTINATION_KEY)

        result = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Data processing completed successfully",
                    "projects_in_json": len(new_processed_data),
                    "existing_projects": len(existing_data),
                    "new_projects_added": len(merged_data) - len(existing_data),
                    "total_projects": len(merged_data),
                }
            ),
        }
        logger.info("Lambda execution result: %s", result)
        return result

    except Exception as e:
        logger.error("Lambda execution failed: %s", str(e))
        raise
