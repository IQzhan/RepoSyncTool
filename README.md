# How to use
Write into sync_repo.json like this:
```json
{
    "repositories": [
        {
            "type": "git",
            "url": "git url",
            "path": "relative path",
            "branch": "branch or tag"
        },
        {
            "type": "svn",
            "url": "svn url",
            "path": "relative path",
            "branch": "revision"
        }
    ]
}
```
Then execute sync_repo.ps1
