import os
import subprocess
import sys
import time


def ensure_pip():
    try:
        import pip
        print("✅ pip is already installed.")
    except ImportError:
        print("⚠️ pip not found. Installing with ensurepip...")
        subprocess.check_call([sys.executable, "-m", "ensurepip"])
        print("✅ pip installed successfully.")


def check_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def install_requirements_in_directory(base_dir):
    # Walk through all folders looking for requirements.txt files
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file == "requirements.txt":
                req_path = os.path.join(root, file)
                print(f"\n:rocket: Installing dependencies from: {req_path}")
                print(f":package: Running: {sys.executable} -m pip install -r {req_path}")

                # Run and show ALL output in real time
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", req_path]
                )

                if result.returncode == 0:
                    print(f":white_check_mark: Successfully installed from {req_path}")
                else:
                    print(f":x: Error installing from {req_path}")
                    sys.exit(1)

    # Comprobar si FFmpeg está instalado al final
    if not check_ffmpeg_installed():
        print("\033[91m Only FFmpeg is missing. Please install it to proceed. \033[0m")


if __name__ == "__main__":
    # if sys.version_info >= (3, 13):
    #     print("❌ This script requires Python 3.12 or lower, because pydub needs audioop.")
    #     time.sleep(3)
    #     sys.exit(1)

    print("🔧 Checking pip...")
    ensure_pip()
    print("🚀 Processing requirements.txt in current folder...")
    install_requirements_in_directory("C:/Apps/Audio_analyzer")
    print("✅ Process completed.")
