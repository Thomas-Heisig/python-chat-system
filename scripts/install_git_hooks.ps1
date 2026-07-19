Param()

$ErrorActionPreference = "Stop"

git config core.hooksPath .githooks
Write-Host "Git hooks activated: core.hooksPath=.githooks"
