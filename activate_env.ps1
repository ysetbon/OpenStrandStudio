# PowerShell script to activate the virtual environment
# Run this in PowerShell to activate your environment

# First, ensure execution policy allows running scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Activate the virtual environment
& .\.venv\Scripts\Activate.ps1

Write-Host "Virtual environment activated successfully!" -ForegroundColor Green
Write-Host "You can now run Python and pip commands." -ForegroundColor Yellow