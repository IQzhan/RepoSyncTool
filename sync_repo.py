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
def ExtractRepositoryConfigs(filePath, rootPath):
    configs = []
    with open(filePath, 'r') as f:
        data = json.load(f)
        for config in data:
            repoType = config['type']
            if repoType != 'git' and repoType != 'svn':
                print(
                    f"Error: Invalid repository type '{repoType}' in file '{filePath}'")
                continue
            url = config['url']
            # if remote key is not exist, use 'origin' as default
            remote = config.get('remote', 'origin')
            # if branch key is not exist, use 'master' as default
            branch = config.get('branch', 'master')
            # if revision key is not exist, use 'HEAD' as default
            revision = config.get('revision', 'HEAD')
            # get path and convert to absolute path
            try:
                path = config['path']
            except KeyError:
                print(f"Error: Missing path in file '{filePath}'")
                continue
            # replace '{rootPath}' with rootPath
            path = path.replace('{rootPath}', rootPath)
            path = ConvertToAbsolutePath(path, filePath)
            # if version key is not exist, use 0 as default
            version = config.get('version', 0)
            # version must be number
            try:
                version = int(version)
            except ValueError:
                print(
                    f"Error: Invalid version '{version}' in file '{filePath}'")
                continue
            thisConfig = {
                'type': repoType,
                'url': url,
                'path': path,
                'version': version,
            }
            if repoType == 'git':
                thisConfig['remote'] = remote
                thisConfig['branch'] = branch
            elif repoType == 'svn':
                thisConfig['revision'] = revision
            configs.append(thisConfig)
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
def RetrieveAndMergeRepositoryConfigs(path, prefix, rootPath):
    configs = []
    repositories_files = FindRepositoriesFiles(path, prefix)
    for file in repositories_files:
        configs += ExtractRepositoryConfigs(file, rootPath)
    return MergeRepositoryConfigs(configs)

# Function to read the start config file
def ReadStartConfig(filePath):
    with open(filePath, 'r') as f:
        data = json.load(f)
        # get target path and convert to absolute path for later use
        try:
            path = data['path']
        except KeyError:
            print(f"Error: Missing path in file '{filePath}'")
            return None
        data['path'] = ConvertToAbsolutePath(path, filePath)
        # if prefix key is not exist, use '' as default(no prefix) for later use
        data['prefix'] = data.get('prefix', '')
        # get root path and convert to absolute path for later use
        rootPath = data.get('rootPath', '')
        data['rootPath'] = ConvertToAbsolutePath(rootPath, filePath)
    return data

# Function to call console command
def ExecuteSubprocessRunAnyway(commands):
    try:
        result = subprocess.run(commands)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    return

# Function to update git repository
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
                    ['git', '-C', targetPath, 'config',
                        '--get', 'remote.' + remote + '.url'],
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
            ExecuteSubprocessRunAnyway(
                ['git', 'clone', '--no-checkout', url, tempPath])
            shutil.move(os.path.join(tempPath, '.git'), targetPath)
            shutil.rmtree(tempPath)
    # Checkout the specified branch or tag
    ExecuteSubprocessRunAnyway(
        ['git', '-C', targetPath, 'checkout', branch, '--force'])
    # If in branch, force update to the latest version
    ExecuteSubprocessRunAnyway(
        ['git', '-C', targetPath, 'pull', remote, branch, '--force'])
    return

# Function to update svn repository
def UpdateSvnRepository(config):
    url = config['url']
    targetPath = config['path']
    revision = config['revision']
    # Check out the repository from the specified URL and branch or tag
    ExecuteSubprocessRunAnyway(
        ['svn', 'checkout', '--force', url, '--revision', revision, targetPath])
    # Force update to the latest version
    ExecuteSubprocessRunAnyway(
        ['svn', 'update', '--force', '--accept=theirs-full', targetPath])
    # Revert any changes if there is no update
    ExecuteSubprocessRunAnyway(
        ['svn', 'revert', '--depth', 'infinity', targetPath])
    return

# Function to update all repositories
def UpdateAllRepositories(configs):
    for config in configs:
        if config['type'] == 'git':
            UpdateGitRepository(config)
        elif config['type'] == 'svn':
            UpdateSvnRepository(config)
    return

# Main function to execute the script
def Execute(configPath):
    if os.path.isfile(configPath) and configPath.endswith('.json'):
        startConfig = ReadStartConfig(configPath)
        if startConfig is None:
            return
        print("Load repositories config: ")
        print(startConfig)
        configs = RetrieveAndMergeRepositoryConfigs(
            startConfig['path'], startConfig['prefix'], startConfig['rootPath'])
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
