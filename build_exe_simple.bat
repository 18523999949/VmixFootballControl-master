@echo off
chcp 65001 >nul
echo ===============================================
echo   简单编译脚本（一键编译）
echo ===============================================
echo.

REM 检查PyInstaller是否安装
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 正在安装 PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败
        pause
        exit /b 1
    )
)

echo 开始编译...
echo.

REM 生成日期时间版本号 (YYYYMMDDHHmm格式，例如V202511110055)
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set "YYYY=%datetime:~0,4%"
set "MM=%datetime:~4,2%"
set "DD=%datetime:~6,2%"
set "HH=%datetime:~8,2%"
set "mm=%datetime:~10,2%"
set "VERSION=V%YYYY%%MM%%DD%%HH%%mm%"
set "EXE_NAME=足球比赛字幕控制系统%VERSION%"

echo 生成的文件名: %EXE_NAME%.exe
echo.

REM 检查图标文件是否存在
set "ICON_FILE=app.ico"
set "ICON_PARAM="
if exist "%ICON_FILE%" (
    set "ICON_PARAM=--icon=%ICON_FILE%"
    echo 找到图标文件: %ICON_FILE%
) else (
    echo 提示: 未找到图标文件 %ICON_FILE%，将使用默认图标
    echo       如需自定义图标，请将 .ico 文件命名为 app.ico 并放在项目根目录
)
echo.

REM 清理
if exist "build" rmdir /s /q build
if exist "dist\%EXE_NAME%.exe" del /q "dist\%EXE_NAME%.exe"

REM 直接使用PyInstaller命令编译
set "ADD_DATA_PARAMS=--add-data config.json;. --add-data away.txt;. --add-data home.txt;."
if exist "%ICON_FILE%" (
    set "ADD_DATA_PARAMS=%ADD_DATA_PARAMS% --add-data %ICON_FILE%;."
)

pyinstaller --name=%EXE_NAME% ^
    --onefile ^
    --windowed ^
    --clean ^
    --noconfirm ^
    %ICON_PARAM% ^
    %ADD_DATA_PARAMS% ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --exclude-module=matplotlib ^
    --exclude-module=numpy ^
    --exclude-module=pandas ^
    a0.95.py

if errorlevel 1 (
    echo.
    echo [错误] 编译失败！
    pause
    exit /b 1
)

echo.
echo ✓ 编译成功！文件位置: dist\%EXE_NAME%.exe
pause

