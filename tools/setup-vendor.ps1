# 安装「自动发布 / 自动采集」依赖：social-auto-upload
#
# 猫后台助手本身可以独立运行（手动发布、素材库、排期、看板、账号记录）。
# 只有「自动发布」和「自动采集作品数据」需要 vendor/social-auto-upload 及其虚拟环境，
# 本脚本负责把它拉下来、建好 .venv、装好 patchright 的 Chromium。
#
# 用法（需已安装 Python 3.12，且能访问 GitHub / PyPI）：
#   powershell -ExecutionPolicy Bypass -File tools\setup-vendor.ps1
#
param(
    [string]$Repo = "https://github.com/dreammis/social-auto-upload.git",
    [string]$Python = "python"
)

# git / pip 会把进度写到 stderr，Stop 会把它们误判为致命错误
$ErrorActionPreference = "Continue"

function Assert-LastExit([string]$what) {
    if ($LASTEXITCODE -ne 0) { throw "$what 失败（退出码 $LASTEXITCODE）" }
}

$root = Split-Path -Parent $PSScriptRoot
$vendorDir = Join-Path $root "vendor"
$target = Join-Path $vendorDir "social-auto-upload"

Write-Host "[1/5] 检查 Python..." -ForegroundColor Cyan
& $Python --version
Assert-LastExit "Python 检测"

if (-not (Test-Path (Join-Path $target ".git"))) {
    Write-Host "[2/5] 克隆 social-auto-upload 到 vendor/" -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path $vendorDir | Out-Null
    git clone --depth 1 $Repo $target
    Assert-LastExit "git clone"
} else {
    Write-Host "[2/5] 已存在 vendor/social-auto-upload，跳过克隆" -ForegroundColor DarkGray
}

$venv = Join-Path $target ".venv"
$venvPython = Join-Path $venv "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[3/5] 创建虚拟环境 .venv" -ForegroundColor Cyan
    & $Python -m venv $venv
    Assert-LastExit "python -m venv"
}

Write-Host "[4/5] 安装依赖（pip install -e .）" -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -e $target
Assert-LastExit "pip install -e"

Write-Host "[5/5] 安装 patchright 浏览器内核" -ForegroundColor Cyan
& $venvPython -m patchright install chromium
Assert-LastExit "patchright install chromium"

$conf = Join-Path $target "conf.py"
if (-not (Test-Path $conf)) {
    Copy-Item (Join-Path $target "conf.example.py") $conf
    Write-Host "已从 conf.example.py 生成 conf.py" -ForegroundColor Cyan
}

$sau = Join-Path $venv "Scripts\sau.exe"
if (Test-Path $sau) {
    Write-Host "`n完成：自动发布依赖已就绪 -> $sau" -ForegroundColor Green
    Write-Host "回到「账号管理」扫码登录后即可使用自动发布。" -ForegroundColor Green
} else {
    Write-Warning "未找到 sau.exe，请确认 pip install -e 是否成功。"
}
