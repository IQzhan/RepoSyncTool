# How to use
Create a json file named '\<config_name\>.json'
```json
{
    "path" : "<repositories config files path>",
    "prefix" : "<prefix of repositories config filenames>",
    "rootPath": "<root path of project>"
}
```

Create repositories config files in '\<path\>' named '\<prefix\>\<name\>.json'
```json
[
    {
        "type": "git",
        "url": "<git url>",
        "remote": "<remote name>",
        "branch": "<branch or tag name>",
        "path": "<{rootPath}/relative or absolute local path>",
        "version": <integer as version>
    },
    {
        "type": "svn",
        "url": "<svn url>",
        "reversion": "<reversion name>",
        "path": "<{rootPath}/relative or absolute local path>",
        "version": <integer as version>
    }
    ...
]
```
Then execute script.
```cmd
python sync_repo.py <config_name>.json
```
