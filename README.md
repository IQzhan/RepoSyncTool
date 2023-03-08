# How to use
Create a json file named '\<config_name\>.json'
```json
{
    "path" : "<repositories config files path>",
    "prefix" : "<prefix of repositories config filenames default empty>",
    "rootPath": "<root path of project default this folder>"
}
```

Create repositories config files in '\<path\>' named '\<prefix\>\<name\>.json'
```json
[
    {
        "type": "git",
        "url": "<git url>",
        "remote": "<remote name default origin>",
        "branch": "<branch or tag name default master>",
        "path": "<{rootPath}/relative or absolute local path>",
        "version": <integer as version default 0>
    },
    {
        "type": "svn",
        "url": "<svn url>",
        "reversion": "<reversion name default HEAD>",
        "path": "<{rootPath}/relative or absolute local path>",
        "version": <integer as version default 0>
    }
    ...
]
```
Then execute script like
```cmd
python RepoSyncTool.py <config_name>.json
```
or
```cmd
RepoSyncTool.exe <config_name>.json
```
