param([string]$PythonExecutable = '')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not $PythonExecutable) {
    if (Test-Path -LiteralPath $bundledPython) { $PythonExecutable = $bundledPython }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExecutable = 'py' }
    else { $PythonExecutable = 'python' }
}
if (-not (Test-Path .venv\Scripts\python.exe)) {
    if ($PythonExecutable -eq $bundledPython) { & $PythonExecutable -m venv --without-pip .venv }
    else { & $PythonExecutable -m venv .venv }
    if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed; specify -PythonExecutable with Python 3.12+ path' }
}
if ($PythonExecutable -eq $bundledPython) {
    & $PythonExecutable -m pip --python .venv\Scripts\python.exe install -r backend\requirements-dev.txt
} else { & .venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt }
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
Push-Location frontend
npm.cmd ci
if ($LASTEXITCODE -ne 0) { throw 'Frontend installation failed' }
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
Pop-Location
& .venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
