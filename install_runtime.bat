@echo off
echo 正在检查和安装必要的运行时环境...
echo.

echo 1. 检查 .NET Framework...
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full" /v Release >nul 2>&1
if %errorlevel% neq 0 (
    echo .NET Framework 4.7.2 或更高版本未安装
    echo 请从以下链接下载安装:
    echo https://dotnet.microsoft.com/download/dotnet-framework
    echo.
) else (
    echo .NET Framework 已安装
)

echo 2. 检查 Microsoft Edge WebView2...
if exist "%PROGRAMFILES(X86)%\Microsoft\EdgeWebView\Application\msedgewebview2.exe" (
    echo Microsoft Edge WebView2 已安装
) else (
    echo Microsoft Edge WebView2 未安装
    echo 请从以下链接下载安装:
    echo https://developer.microsoft.com/microsoft-edge/webview2/
    echo.
)

echo 3. 检查 Visual C++ Redistributable...
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" >nul 2>&1
if %errorlevel% neq 0 (
    echo Visual C++ Redistributable 未安装
    echo 请从以下链接下载安装:
    echo https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
) else (
    echo Visual C++ Redistributable 已安装
)

echo.
echo 检查完成！如果有缺失的组件，请按照提示安装。
pause
