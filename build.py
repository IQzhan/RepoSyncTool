import os
import shutil
import subprocess

fileName = "RepoSyncTool"


def GetAbsolutePath(relativePath):
    """Function to get absolute path"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relativePath)


def Cmd(commands):
    """Function to call console commands and ignore errors"""
    try:
        result = subprocess.run(commands)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    return


def Main():
    """Main function"""
    filePath = GetAbsolutePath("src/" + fileName + ".py")
    outputPath = GetAbsolutePath("output")
    buildPath = GetAbsolutePath("build")
    # create the output folder if it doesn't exist
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
    # build the executable
    Cmd([
        'pyinstaller',
        '--onefile', filePath,
        '--distpath=' + outputPath,
        '--workpath=' + buildPath,
        '--specpath=' + buildPath])
    # force delete of build folder
    shutil.rmtree(buildPath)
    return


if __name__ == "__main__":
    Main()
