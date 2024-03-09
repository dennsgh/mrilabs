from pathlib import Path

# Locate the root directory (assuming the script is in root/etc)
script_path = Path(__file__).resolve()
root_dir = script_path.parent.parent  # Move up twice to get to root

# Define directories
workdir = root_dir
src_dir = root_dir / "src"
data_dir = root_dir / "data"
assets_dir = src_dir / "assets"

# Environment variables as key-value pairs
env_vars = {
    "WORKINGDIR": str(workdir),
    "PYTHONPATH": str(src_dir),
    "ASSETS": str(assets_dir),
    "DATA": str(data_dir),
}
print("Environment variables:")
print("|=====================================|")
for key, value in env_vars.items():
    print(f"|  {key}={value}")
print("|=====================================|")

# Write environment variables to .env file
env_file_path = root_dir / ".env"
with env_file_path.open("w") as env_file:
    for key, value in env_vars.items():
        env_file.write(f"{key}={value}\n")

print("Environment setup completed.")
