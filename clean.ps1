# DSVis 清理脚本 — 删除所有 Python 编译产物
# 用法: .\clean.ps1

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "清理 DSVis 编译产物..." -ForegroundColor Cyan

# __pycache__ 目录
$pycacheDirs = Get-ChildItem -Path $root -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
foreach ($dir in $pycacheDirs) {
    Write-Host "  删除: $($dir.FullName)" -ForegroundColor Gray
    Remove-Item -Path $dir.FullName -Recurse -Force
}

# .pyc 文件
$pycFiles = Get-ChildItem -Path $root -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue
foreach ($f in $pycFiles) {
    Write-Host "  删除: $($f.FullName)" -ForegroundColor Gray
    Remove-Item -Path $f.FullName -Force
}

# .pyo 文件
$pyoFiles = Get-ChildItem -Path $root -Recurse -File -Filter "*.pyo" -ErrorAction SilentlyContinue
foreach ($f in $pyoFiles) {
    Write-Host "  删除: $($f.FullName)" -ForegroundColor Gray
    Remove-Item -Path $f.FullName -Force
}

# 临时 HTML（调试输出产物）
$tmpHtml = Get-ChildItem -Path $root -Recurse -File -Filter "*.html" -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -like "debug_*" -or $_.Name -like "DSVis_Debugger_*"
}
foreach ($f in $tmpHtml) {
    Write-Host "  删除临时HTML: $($f.FullName)" -ForegroundColor Gray
    Remove-Item -Path $f.FullName -Force
}

$count = ($pycacheDirs.Count + $pycFiles.Count + $pyoFiles.Count + $tmpHtml.Count)
Write-Host "`n清理完成: 共删除 $count 项" -ForegroundColor Green
