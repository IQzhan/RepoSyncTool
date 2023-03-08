import os
import subprocess


def GetAbsolutePath(fileName):
    """Function to get absolute path"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), fileName)


def ExecuteSubprocessRunAnyway(commands):
    """Function to call console commands and ignore errors"""
    try:
        result = subprocess.run(commands)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    return


def Main():
    """Main function"""
    fileName = "sync_repo.py"
    filePath = GetAbsolutePath(fileName)
    ExecuteSubprocessRunAnyway(['pyinstaller', '--onefile', filePath])
    return


if __name__ == "__main__":
    Main()
