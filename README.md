# Tech Radar Lambda & Storage

This repo contains the lambda function and storage for the tech radar lambda. This code is designed to be deployed to AWS using Terraform and set to run on a cron job, once per day. The code reads the JSON data from the S3 bucket, that is gathered using the Tech Audit Tool, and formats and writes new projects to the CSV file that is accessed by the Tech Radar.

This code links closely to the [Tech Radar](https://github.com/ONS-Innovation/keh-tech-radar), [Tech Audit Tool](https://github.com/ONS-Innovation/keh-tech-audit-tool) and [Tech Audit Tool API](https://github.com/ONS-Innovation/keh-tech-audit-tool-api).

## Prerequisites

- AWS CLI
- Python 3.12
- Docker
- Pip

## Getting Started

Clone the project

```bash
git clone https://github.com/ONS-Innovation/keh-tech-radar-lambda.git
```

Install dependencies

```bash
make install
```

## Running locally with Docker


Build the docker image:

```bash
docker build -t <image_name> .
```

Run the docker image:

```bash
docker run --platform linux/amd64 -p 9000:8080 \
-e SOURCE_BUCKET=<source_bucket> \
-e SOURCE_KEY=<source_key> \
-e DESTINATION_BUCKET=<destination_bucket> \
-e DESTINATION_KEY=<destination_key> \
-e AWS_ACCESS_KEY_ID=<aws_access_key_id> \
-e AWS_SECRET_ACCESS_KEY=<aws_secret_access_key> \
<image_name>
```

Invoke the lambda function:

```bash
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'
```

Example response:

```JSON
{"statusCode": 200, "body": "{\"message\": \"Data processing completed successfully\", \"projects_in_json\": 14, \"existing_projects\": 34, \"new_projects_added\": 0, \"total_projects\": 34}"}
```

## Storing the Container on AWS Elastic Container Registry (ECR)

These instructions assume:

1. You have a repository set up in your AWS account named tech-radar-lambda.
2. You have created an AWS IAM user with permissions to read/write to ECR (e.g AmazonEC2ContainerRegistryFullAccess policy) and that you have created the necessary access keys for this user. The credentials for this user are stored in ~/.aws/credentials and can be used by accessing --profile <aws-credentials-profile>, if these are the only credentials in your file then the profile name is default.

You can find the AWS repo push commands under your repository in ECR by selecting the "View Push Commands" button. This will display a guide to the following (replace <aws-credentials-profile>, <aws-account-id> and <version> accordingly):

Get an authentication token and authenticate your docker client for pushing images to ECR:

```bash
aws ecr --profile <aws-credentials-profile> get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.eu-west-2.amazonaws.com
```

Tag your latest built docker image for ECR (assumes you have run docker build -t sdp-repo-archive . locally first)

```bash
docker tag tech-radar-lambda:latest <aws-account-id>.dkr.ecr.eu-west-2.amazonaws.com/tech-radar-lambda:<version>
```

Note: To find the <version> to build look at the latest tagged version in ECR and increment appropriately

Push the version up to ECR

```bash
docker push <aws-account-id>.dkr.ecr.eu-west-2.amazonaws.com/tech-radar-lambda:<version>
```

## Updating the running service using Terraform

If the application has been modified then the following can be performed to update the running service:

Build a new version of the container image and upload to ECR as per the instructions earlier in this guide.

Change directory to the dashboard terraform

```bash
cd terraform/lambda
```

In the appropriate environment variable file env/sandbox/sandbox.tfvars, env/dev/dev.tfvars or env/prod/prod.tfvars

Change the container_ver variable to the new version of your container.
Initialise terraform for the appropriate environment config file backend-dev.tfbackend or backend-prod.tfbackend run:

```bash
terraform init -backend-config=env/dev/backend-dev.tfbackend -reconfigure
```

The reconfigure options ensures that the backend state is reconfigured to point to the appropriate S3 bucket.

Please Note: This step requires an AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to be loaded into the environment if not already in place. This can be done using:

```bash
export AWS_ACCESS_KEY_ID="<aws_access_key_id>"
export AWS_SECRET_ACCESS_KEY="<aws_secret_access_key>"
```

Refresh the local state to ensure it is in sync with the backend

```bash
terraform refresh -var-file=env/dev/dev.tfvars
```

Plan the changes, ensuring you use the correct environment config (depending upon which env you are configuring):

E.g. for the dev environment run

```bash
terraform plan -var-file=env/dev/dev.tfvars
```

Apply the changes, ensuring you use the correct environment config (depending upon which env you are configuring):

E.g. for the dev environment run

```bash
terraform apply -var-file=env/dev/dev.tfvars
```

When the terraform has applied successfully the running task will have been replaced by a task running the container version you specified in the tfvars file

## Example structure

<details>
  <summary>View Example JSON Structure</summary>

    ```JSON
    {
    'user': [
        {
        'email': 'test@ons.gov.uk',
        'roles': ['Technical Contact', 'Editor'],
        'grade': 'SEO'
        },
        {
        'email': 'test.user@ons.gov.uk',
        'roles': ['Delivery Manager Contact'],
        'grade': 'HEO'
        }
    ],
    'details': [
        {
        'name': 'Forward Program Engineer',
        'short_name': 'FPE',
        'documentation_link': ['https://test.ons.gov.uk'],
        'project_description': 'Operative hybrid instruction set'
        }
    ],
    'developed': ['In-house', []],
    'source_control': [
        {
        'type': 'GitHub',
        'links': [
            {
            'description': 'systematic',
            'url': 'http://test.ons.gov.uk/Documentation'
            }
        ]
        }
    ],
    'architecture': {
        'hosting': {
        'type': ['Hybrid'],
        'details': ['AWS', 'Local']
        },
        'database': {
        'main': [],
        'others': ['DocumentDB']
        },
        'languages': {
        'main': ['Python'],
        'others': ['JavaScript', 'Java']
        },
        'frameworks': {
        'main': [],
        'others': ['Flask']
        },
        'cicd': {
        'main': [],
        'others': ['Github Actions']
        },
        'infrastructure': {
        'main': [],
        'others': ['Jenkins']
        }
    },
    'stage': 'Development'
    }
    ```

</details>

<details>
  <summary>View Example CSV Structure</summary>

    | Field | Value |
    | --- | --- |
    | Project | Test Project |
    | Project_Short | SDX |
    | Project_Area |  |
    | DST_Area |  |
    | Team |  |
    | Language_Main | Python |
    | Language_Others | VB6 |
    | Language_Frameworks |  |
    | Testing_Frameworks |  |
    | Hosted | GCP |
    | Messaging_Type | PubSub |
    | Containers |  |
    | Architectures |  |
    | Source_Control | GitLab |
    | Branching_Strategy |  |
    | Repo |  |
    | Static_Analysis |  |
    | Code_Formatter |  |
    | Package_Manager |  |
    | Security_Tools |  |
    | CICD | Concourse |
    | CICD_Orchestration | Kubernetes |
    | Monitoring | GCP Stackdriver |
    | Datastores |  |
    | Database_Technologies |  |
    | Data_Output_Formats | pck |
    | Business_Dashboards |  |
    | Integrations_ONS |  |
    | Integrations_External |  |
    | IAM_Services |  |
    | Cloud_Services | GCP Cloud Datastore |
    | Datasets_Used |  |
    | Project_Tools |  |
    | Other_Tools |  |
    | Documentation |  |
</details>

## Linting and Formatting

To view all commands

```bash
make all
```

Linting tools must first be installed before they can be used

```bash
make install-dev
```

To clean residue files

```bash
make clean
```

To format your code

```bash
make format
```

To run all linting tools

```bash
make lint
```

To run a specific linter (black, ruff, pylint)

```bash
make black
make ruff
make pylint
```

To run mypy (static type checking)

```bash
make mypy
```

To run the application locally

```bash
make run-local
```
