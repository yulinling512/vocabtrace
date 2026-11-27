# 打安卓 APK（Windows 版，等价于 build-apk.sh）
# 用法：$env:KS_PASS="你的签名密码"; pwsh -File build-apk.ps1 -Ver 1.0.14 -Code 115
param(
  [string]$Ver = "1.0.14",
  [int]$Code = 115
)
$ErrorActionPreference = "Stop"

# 目录按仓库相对路径推导，克隆下来即可直接构建
$PROJ = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT = Split-Path -Parent $PROJ
$SDK = if ($env:ANDROID_SDK_ROOT) { $env:ANDROID_SDK_ROOT } else { "$env:LOCALAPPDATA\Android\Sdk" }
$JDK = if ($env:JAVA_HOME) { $env:JAVA_HOME } else { "C:\Program Files\Java\jdk-17" }
$BT = "$SDK\build-tools\34.0.0"
$AJAR = "$SDK\platforms\android-34\android.jar"
$OUT = "$ROOT\dist\词迹-安卓-$Ver.apk"

$env:PATH = "$JDK\bin;$env:PATH"

if (Test-Path "$PROJ\build") { Remove-Item "$PROJ\build" -Recurse -Force }
New-Item -ItemType Directory -Path "$PROJ\build\classes","$PROJ\build\dex","$PROJ\build\gen" -Force | Out-Null

Write-Host "[1/7] 编译 Java"
& "$JDK\bin\javac.exe" -source 8 -target 8 -encoding UTF-8 -cp $AJAR -d "$PROJ\build\classes" `
  "$PROJ\src\com\vocabtrace\app\MainActivity.java" 2>&1 | Where-Object { $_ -notmatch "bootstrap class path" }

Write-Host "[2/7] 生成 dex"
$classes = (Get-ChildItem "$PROJ\build\classes" -Filter *.class -Recurse | ForEach-Object { $_.FullName }) -join " "
& "$BT\d8.bat" --lib $AJAR --min-api 19 --output "$PROJ\build\dex" $classes.Split(" ", [StringSplitOptions]::RemoveEmptyEntries)

Write-Host "[3/7] 打包资源与清单"
& "$BT\aapt2.exe" compile --dir "$PROJ\res" -o "$PROJ\build\res.zip"
& "$BT\aapt2.exe" link -o "$PROJ\build\base.apk" -I $AJAR `
  --manifest "$PROJ\AndroidManifest.xml" -A "$PROJ\assets" `
  -R "$PROJ\build\res.zip" `
  --java "$PROJ\build\gen" --min-sdk-version 19 --target-sdk-version 34 `
  --version-code $Code --version-name $Ver

Write-Host "[4/7] 合入 dex"
Push-Location "$PROJ\build\dex"
& "$JDK\bin\jar.exe" uf "$PROJ\build\base.apk" classes.dex
Pop-Location

Write-Host "[5/7] 钥匙"
$KS = "$PROJ\keystore\vocabtrace.jks"
if (!(Test-Path $KS)) { throw "缺少签名钥匙 $KS" }

Write-Host "[6/7] 对齐并签名"
& "$BT\zipalign.exe" -f -p 4 "$PROJ\build\base.apk" "$PROJ\build\aligned.apk"
if (-not $env:KS_PASS) { throw "缺少签名密码：先设置环境变量 KS_PASS" }
& "$BT\apksigner.bat" sign --ks $KS --ks-pass "pass:$env:KS_PASS" --key-pass "pass:$env:KS_PASS" `
  --out $OUT "$PROJ\build\aligned.apk"

Write-Host "[7/7] 校验"
& "$BT\apksigner.bat" verify --print-certs $OUT
Get-Item $OUT | Select-Object FullName,Length
Write-Host "APK_OK"
