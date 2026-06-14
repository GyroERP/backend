param(
    [string]$Repo = "backend"
)

$base = "e:\GyroERP\$Repo\scripts"
$owner = "GyroERP"

$rules = @(
    @{ branch = "main"; file = "branch-protection-backend.json" },
    @{ branch = "development"; file = "branch-protection-development.json" },
    @{ branch = "staging"; file = "branch-protection-staging.json" },
    @{ branch = "beta-release"; file = "branch-protection-beta-release.json" }
)

foreach ($rule in $rules) {
    $path = Join-Path $base $rule.file
    if (-not (Test-Path $path)) {
        Write-Output ("Skip " + $rule.branch + " missing " + $path)
        continue
    }
    Write-Output "Protecting $owner/$Repo :: $($rule.branch)"
    gh api --method PUT "repos/$owner/$Repo/branches/$($rule.branch)/protection" --input $path | Out-Null
}

Write-Output "Done."
