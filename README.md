
## Setting up & Running Locally

Clone the project

```bash
git clone https://github.com/ONS-Innovation/keh-tech-radar-lambda.git
```

Install dependencies

```bash
make install
```

Install dev dependencies to run linting tools

```bash
make install-dev
```

Set environment variables:

```bash
export SOURCE_BUCKET=<source_bucket>
export SOURCE_KEY=<source_key>
export DESTINATION_BUCKET=<destination_bucket>
export DESTINATION_KEY=<destination_key>
```
