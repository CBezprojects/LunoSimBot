Set-Location -Path "$PSScriptRoot\..\bot"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3 and add to PATH."
    exit
}
if (-not (pip show requests)) {
    Write-Host "📦 Installing missing 'requests' module..."
    pip install requests
}

Write-Host "🚀 Starting LunoSimBot..."
python .\main.py
