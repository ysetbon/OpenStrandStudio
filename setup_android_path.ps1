$androidPath = "$env:LOCALAPPDATA\Android\Sdk\platform-tools"
$currentPath = [Environment]::GetEnvironmentVariable('Path', 'User')

if ($currentPath -notlike "*platform-tools*") {
    [Environment]::SetEnvironmentVariable('Path', "$currentPath;$androidPath", 'User')
    Write-Host "Added platform-tools to PATH: $androidPath"
} else {
    Write-Host "platform-tools already in PATH"
}

Write-Host "Done! Close and reopen your terminal for changes to take effect."
