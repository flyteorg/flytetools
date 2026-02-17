#!/usr/bin/env python3
"""
Serverless-compatible entrypoint for Flyte Databricks tasks.

This entrypoint is designed to work with Databricks Serverless Compute,
which has restrictions on accessing certain directories like /root and
does not provide standard AWS credentials via instance metadata.

Key features:
- Uses /tmp as the working directory (accessible in serverless)
- Configures AWS credentials from Databricks service credentials
- Works with flytekitplugins-spark which has native serverless support

Credential Provider Configuration (in order of precedence):
    1. Command-line argument: --flyte-credential-provider=<name>
    2. Environment variable: DATABRICKS_SERVICE_CREDENTIAL_PROVIDER
    3. Default fallback (if configured in DEFAULT_CREDENTIAL_PROVIDER below)

Optional Environment Variables:
    AWS_DEFAULT_REGION: AWS region (defaults to 'us-east-1')
    FLYTE_INTERNAL_WORK_DIR: Working directory (defaults to '/tmp/flyte')
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


# =============================================================================
# CONFIGURATION: Set your default credential provider here (optional)
# =============================================================================
# If environment variables and command-line arguments don't work in your 
# Databricks serverless setup, you can hardcode the credential provider name 
# here as a fallback. Set to None to disable the fallback.

DEFAULT_CREDENTIAL_PROVIDER = None  # e.g., "my-credential-provider-name"

# =============================================================================


def parse_credential_provider_from_args():
    """
    Parse the credential provider from command-line arguments.
    
    Looks for --flyte-credential-provider=<name> anywhere in sys.argv
    and removes it from the args list.
    
    Returns:
        tuple: (credential_provider, remaining_args)
    """
    credential_provider = None
    remaining_args = []
    
    for arg in sys.argv[1:]:
        if arg.startswith("--flyte-credential-provider="):
            credential_provider = arg.split("=", 1)[1]
        else:
            remaining_args.append(arg)
    
    return credential_provider, remaining_args


def setup_aws_credentials_from_databricks(credential_provider: str = None):
    """
    Configure AWS credentials from Databricks service credentials.
    
    In Databricks serverless, standard AWS credential mechanisms (instance metadata,
    environment variables) are not available. Instead, credentials must be obtained
    via dbutils.credentials.getServiceCredentialsProvider().
    
    Args:
        credential_provider: Optional credential provider name (overrides env var)
    
    Returns:
        bool: True if credentials were configured, False otherwise
    """
    # Try to get credential provider from multiple sources (in order of precedence)
    if not credential_provider:
        credential_provider = os.environ.get("DATABRICKS_SERVICE_CREDENTIAL_PROVIDER")
    
    if not credential_provider:
        if DEFAULT_CREDENTIAL_PROVIDER:
            print(f"[Flyte] Using fallback credential provider: {DEFAULT_CREDENTIAL_PROVIDER}")
            credential_provider = DEFAULT_CREDENTIAL_PROVIDER
        else:
            print("[Flyte] WARNING: No credential provider configured")
            print("[Flyte] S3 access may fail. Options to fix:")
            print("[Flyte]   1. Pass --flyte-credential-provider=<name> as command argument")
            print("[Flyte]   2. Set DATABRICKS_SERVICE_CREDENTIAL_PROVIDER env var")
            print("[Flyte]   3. Use databricks_service_credential_provider in DatabricksV2 config")
            return False
    
    print(f"[Flyte] Configuring AWS credentials from: {credential_provider}")
    
    try:
        # Import dbutils - only available in Databricks runtime
        from pyspark.dbutils import DBUtils
        from pyspark.sql import SparkSession
        
        # Get SparkSession (pre-configured in serverless)
        spark = SparkSession.builder.getOrCreate()
        dbutils = DBUtils(spark)
        
        # Get the botocore session from Databricks service credentials
        print("[Flyte] Calling dbutils.credentials.getServiceCredentialsProvider()...")
        botocore_session = dbutils.credentials.getServiceCredentialsProvider(credential_provider)
        
        # Create a boto3 session with this botocore session
        import boto3
        region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        session = boto3.Session(botocore_session=botocore_session, region_name=region)
        
        # Get credentials from the session
        credentials = session.get_credentials()
        if credentials is None:
            print("[Flyte] ERROR: No credentials returned from service credential provider")
            return False
        
        # Get frozen credentials (thread-safe snapshot)
        frozen_credentials = credentials.get_frozen_credentials()
        
        # Set environment variables for AWS SDK / s3fs / flytekit
        os.environ["AWS_ACCESS_KEY_ID"] = frozen_credentials.access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = frozen_credentials.secret_key
        
        if frozen_credentials.token:
            os.environ["AWS_SESSION_TOKEN"] = frozen_credentials.token
        
        if region:
            os.environ["AWS_DEFAULT_REGION"] = region
        
        # Verify credentials are working
        try:
            sts_client = session.client("sts")
            identity = sts_client.get_caller_identity()
            print(f"[Flyte] ✓ AWS credentials configured successfully")
            print(f"[Flyte]   Account: {identity.get('Account', 'unknown')}")
            print(f"[Flyte]   ARN: {identity.get('Arn', 'unknown')}")
        except Exception as e:
            print(f"[Flyte] WARNING: Could not verify AWS credentials: {e}")
        
        return True
        
    except ImportError as e:
        print(f"[Flyte] WARNING: Required modules not available: {e}")
        print("[Flyte] This entrypoint must run in Databricks serverless environment")
        return False
    except Exception as e:
        print(f"[Flyte] ERROR: Failed to configure AWS credentials: {e}")
        import traceback
        traceback.print_exc()
        return False


def setup_spark_session():
    """
    Pre-initialize SparkSession and store it for Flyte tasks.
    
    IMPORTANT: In Databricks serverless python_file tasks, the 'spark' variable
    is NOT automatically injected like it is in notebooks.
    
    We store the SparkSession in TWO places to survive module reloads:
    1. A custom module '_flyte_spark_session' in sys.modules (most reliable)
    2. builtins.spark (backup)
    
    The custom module approach survives even if other code deletes pyspark
    from sys.modules or manipulates builtins.
    """
    import builtins
    import sys
    import types
    
    # Check if we already have a spark session stored
    if '_flyte_spark_session' in sys.modules:
        spark_module = sys.modules['_flyte_spark_session']
        if hasattr(spark_module, 'spark') and spark_module.spark is not None:
            print(f"[Flyte] SparkSession already stored: {spark_module.spark}")
            return spark_module.spark
    
    if hasattr(builtins, 'spark') and builtins.spark is not None:
        print(f"[Flyte] SparkSession already in builtins: {builtins.spark}")
        return builtins.spark
    
    spark_remote = os.environ.get("SPARK_REMOTE")
    if spark_remote:
        print(f"[Flyte] SPARK_REMOTE: {spark_remote}")
    
    # CRITICAL: Prioritize Databricks' native Python path FIRST
    # This ensures we use Databricks' PySpark, not pip-installed version
    db_paths = [
        "/databricks/python/lib/python3.12/site-packages",
        "/databricks/python/lib/python3.11/site-packages", 
        "/databricks/python/lib/python3.10/site-packages",
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            if db_path in sys.path:
                sys.path.remove(db_path)
            sys.path.insert(0, db_path)
            print(f"[Flyte] Prioritized Databricks Python path: {db_path}")
            break
    
    spark = None
    
    # Method 1: Use SparkSession.builder.getOrCreate() (standard approach)
    try:
        from pyspark.sql import SparkSession
        print("[Flyte] Creating SparkSession via SparkSession.builder.getOrCreate()...")
        spark = SparkSession.builder.getOrCreate()
        print(f"[Flyte] ✓ SparkSession created: {spark}")
    except Exception as e:
        print(f"[Flyte] SparkSession.builder.getOrCreate() failed: {e}")
    
    # Method 2: Try to get an active session
    if spark is None:
        try:
            from pyspark.sql import SparkSession
            spark = SparkSession.getActiveSession()
            if spark:
                print(f"[Flyte] Got active SparkSession: {spark}")
        except Exception as e:
            print(f"[Flyte] Could not get active session: {e}")
    
    if spark is not None:
        # Store in a custom module (survives module reloads)
        spark_module = types.ModuleType('_flyte_spark_session')
        spark_module.spark = spark
        sys.modules['_flyte_spark_session'] = spark_module
        print("[Flyte] ✓ SparkSession stored in _flyte_spark_session module")
        
        # Also store in builtins as backup
        builtins.spark = spark
        print("[Flyte] ✓ SparkSession injected into builtins")
        
        return spark
    
    print("[Flyte] WARNING: Could not initialize SparkSession")
    return None


def setup_environment():
    """Set up the working environment for serverless compute."""
    # Mark this as Databricks serverless for plugin compatibility
    # The flytekitplugins-spark plugin checks these env vars
    os.environ["DATABRICKS_SERVERLESS"] = "true"
    os.environ["SPARK_CONNECT_MODE"] = "true"
    
    # Use /tmp for serverless - it's always writable
    # Unlike /root which is not accessible in serverless
    work_dir = os.environ.get("FLYTE_INTERNAL_WORK_DIR", "/tmp/flyte")
    
    try:
        Path(work_dir).mkdir(parents=True, exist_ok=True)
        os.chdir(work_dir)
        print(f"[Flyte] Working directory: {work_dir}")
    except Exception as e:
        # Fallback to temp directory if even /tmp/flyte fails
        work_dir = tempfile.mkdtemp(prefix="flyte_")
        os.chdir(work_dir)
        print(f"[Flyte] Fallback working directory: {work_dir}")
    
    return work_dir


def download_and_extract_distribution(additional_distribution: str, dest_dir: str):
    """Download and extract the tarball from S3."""
    import tarfile
    import tempfile
    import fsspec
    
    os.makedirs(dest_dir, exist_ok=True)
    
    with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        fs = fsspec.filesystem('s3')
        s3_path = additional_distribution.replace('s3://', '')
        print(f"[Flyte] Downloading: {s3_path}")
        fs.get(s3_path, tmp_path)
        print(f"[Flyte] Downloaded to: {tmp_path}")
        
        with tarfile.open(tmp_path, 'r:gz') as tar:
            tar.extractall(path=dest_dir)
        print(f"[Flyte] Extracted to: {dest_dir}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def execute_flyte_task_directly(args: list):
    """
    Execute Flyte task directly to preserve SparkSession.
    
    This is the key to making Spark work in Databricks serverless with Flyte.
    fast_execute_task_cmd clears Python state, losing the SparkSession.
    By downloading the tarball and importing the module ourselves, we preserve
    the SparkSession that was created by setup_spark_session().
    """
    import importlib
    
    # Parse args: --additional-distribution <url> --dest-dir <dir> -- pyflyte-execute ...
    additional_distribution = None
    dest_dir = "."
    execute_args = []
    
    i = 0
    while i < len(args):
        if args[i] == "--additional-distribution" and i + 1 < len(args):
            additional_distribution = args[i + 1]
            i += 2
        elif args[i] == "--dest-dir" and i + 1 < len(args):
            dest_dir = args[i + 1]
            i += 2
        elif args[i] == "--":
            execute_args = args[i + 1:]
            break
        else:
            i += 1
    
    # Extract task info for logging
    task_module = None
    for j, arg in enumerate(execute_args):
        if arg == "task-module" and j + 1 < len(execute_args):
            task_module = execute_args[j + 1]
            break
    
    print(f"[Flyte] Executing task: {task_module}")
    
    # Download and extract tarball
    if additional_distribution:
        download_and_extract_distribution(additional_distribution, dest_dir)
    
    # Add to sys.path
    abs_dest = os.path.abspath(dest_dir)
    if abs_dest not in sys.path:
        sys.path.insert(0, abs_dest)
    
    # Import task module in our context (preserves SparkSession)
    if task_module:
        importlib.import_module(task_module)
    
    # Execute via flytekit (handles inputs/outputs)
    from flytekit.bin.entrypoint import execute_task_cmd
    exec_args = execute_args[1:] if execute_args and execute_args[0] == "pyflyte-execute" else execute_args
    
    execute_task_cmd.main(exec_args, standalone_mode=False)
    return 0


def execute_flyte_command_inprocess(args: list):
    """
    Execute the Flyte command IN-PROCESS to preserve SparkSession.
    
    IMPORTANT: We use direct task execution instead of fast_execute_task_cmd
    because fast_execute_task_cmd clears Python state when loading the task module,
    which loses the SparkSession created by this entrypoint.
    """
    if not args:
        print("[Flyte] ERROR: No command provided", file=sys.stderr)
        return 1
    
    cmd = args[0] if args else ""
    
    try:
        if cmd == "pyflyte-fast-execute":
            # Use DIRECT execution to preserve SparkSession
            return execute_flyte_task_directly(args[1:])
            
        elif cmd == "pyflyte-execute":
            from flytekit.bin.entrypoint import execute_task_cmd
            return execute_task_cmd.main(args[1:], standalone_mode=False) or 0
            
        else:
            print(f"[Flyte] Unknown command '{cmd}', using subprocess")
            result = subprocess.run(args, check=False, env=os.environ.copy())
            return result.returncode
            
    except SystemExit as e:
        return e.code if e.code is not None else 0
    except Exception as e:
        print(f"[Flyte] ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def is_running_in_ipython():
    """Check if we're running inside IPython/Jupyter/Databricks notebook."""
    try:
        get_ipython()  # noqa: F821
        return True
    except NameError:
        return False


def main():
    """Main entrypoint for Flyte serverless tasks."""
    print("[Flyte] Serverless Entrypoint")
    print(f"[Flyte] Python: {sys.version.split()[0]}")
    print(f"[Flyte] Raw args: {sys.argv[1:]}")
    
    # Parse credential provider from command-line arguments
    credential_provider, remaining_args = parse_credential_provider_from_args()
    print(f"[Flyte] Executing: {' '.join(remaining_args[:3])}..." if len(remaining_args) > 3 else f"[Flyte] Executing: {' '.join(remaining_args)}")
    
    # Configure AWS credentials from Databricks service credentials
    # This must happen BEFORE any S3 access attempts
    if not setup_aws_credentials_from_databricks(credential_provider):
        print("[Flyte] WARNING: S3 operations may fail without credentials")
    
    # Set up working environment
    setup_environment()
    
    # Pre-initialize SparkSession and inject into builtins
    # This is critical - the SparkSession must be created HERE (before fast_execute)
    # because Databricks' pyspark handles unix:// URLs correctly only on first import
    spark = setup_spark_session()
    if not spark:
        print("[Flyte] ERROR: Failed to create SparkSession - cannot proceed")
        sys.exit(1)
    
    # Execute the Flyte command (uses direct execution to preserve SparkSession)
    return_code = execute_flyte_command_inprocess(remaining_args)
    
    print(f"[Flyte] Task completed with return code: {return_code}")
    
    # Handle IPython context (Databricks notebook)
    if is_running_in_ipython():
        if return_code != 0:
            raise RuntimeError(f"Flyte task failed with return code: {return_code}")
        return return_code
    else:
        sys.exit(return_code)


if __name__ == "__main__":
    main()
