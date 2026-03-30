import os
import subprocess
import sys
import importlib.metadata

def ensure_pip():
    """Ensures pip is available by checking the module via subprocess."""
    try:
        # Running 'pip --version' is more reliable than 'import pip'
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                       check=True, capture_output=True)
        print("✅ pip is already installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ pip not found. Installing with ensurepip...")
        subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
        print("✅ pip installed successfully.")

def check_ffmpeg_installed():
    """Checks if FFmpeg is available in the system PATH."""
    try:
        subprocess.run(["ffmpeg", "-version"], 
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def is_installed(req_string):
    """
    Checks if a package meets the required version using modern importlib.metadata.
    """
    try:
        # External library 'packaging' is the standard for parsing requirements.txt
        from packaging.requirements import Requirement
    except ImportError:
        print("📦 Installing 'packaging' for version parsing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "packaging"])
        from packaging.requirements import Requirement

    try:
        req = Requirement(req_string)
        # Fetch the version of the installed package
        dist_version = importlib.metadata.version(req.name)
        
        # If no version constraints (like == or >=), being installed is enough
        if not req.specifier:
            return True, dist_version
        
        # Check if installed version matches the requirement specifier
        if dist_version in req.specifier:
            return True, dist_version
        else:
            return False, dist_version
            
    except importlib.metadata.PackageNotFoundError:
        return False, None
    except Exception as e:
        print(f"❌ Error parsing {req_string}: {e}")
        return False, None

def install_requirements_in_directory(base_dir):
    """
    Walk through folders to find requirements.txt and manage installations.
    """
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file == "requirements.txt":
                req_path = os.path.join(root, file)
                print(f"\n🔍 Found requirements: {req_path}")

                try:
                    with open(req_path, 'r', encoding='utf-8') as f:
                        # Clean lines and ignore comments or recursive flags
                        requirements = [line.strip() for line in f 
                                       if line.strip() and not line.startswith(('#', '-r'))]
                except Exception as e:
                    print(f"❌ Failed to read {req_path}: {e}")
                    continue

                for req in requirements:
                    installed, current_v = is_installed(req)
                    
                    if installed:
                        print(f"✅ {req} is already satisfied (Installed: {current_v}).")
                    elif current_v:
                        # Package exists but version is incompatible
                        print(f"⚠️ Version conflict for {req}: installed {current_v}. Skipping to avoid environment breakage.")
                    else:
                        # Package is missing
                        print(f"📦 {req} not found. Installing...")
                        result = subprocess.run([sys.executable, "-m", "pip", "install", req])
                        if result.returncode == 0:
                            print(f"✅ Successfully installed {req}")
                        else:
                            print(f"❌ Failed to install {req}")
                            sys.exit(1)

    # Optional: Final FFmpeg check
    # if not check_ffmpeg_installed():
    #     print("\033[31mFFmpeg is not installed. This may cause issues with audio processing.\033[0m")

if __name__ == "__main__":
    # Note: Python 3.13+ has removed 'audioop', which pydub requires.
    # If using pydub, ensure you are on Python 3.12 or below.

    print("🔧 Checking pip environment...")
    ensure_pip()
    
    # Path configuration
    TARGET_DIR = r"C:/Apps/Audio_analyzer"
    
    if os.path.exists(TARGET_DIR):
        print(f"🚀 Processing directory: {TARGET_DIR}")
        install_requirements_in_directory(TARGET_DIR)
        print("\n✅ Setup completed.")
    else:
        print(f"❌ Error: The directory '{TARGET_DIR}' was not found.")
