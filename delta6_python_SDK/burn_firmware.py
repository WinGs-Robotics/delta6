import subprocess
import os
import argparse

def burn_firmware(port, environment="nano_every"):
    # Save the current working directory
    original_cwd = os.getcwd()

    try:
        # Change to firmware directory
        firmware_dir = os.path.join(original_cwd, "..", "firmware")
        os.chdir(firmware_dir)

        # Build the PlatformIO command
        cmd = [
            "pio", "run",
            "-e", environment,
            "--target", "upload",
            "--upload-port", port
        ]
        print(f"Running: {' '.join(cmd)}")

        # Execute
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("✅ Upload successful!")

    except subprocess.CalledProcessError as e:
        print("❌ Upload failed:")
        print(e.stdout)
        print(e.stderr)

    finally:
        # Always change back to the original directory
        os.chdir(original_cwd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Burn firmware to the Nano Every board.")
    parser.add_argument("--port", type=str, required=True, help="Port to upload to")
    parser.add_argument("--env", type=str, default="nano_every", help="PlatformIO environment name (default: nano_every)")
    args = parser.parse_args()

    burn_firmware(args.port, args.env)
