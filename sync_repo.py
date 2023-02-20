import sys
import os
import json
import subprocess
import shutil

# Function to convert a path to an absolute path
def ConvertToAbsolutePath(path, configFilePath):
    if os.path.isabs(path):
        return path
    else:
        return os.path.abspath(os.path.join(os.path.dirname(configFilePath), path))

# Function to find all '<prefix><name>.json' files in the specified path
def FindRepositoriesFiles(path, prefix):
    repositoriesFiles = []
    for root, dirs, files in os.walk(path):
        for file in files:
            filePath = os.path.join(root, file)
            if os.path.isfile(filePath) and file.startswith(prefix) and file.endswith('.json'):
                repositoriesFiles.append(filePath)
    return repositoriesFiles

# Function to extract repository configuration from a '<prefix><name>.json' file
def ExtractRepositoryConfigs(filePath):
    configs = []
    with open(filePath, 'r') as f:
        data = json.load(f)
        for config in data:
            repoType = config['type']
            if repoType != 'git' and repoType != 'svn':
                print(f"Error: Invalid repository type '{repoType}' in file '{filePath}'")
                continue
            url = config['url']
            remote = config['remote']
            if remote == '' or remote == None:
                remote = 'origin'
            branch = config['branch']
            if branch == '' or branch == None:
                branch = 'main'
            path = ConvertToAbsolutePath(config['path'], filePath)
            version = config['version']
            # version must be number
            if version == '' or version == None:
                version = 0
            else:
                try:
                    version = int(version)
                except ValueError:
                    print(f"Error: Invalid version '{version}' in file '{filePath}'")
                    continue
            configs.append({
                'type': repoType,
                'url': url,
                'remote': remote,
                'branch': branch,
                'path': path,
                'version': version,
            })
    return configs

# Function to merge repository configurations with the same repository url and target path
def MergeRepositoryConfigs(configs):
    mergedConfigs = {}
    for config in configs:
        path = config['path']
        key = path
        if key in mergedConfigs:
            versionGreater = mergedConfigs[key]['version'] - config['version']
            if versionGreater <= 0:
                mergedConfigs[key] = config
        else:
            mergedConfigs[key] = config
    return list(mergedConfigs.values())

# Main function to retrieve and merge repository configurations
def RetrieveAndMergeRepositoryConfigs(path, prefix):
    configs = []
    repositories_files = FindRepositoriesFiles(path, prefix)
    for file in repositories_files:
        configs += ExtractRepositoryConfigs(file)
    return MergeRepositoryConfigs(configs)

def ReadStartConfig(filePath):
    with open(filePath, 'r') as f:
        data = json.load(f)
        targetPath = data['path']
        data['path'] = ConvertToAbsolutePath(targetPath, filePath)
    return data

def ExecuteSubprocessRunAnyway(commands):
    try:
        result = subprocess.run(commands)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    return

def UpdateGitRepository(config):
    url = config['url']
    remote = config['remote']
    branch = config['branch']
    targetPath = config['path']
    # check if the local path exists
    if not os.path.exists(targetPath):
        # if the local path does not exist
        # Clone the repository
        ExecuteSubprocessRunAnyway(['git', 'clone', url, targetPath])
    else:
        # if the local path exists, check if it's a git repository and if it's the same as the remote
        targetGitPath = os.path.join(targetPath, '.git')
        needGitFolder = False
        if os.path.exists(targetGitPath):
            # if it's a git repository, check if it's the same as the remote
            isRepo = False
            try:
                repoUrlOutput = subprocess.run(
                    ['git', '-C', targetPath, 'config', '--get', 'remote.' + remote + '.url'],
                    stdout=subprocess.PIPE,
                    check=True,
                )
                repoUrlOutput = repoUrlOutput.stdout.decode().strip()
                if repoUrlOutput == url:
                    isRepo = True
            except subprocess.CalledProcessError:
                return
            if not isRepo:
                # if the current remote is not the same as the desired remote
                # Remove '.git' folder
                shutil.rmtree(targetGitPath)
                needGitFolder = True
        else:
            # if the local path is not a git repository
            needGitFolder = True
        if needGitFolder:
            # Clone into a temp folder then move to targetPath
            tempPath = os.path.join(targetPath, "temp_path")
            shutil.rmtree(tempPath)
            ExecuteSubprocessRunAnyway(['git', 'clone', '--no-checkout', url, tempPath])
            shutil.move(os.path.join(tempPath, '.git'), targetPath)
            shutil.rmtree(tempPath)
    # Checkout the specified branch or tag
    ExecuteSubprocessRunAnyway(['git', '-C', targetPath, 'checkout', branch, '--force'])
    # If in branch, force update to the latest version
    ExecuteSubprocessRunAnyway(['git', '-C', targetPath, 'pull', remote, branch, '--force'])
    return

def UpdateSvnRepository(config):
    url = config['url']
    targetPath = config['path']
    # Check out the repository from the specified URL and branch or tag
    ExecuteSubprocessRunAnyway(['svn', 'checkout', '--force', url, '--revision', 'HEAD', targetPath])
    # Force update to the latest version
    ExecuteSubprocessRunAnyway(['svn', 'update', '--force', '--accept=theirs-full', targetPath])
    # Revert any changes if there is no update
    ExecuteSubprocessRunAnyway(['svn', 'revert', '--depth', 'infinity', targetPath])
    return

def UpdateAllRepositories(configs):
    for config in configs:
        if config['type'] == 'git':
            UpdateGitRepository(config)
        elif config['type'] == 'svn':
            UpdateSvnRepository(config)
    return

def Execute(configPath):
    if os.path.isfile(configPath) and configPath.endswith('.json'):
        startConfig = ReadStartConfig(configPath)
        print("Load repositories config: ")
        print(startConfig)
        configs = RetrieveAndMergeRepositoryConfigs(startConfig['path'], startConfig['prefix'])
        print("Update repositories: ")
        print(configs)
        UpdateAllRepositories(configs)
        print("Update repositories complete")
    return

def Main():
    configPath = None
    if len(sys.argv) > 1:
        configPath = sys.argv[1]
    else:
        configPath = input("Input config path: ")
    Execute(configPath)
    return

if __name__ == "__main__":
    Main()
