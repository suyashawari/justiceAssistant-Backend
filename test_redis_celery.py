import os
import time
from dotenv import load_dotenv
import redis
from celery import Celery
from celery.exceptions import TimeoutError

# --- Configuration ---
# This default URL is used for the basic test.
# The project-specific test will load the URL from your .env file.
DEFAULT_REDIS_URL = "redis://localhost:6379/0"

def print_header(title):
    """Prints a formatted header."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def test_basic_redis_connection():
    """
    Test 1: A raw connection to Redis.
    This bypasses all project code and just checks if Redis is running.
    """
    print_header("Test 1: Basic Redis Server Connection")
    try:
        print(f"Attempting to connect to Redis at: {DEFAULT_REDIS_URL}...")
        r = redis.Redis.from_url(DEFAULT_REDIS_URL)
        if r.ping():
            print("✅ SUCCESS: Successfully connected to Redis and received a PONG response.")
            return True
        else:
            print("❌ FAILURE: Connected to Redis, but the PING command failed.")
            return False
    except redis.exceptions.ConnectionError as e:
        print(f"❌ FAILURE: Could not connect to the Redis server.")
        print("   Error Details:", e)
        print("\n   TROUBLESHOOTING:")
        print("   - Is the Redis server running? You can start it with the `redis-server` command.")
        print("   - Is Redis running on a different host or port? If so, update DEFAULT_REDIS_URL in this script.")
        return False

def test_project_celery_setup():
    """
    Test 2: Connect to Redis using the project's Celery configuration.
    This checks if your .env file is set up correctly for Celery.
    """
    print_header("Test 2: Project's Celery-to-Redis Connection")
    print("Loading environment variables from .env file...")
    load_dotenv()

    broker_url = os.environ.get("CELERY_BROKER_URL")
    if not broker_url:
        print("❌ FAILURE: The `CELERY_BROKER_URL` was not found in your environment or .env file.")
        print("\n   TROUBLESHOOTING:")
        print("   - Make sure you have a .env file in the same directory as this script.")
        print("   - Ensure the .env file contains a line like: CELERY_BROKER_URL=redis://localhost:6379/0")
        return None

    print(f"Found project's broker URL: {broker_url}")
    print("Initializing a Celery app with this configuration...")

    try:
        celery_app = Celery("diagnostic_app", broker=broker_url, backend=broker_url)
        # The 'with' statement ensures the connection is properly closed.
        with celery_app.connection() as connection:
            connection.ensure_connection(max_retries=1)
        print("✅ SUCCESS: Celery was able to establish a connection with Redis using your project's configuration.")
        return celery_app
    except Exception as e:
        print(f"❌ FAILURE: Celery could not connect to Redis using the project's URL.")
        print("   Error Details:", e)
        print("\n   TROUBLESHOOTING:")
        print("   - Does the URL in your .env file point to the correct Redis server?")
        print("   - If your Redis server has a password, is it included in the URL? (e.g., redis://:password@host:port/0)")
        return None

def test_task_execution(celery_app):
    """
    Test 3: Send a simple task and wait for the result.
    This confirms that a Celery worker is running and processing tasks from the queue.
    """
    print_header("Test 3: End-to-End Task Execution")

    # Define a simple task for testing purposes
    @celery_app.task(name="diagnostic_add_task")
    def add(x, y):
        return x + y

    try:
        test_data = (5, 10)
        print(f"Sending a test task `add{test_data}` to the queue...")
        result = add.delay(*test_data)
        print(f"Task sent with ID: {result.id}. Waiting for a worker to execute it (10s timeout)...")
        
        # Wait for the result from the worker
        task_result_value = result.get(timeout=10)
        
        expected_result = sum(test_data)
        if task_result_value == expected_result:
            print(f"✅ SUCCESS: A worker picked up the task and returned the correct result: {task_result_value}")
        else:
            print(f"❌ FAILURE: A worker returned a result, but it was incorrect.")
            print(f"   - Expected: {expected_result}, Got: {task_result_value}")

    except TimeoutError:
        print("❌ FAILURE: The task was sent, but we never received a result.")
        print("\n   TROUBLESHOOTING:")
        print("   - This almost always means a Celery worker is NOT RUNNING.")
        print("   - Open a new terminal, activate the virtual environment, and run the worker with:")
        print("     celery -A run:celery worker --loglevel=info")
    except Exception as e:
        print("❌ FAILURE: An unexpected error occurred while sending or retrieving the task.")
        print("   Error Details:", e)


if __name__ == "__main__":
    print("="*60)
    print("  JusticeAssist Redis & Celery Diagnostic Tool")
    print("="*60)
    
    if test_basic_redis_connection():
        celery_app_instance = test_project_celery_setup()
        if celery_app_instance:
            test_task_execution(celery_app_instance)

    print("\n" + "="*60)
    print("  Diagnostic complete.")
    print("="*60)