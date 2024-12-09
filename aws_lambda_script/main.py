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
SOURCE_BUCKET = os.environ.get("SOURCE_BUCKET")
SOURCE_KEY = os.environ.get("SOURCE_KEY")
DESTINATION_BUCKET = os.environ.get("DESTINATION_BUCKET")
DESTINATION_KEY = os.environ.get("DESTINATION_KEY")

# Set global s3 client
client = boto3.client("s3")

def get_data_from_s3(bucket: str, key: str) -> Dict:
    """
    Retrieves data from an S3 bucket and returns it as a dictionary.

    Args:
        bucket (str): The S3 bucket to retrieve the data from.
        key (str): The S3 key to retrieve the data from.

    Returns:
        Dict: The data from the S3 bucket as a dictionary.
    """
    try:
        response = client.get_object(Bucket=bucket, Key=key)
        return response
    except client.exceptions.NoSuchKey:
        logger.info("No existing CSV found at %s/%s", bucket, key)
        return []
    except Exception as e:
        logger.error("Error retrieving CSV from S3: %s", str(e))
        raise


def get_json_from_s3(bucket: str, key: str) -> Dict:
    """
    Retrieves JSON data from an S3 bucket and returns it as a dictionary.

    Args:
        bucket (str): The S3 bucket to retrieve the JSON from.
        key (str): The S3 key to retrieve the JSON from.

    Returns:
        Dict: The JSON data as a dictionary.
    """
    response = get_data_from_s3(bucket, key)
    json_data = json.loads(response["Body"].read().decode("utf-8"))
    return json_data


def process_project_data(project_data: Dict) -> List[Dict]:
    """
    Processes the project data into the required format.

    Args:
        project_data (Dict): The project data to process.

    Returns:
        List[Dict]: The processed data as a list of dictionaries.
    """
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
    """
    Writes processed data to S3 as CSV.

    Args:
        data (List[Dict]): The processed data to write to CSV.
        bucket (str): The S3 bucket to write the CSV to.
        key (str): The S3 key to write the CSV to.

    Returns:
        None
    """
    try:
        if not data:
            logger.warning("No data to write to CSV")
            return

        csv_buffer = StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        # Upload to S3
        client.put_object(
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
    """
    Retrieves existing CSV data from an S3 bucket and returns it as a list of dictionaries.

    Args:
        bucket (str): The S3 bucket to retrieve the CSV from.
        key (str): The S3 key to retrieve the CSV from.

    Returns:
        List[Dict]: The existing CSV data as a list of dictionaries.
    """
    response = get_data_from_s3(bucket, key)
    csv_content = response["Body"].read().decode("utf-8")

    csv_buffer = StringIO(csv_content)
    reader = csv.DictReader(csv_buffer)
    return list(reader)


def merge_project_data(new_data: List[Dict], existing_data: List[Dict]) -> List[Dict]:
    """
    Merges new project data with existing CSV data.

    Args:
        new_data (List[Dict]): The new project data to merge.
        existing_data (List[Dict]): The existing CSV data to merge with.

    Returns:
        List[Dict]: The merged data as a list of dictionaries.
    """
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
    """
    Main Lambda handler function.

    Args:
        event (Dict): The event data.
        context (Dict): The context data.

    Returns:
        Dict: The result of the Lambda execution.
    """
    try:
        if not DESTINATION_BUCKET:
            raise ValueError("DESTINATION_BUCKET environment variable is required")
        if not SOURCE_BUCKET:
            raise ValueError("SOURCE_BUCKET environment variable is required")
        if not SOURCE_KEY:
            raise ValueError("SOURCE_KEY environment variable is required")
        if not DESTINATION_KEY:
            raise ValueError("DESTINATION_KEY environment variable is required")

        logger.info("Reading from %s/%s", SOURCE_BUCKET, SOURCE_KEY)
        logger.info("Writing to %s/%s", DESTINATION_BUCKET, DESTINATION_KEY)

        project_data = get_json_from_s3(SOURCE_BUCKET, SOURCE_KEY)
        projects = []
        for project in project_data['projects']:
            projects.append(project['details'][0]['name'])
        logger.info("(JSON) Project names: %s", "; ".join(projects))

        new_processed_data = process_project_data(project_data)

        existing_data = get_existing_csv_data(DESTINATION_BUCKET, DESTINATION_KEY)

        merged_data = merge_project_data(new_processed_data, existing_data)

        projects = []
        for project in merged_data:
            projects.append(project['Project'])
        logger.info("(CSV) Merged data names: %s", "; ".join(projects))

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