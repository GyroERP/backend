param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath,
    [Parameter(Mandatory = $true)]
    [string]$Message
)

$git = "C:\Program Files\Git\cmd\git.exe"
Set-Location $RepoPath

& $git add -A

$status = (& $git status --porcelain).Trim()
if (-not $status) {
    Write-Output "Nothing to commit in $RepoPath"
    exit 0
}

$tree = (& $git write-tree).Trim()
$parent = (& $git rev-parse HEAD 2>$null).Trim()
$now = [int][double](Get-Date -UFormat %s)

if ($parent -and $LASTEXITCODE -eq 0) {
    $commitContent = "tree $tree`nparent $parent`nauthor TheodoreAsher <agchaveli@gmail.com> $now +0500`ncommitter TheodoreAsher <agchaveli@gmail.com> $now +0500`n`n$Message`n"
} else {
    $commitContent = "tree $tree`nauthor TheodoreAsher <agchaveli@gmail.com> $now +0500`ncommitter TheodoreAsher <agchaveli@gmail.com> $now +0500`n`n$Message`n"
}

$newCommit = ($commitContent | & $git hash-object -w -t commit --stdin).Trim()
& $git reset --hard $newCommit | Out-Null

Write-Output "Committed: $newCommit"
& $git cat-file -p HEAD
& $git push origin main
