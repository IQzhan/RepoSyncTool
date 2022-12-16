# Started directory
$oriDir = Get-Location
# Get the current directory
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
# Load the configuration
$config = Get-Content "$dir/sync_repo.json" -Raw | ConvertFrom-Json
# Iterate over the configured git repositories
foreach ($repo in $config.repositories) {
    # Target directory
    $targetDir = Join-Path $dir $repo.path
    # Git
    if ($repo.type -eq "git") {
        # check if the local path exists
        if (Test-Path $targetDir) {
            $removeOriginalGit = 'false'
            $downloadNewGit = 'false'
            # if the local path exists, check if it's a git repository and if it's the same as the remote
            $gitPath = Join-Path $targetDir ".git"
            if (Test-Path $gitPath) {
                # if it's a git repository, check if it's the same as the remote
                $currentRemoteURL = (git -C $targetDir remote get-url origin)
                if ($currentRemoteURL -ne $repo.url) {
                    # if the current remote is not the same as the desired remote
                    $removeOriginalGit = 'true'
                    $downloadNewGit = 'true'
                }
            }
            else {
                # if the local path is not a git repository
                $downloadNewGit = 'true'
            }
            if ($removeOriginalGit -eq 'true') {
                # Remove '.git' folder
                Remove-Item -Path $gitPath -Recurse -Force -ErrorAction Ignore
            }
            if ($downloadNewGit -eq 'true') {
                # Will create 'temp_git' as temp folder for matiain '.git' folder whitch clone from remote
                $tempPath = Join-Path $targetDir "temp_git"
                if (Test-Path $tempPath) {
                    Remove-Item -Path $tempPath -Recurse -Force -ErrorAction Ignore
                }
                # Clone from remote to 'temp_git', '--no-checkout' makes sure only '.git' folder will be create
                git clone --no-checkout $repo.url $tempPath
                # Move this new '.git' folder to $targetDir
                $tempPathGit = Join-Path $tempPath ".git"
                Move-Item -Path $tempPathGit -Destination $targetDir
                # Remove 'temp_git' folder
                Remove-Item -Path $tempPath -Recurse -Force -ErrorAction Ignore
            }
        }
        else {
            # if the local path does not exist
            # Checkout the repository
            git clone $repo.url $targetDir
        }
        # Switch to the repository directory
        Set-Location $targetDir
        # Checkout the specified branch or tag
        git checkout $repo.branch --force
        # If in branch, force update to the latest version
        git pull --force
    }
    # Svn
    elseif ($repo.type -eq "svn") {
        # Check out the repository from the specified URL and branch or tag
        svn checkout --force $repo.url --revision $repo.branch $targetDir
        # Switch to the repository directory
        Set-Location $targetDir
        # Force update to the latest version
        svn update --force --accept=theirs-full
        # Revert any changes if there is no update
        svn revert --depth infinity $targetDir
    }
    else {
        Write-Output "'type' must be 'git' or 'svn'."
    }
}
Write-Output "Update repositories finished."
# Back to started directory
Set-Location $oriDir
