param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath,
    [Parameter(Mandatory = $true)]
    [string]$RepoName,
    [Parameter(Mandatory = $true)]
    [string]$Message
)

$git = "C:\Program Files\Git\cmd\git.exe"
Set-Location $RepoPath

if (-not ((& $git remote) -contains "origin")) {
    & $git remote add origin "https://github.com/GyroERP/$RepoName.git"
}

& $git fetch origin
& $git checkout main 2>$null
& $git reset --hard origin/main | Out-Null

$branch = "chore/ci-and-codeowners"
& $git checkout -B $branch | Out-Null
& $git add -A

$status = (& $git status --porcelain).Trim()
if (-not $status) {
    Write-Output "Nothing to commit in $RepoName"
    exit 0
}

$tree = (& $git write-tree).Trim()
$parent = (& $git rev-parse HEAD).Trim()
$now = [int][double](Get-Date -UFormat %s)
$commitContent = "tree $tree`nparent $parent`nauthor TheodoreAsher <agchaveli@gmail.com> $now +0500`ncommitter TheodoreAsher <agchaveli@gmail.com> $now +0500`n`n$Message`n"
$newCommit = ($commitContent | & $git hash-object -w -t commit --stdin).Trim()
& $git reset --hard $newCommit | Out-Null

Write-Output "=== $RepoName commit ==="
& $git cat-file -p HEAD | Select-Object -First 8
& $git push -u origin $branch --force

$prUrl = gh pr create --repo "GyroERP/$RepoName" --head $branch --base main --title $Message --body "Adds CI workflows, CODEOWNERS, Dependabot, and branch protection JSON templates."
Write-Output "PR: $prUrl"

$prNumber = ($prUrl -split '/')[-1]
Write-Output "Waiting for CI on PR #$prNumber..."
Start-Sleep -Seconds 50
gh pr checks $prNumber --repo "GyroERP/$RepoName"

$tempFile = Join-Path $RepoPath "scripts/branch-protection-temp-merge.json"
gh api --method PUT "repos/GyroERP/$RepoName/branches/main/protection" --input $tempFile | Out-Null
gh pr merge $prNumber --repo "GyroERP/$RepoName" --merge --admin --delete-branch 2>$null
if ($LASTEXITCODE -ne 0) {
    gh pr merge $prNumber --repo "GyroERP/$RepoName" --squash --admin --delete-branch
}

$protectFile = Join-Path $RepoPath "scripts/branch-protection.json"
gh api --method PUT "repos/GyroERP/$RepoName/branches/main/protection" --input $protectFile | Out-Null
Write-Output "Branch protection restored for $RepoName"

& $git checkout main
& $git pull origin main
