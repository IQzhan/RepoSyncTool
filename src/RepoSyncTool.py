import sys
import os
import json
import subprocess
import shutil


def ConvertToAbsolutePath(path, configFilePath):
    """Function to convert a path to an absolute path"""
    if os.path.isabs(path):
        return path
    else:
        return os.path.abspath(os.path.join(os.path.dirname(configFilePath), path))


def Cmd(commands):
    """Function to call console commands and ignore errors"""
    try:
        result = subprocess.run(commands)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    return


def UpdateSvnRepository(config):
    """Function to update svn repository"""
    url = config['url']
    targetPath = config['path']
    revision = config['revision']
    # Check out the repository from the specified URL and branch or tag
    Cmd(['svn', 'checkout', '--force', url, '--revision', revision, targetPath])
    # Force update to the latest version
    Cmd(['svn', 'update', '--force', '--accept=theirs-full', targetPath])
    # Revert any changes if there is no update
    Cmd(['svn', 'revert', '--depth', 'infinity', targetPath])
    return


def UpdateGitRepository(config):
    """Function to update git repository"""
    url = config['url']
    remote = config['remote']
    branch = config['branch']
    targetPath = config['path']
    # check if the local path exists
    if not os.path.exists(targetPath):
        # if the local path does not exist
        # Clone the repository
        Cmd(['git', 'clone', url, targetPath])
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
            Cmd(['git', 'clone', '--no-checkout', url, tempPath])
            shutil.move(os.path.join(tempPath, '.git'), targetPath)
            shutil.rmtree(tempPath)
    # Checkout the specified branch or tag
    Cmd(['git', '-C', targetPath, 'checkout', branch, '--force'])
    # If in branch, force update to the latest version
    Cmd(['git', '-C', targetPath, 'pull', remote, branch, '--force'])
    return


def MergeRepositoryConfigs(configs):
    """Function to merge repository configurations with the same repository url and target path"""
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


def ExtractRepositoryConfigs(filePath, rootPath):
    """Function to extract repository configuration from a '<prefix><name>.json' file"""
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


def FindRepositoriesFiles(path, prefix):
    """Function to find all '<prefix><name>.json' files in the specified path"""
    repositoriesFiles = []
    for root, dirs, files in os.walk(path):
        for file in files:
            filePath = os.path.join(root, file)
            if os.path.isfile(filePath) and file.startswith(prefix) and file.endswith('.json'):
                repositoriesFiles.append(filePath)
    return repositoriesFiles


def UpdateAllRepositories(configs):
    """Function to update all repositories"""
    for config in configs:
        if config['type'] == 'git':
            UpdateGitRepository(config)
        elif config['type'] == 'svn':
            UpdateSvnRepository(config)
    return


def RetrieveAndMergeRepositoryConfigs(path, prefix, rootPath):
    """Main function to retrieve and merge repository configurations"""
    configs = []
    repositories_files = FindRepositoriesFiles(path, prefix)
    for file in repositories_files:
        configs += ExtractRepositoryConfigs(file, rootPath)
    return MergeRepositoryConfigs(configs)


def ReadStartConfig(filePath):
    """Function to read the start config file"""
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


def Execute(configPath):
    """Main function to execute the script"""
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
    """Main function"""
    configPath = None
    if len(sys.argv) > 1:
        configPath = sys.argv[1]
    else:
        configPath = input("Input config path: ")
    Execute(configPath)
    return


if __name__ == "__main__":
    Main()
