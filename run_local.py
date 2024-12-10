import logging
import time
from main import lambda_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S.%fZ",
)

logger = logging.getLogger()


def run_local():
    """Run the lambda function locally

    Args:
        None

    Returns:
        dict: The result of the lambda function
    """

    # Simulate Lambda environment
    start_time = time.time()
    request_id = "local-test-request"

    print(f"START RequestId: {request_id} Version: $LATEST")

    try:
        # Create event and context objects
        event = {}
        context = type(
            "LambdaContext",
            (),
            {
                "function_name": "tech-radar-lambda",
                "function_version": "$LATEST",
                "invoked_function_arn": (
                    "arn:aws:lambda:local:000000000000:function:tech-radar-lambda"
                ),
                "memory_limit_in_mb": 128,
                "aws_request_id": request_id,
                "log_group_name": "/aws/lambda/tech-radar-lambda",
                "log_stream_name": f"local-test-{int(time.time())}",
            },
        )()

        # Run the handler
        result = lambda_handler(event, context)
        print(f"END RequestId: {request_id}")

        # Calculate duration
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        print(
            f"REPORT RequestId: {request_id}\tDuration: {duration:.2f} ms\t"
            f"Billed Duration: {int(duration)} ms\tMemory Size: 128 MB\tMax Memory Used: N/A"
        )

        return result

    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"END RequestId: {request_id}")
        raise


if __name__ == "__main__":
    run_local()
