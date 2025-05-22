import subprocess
import sys


def install_package(package_name: str):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
