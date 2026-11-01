# 一键构建发布包：打包 exe -> 生成安装包与免安装压缩包 -> 输出到 release/
#
# 用法（在项目根目录）：
#   powershell -ExecutionPolicy Bypass -File build-release.ps1
#
# 产物：
#   release\猫后台助手_Setup_1.0.0.exe      安装包（含卸载、开始菜单、可选桌面快捷方式）
#   release\猫后台助手_v1.0.0_portable.zip  免安装压缩包

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$version = "1.0.0"
$dist = Join-Path $root "dist\猫后台助手"
$release = Join-Path $root "release"
$payload = Join-Path $release "payload"
$iscc = Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"
$sevenZip = "C:\Program Files\7-Zip\7z.exe"

Write-Host "[1/5] PyInstaller 打包" -ForegroundColor Cyan
Push-Location $root
try {
    python -m PyInstaller --noconfirm "猫后台助手.spec"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller 失败" }
} finally { Pop-Location }

Write-Host "[2/5] 准备安装载荷（排除用户数据 data\\）" -ForegroundColor Cyan
if (Test-Path $payload) { Remove-Item -LiteralPath $payload -Recurse -Force }
New-Item -ItemType Directory -Force -Path $payload | Out-Null
Copy-Item -Path (Join-Path $dist "*") -Destination $payload -Recurse -Force
Remove-Item -LiteralPath (Join-Path $payload "data") -Recurse -Force -ErrorAction SilentlyContinue
foreach ($junk in @("__pycache__")) {
    Get-ChildItem -LiteralPath $payload -Recurse -Directory -Filter $junk -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "[3/5] 生成免安装压缩包" -ForegroundColor Cyan
$zip = Join-Path $release "猫后台助手_v$version"+"_portable.zip"
if (Test-Path $zip) { Remove-Item -LiteralPath $zip -Force }
& $sevenZip a -tzip -mx=9 $zip (Join-Path $payload "*") | Out-Null
if ($LASTEXITCODE -ne 0) { throw "7z 压缩失败" }

Write-Host "[4/5] 编译安装包" -ForegroundColor Cyan
& $iscc "/DMyAppVersion=$version" (Join-Path $root "packaging\installer.iss") | Out-Null
if ($LASTEXITCODE -ne 0) { throw "ISCC 失败" }

Write-Host "[5/5] 完成" -ForegroundColor Green
Get-ChildItem -LiteralPath $release -File | Select-Object Name, @{n='MB';e={[math]::Round($_.Length/1MB,1)}} | Format-Table -AutoSize
