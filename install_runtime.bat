@echo off
echo ���ڼ��Ͱ�װ��Ҫ������ʱ����...
echo.

echo 1. ��� .NET Framework...
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full" /v Release >nul 2>&1
if %errorlevel% neq 0 (
    echo .NET Framework 4.7.2 ����߰汾δ��װ
    echo ��������������ذ�װ:
    echo https://dotnet.microsoft.com/download/dotnet-framework
    echo.
) else (
    echo .NET Framework �Ѱ�װ
)

echo 2. ��� Microsoft Edge WebView2...
if exist "%PROGRAMFILES(X86)%\Microsoft\EdgeWebView\Application\msedgewebview2.exe" (
    echo Microsoft Edge WebView2 �Ѱ�װ
) else (
    echo Microsoft Edge WebView2 δ��װ
    echo ��������������ذ�װ:
    echo https://developer.microsoft.com/microsoft-edge/webview2/
    echo.
)

echo 3. ��� Visual C++ Redistributable...
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" >nul 2>&1
if %errorlevel% neq 0 (
    echo Visual C++ Redistributable δ��װ
    echo ��������������ذ�װ:
    echo https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
) else (
    echo Visual C++ Redistributable �Ѱ�װ
)

echo.
echo �����ɣ������ȱʧ��������밴����ʾ��װ��
pause
