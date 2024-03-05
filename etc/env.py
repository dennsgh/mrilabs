import os
import subprocess
import sys

# Create .env file if it does not exist
open(".env", "a").close()
print(f"Setting up environment with OS type: {os.name}")

# Determine the operating system type
ostype = sys.platform
script_path = os.path.abspath(__file__)

if ostype.startswith("linux") or ostype == "msys" or ostype == "cygwin":
    config = os.path.dirname(script_path)
    working_dir = os.path.dirname(config)
elif ostype == "darwin":
    working_dir = os.path.dirname(script_path)
    config = os.path.join(working_dir, "etc")
else:
    # This else block is not directly from your script but assumes a default behavior
    working_dir = os.path.dirname(script_path)
    config = os.path.join(working_dir, "etc")

data = os.path.join(working_dir, "data")
logs = os.path.join(working_dir, "logs")
assets = os.path.join(working_dir, "assets")

src = os.path.join(working_dir, "src")

if (
    ostype.startswith("linux")
    or ostype == "darwin"
    or ostype == "cygwin"
    or ostype == "msys"
):
    pythonpath = f"{src}"
else:
    pythonpath = f"{os.getenv('PYTHONPATH', '')}:{src}"

# Set environment variables
os.environ["WORKINGDIR"] = working_dir
os.environ["CONFIG"] = config
os.environ["DATA"] = data
os.environ["LOGS"] = logs
os.environ["ASSETS"] = assets
os.environ["SRC"] = src
os.environ["PYTHONPATH"] = pythonpath

# Corrected invocation of dotenv with subprocess.run
env_vars = ["WORKINGDIR", "ASSETS", "CONFIG", "LOGS", "DATA", "PYTHONPATH"]
for var in env_vars:
    subprocess.run(
        [
            "python",
            "-m",
            "dotenv",
            "-f",
            f".env",
            "set",
            var,
            os.getenv(var),
        ],
        check=True,  # Optionally, add this to raise an exception if the command fails
    )
