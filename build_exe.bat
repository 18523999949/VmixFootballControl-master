@echo off
chcp 65001 >nul
echo ===============================================
echo   Vmix足球比赛控制面板 - 编译EXE
echo ===============================================
echo.

REM 检查PyInstaller是否安装
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [错误] PyInstaller 未安装
    echo.
    echo 正在安装 PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败
        echo 请手动运行: pip install pyinstaller
        pause
        exit /b 1
    )
    echo ✓ PyInstaller 安装成功
    echo.
)

echo 开始编译...
echo.

REM 清理旧的构建文件
if exist "build" (
    echo 清理旧的构建文件...
    rmdir /s /q build
)

if exist "dist\VmixFootballControl.exe" (
    echo 清理旧的exe文件...
    del /q "dist\VmixFootballControl.exe"
)

echo 使用 PyInstaller 编译...
echo.

REM 使用spec文件编译
pyinstaller build_exe.spec

if errorlevel 1 (
    echo.
    echo [错误] 编译失败！
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   编译成功！
echo ===============================================
echo.
echo EXE文件位置: dist\VmixFootballControl.exe
echo.
echo 注意：
echo   1. 确保以下文件与exe在同一目录：
echo      - config.json
echo      - away.txt
echo      - home.txt
echo      - （其他CSV文件会在运行时自动创建）
echo.
echo   2. 如果需要打包所有文件为单文件，请修改 build_exe.spec
echo      中的 datas 配置
echo.
pause

