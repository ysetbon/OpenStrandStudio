# Fix for conda error and proper environment activation

Write-Host "Fixing conda initialization error..." -ForegroundColor Yellow

# Disable conda auto-activation if it exists
$env:CONDA_AUTO_ACTIVATE_BASE = "false"

# Check if we're in the OpenStrandStudio directory
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "Found local Python virtual environment (.venv)" -ForegroundColor Green
    
    # Deactivate conda if it's active
    if ($env:CONDA_DEFAULT_ENV) {
        Write-Host "Deactivating conda environment..." -ForegroundColor Yellow
        conda deactivate 2>$null
    }
    
    # Activate the local virtual environment
    Write-Host "Activating local virtual environment..." -ForegroundColor Green
    & .\.venv\Scripts\Activate.ps1
    
    Write-Host "Virtual environment activated successfully!" -ForegroundColor Green
    Write-Host "You can now use 'python' and 'pip' commands." -ForegroundColor Cyan
} else {
    Write-Host "No local virtual environment found." -ForegroundColor Red
    Write-Host "You can create one with: python -m venv .venv" -ForegroundColor Yellow
}

# Show Python version
Write-Host "`nCurrent Python:" -ForegroundColor Cyan
python --version

Write-Host "`nTo avoid this error in the future, use:" -ForegroundColor Yellow
Write-Host "  .\.venv\Scripts\Activate.ps1  (for virtual environment)" -ForegroundColor White
Write-Host "  conda activate base           (for conda base environment)" -ForegroundColor White
Write-Host "  conda activate crewai         (for conda crewai environment)" -ForegroundColor White