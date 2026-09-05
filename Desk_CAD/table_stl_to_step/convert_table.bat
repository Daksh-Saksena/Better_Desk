@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

title Table STL to STEP Converter

set "PROJ_DIR=%~dp0"
if "%PROJ_DIR:~-1%"=="\" set "PROJ_DIR=%PROJ_DIR:~0,-1%"

set "ARCHIVE_FILE=%PROJ_DIR%\final_table_1-5m.7z"
set "EXTRACT_DIR=%PROJ_DIR%\input_extracted"
set "OUTPUT_DIR=%PROJ_DIR%\output"
set "BUILD_DIR=%PROJ_DIR%\build"
set "CONVERTER_DIR=%PROJ_DIR%\2STEP-Converter"
set "OUTPUT_STEP=%OUTPUT_DIR%\final_table_1-5m.step"

echo ========================================
echo Table STL -^> STEP Converter
echo ========================================
echo.

echo [1/4] Preparing 2STEP Converter...

rem --- Check 7-Zip Installation ---
set "SEVENZIP="
if exist "%ProgramFiles%\7-Zip\7z.exe" (
    set "SEVENZIP=%ProgramFiles%\7-Zip\7z.exe"
) else if exist "%ProgramFiles(x86)%\7-Zip\7z.exe" (
    set "SEVENZIP=%ProgramFiles(x86)%\7-Zip\7z.exe"
) else (
    where 7z.exe >nul 2>&1
    if !errorlevel! equ 0 set "SEVENZIP=7z.exe"
)

if not defined SEVENZIP (
    echo [ERROR] Stage 1 Failed: 7-Zip ^(7z.exe^) was not found on your system.
    echo Please install 7-Zip from https://www.7-zip.org/ and ensure it is installed in a standard path or added to PATH.
    echo.
    pause
    exit /b 1
)

rem --- Check Source Code Directory ---
if not exist "%CONVERTER_DIR%\src\converter.py" (
    echo [INFO] 2STEP Converter source code missing. Cloning from GitHub...
    where git.exe >nul 2>&1
    if !errorlevel! neq 0 (
        echo [ERROR] Stage 1 Failed: Git is required to clone the repository, but git.exe was not found.
        echo Please install Git or manually place 2STEP Converter source inside "%CONVERTER_DIR%".
        echo.
        pause
        exit /b 1
    )
    git clone https://github.com/yaneony/2STEP-Converter.git "%CONVERTER_DIR%"
    if !errorlevel! neq 0 (
        echo [ERROR] Stage 1 Failed: Git clone failed.
        echo.
        pause
        exit /b 1
    )
)

rem --- Check Input Archive ---
if not exist "%ARCHIVE_FILE%" (
    echo [ERROR] Stage 1 Failed: Input archive missing at "%ARCHIVE_FILE%".
    echo.
    pause
    exit /b 1
)

if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
if not exist "%EXTRACT_DIR%" mkdir "%EXTRACT_DIR%"

echo.
echo [2/4] Building 2STEP Converter environment...

set "_MM_ROOT=%BUILD_DIR%"
set "_MM=%_MM_ROOT%\micromamba.exe"
set "_ENV=%_MM_ROOT%\env"
set "_PY=%_ENV%\python.exe"
set "_SPEC=%CONVERTER_DIR%\src\environment.yml"
set "_MM_SHA256=b645a5259cb92b5869b0e60943390dd0d362cae45bc7e2f5ba8c7e4a4b06c7aa"
set "MAMBA_ROOT_PREFIX=%_MM_ROOT%"
set "CONDA_PKGS_DIRS=%_MM_ROOT%"
set "PYTHONNOUSERSITE=1"
set "PATH=%_ENV%\Library\bin;%_ENV%\Library\mingw-w64\bin;%_ENV%\Scripts;%_ENV%;%PATH%"

if exist "%_MM%" goto :check_env

echo Downloading portable Python environment manager (micromamba)...
curl.exe --ssl-no-revoke -L --progress-bar -o "%_MM%" "https://github.com/mamba-org/micromamba-releases/releases/download/2.8.1-1/micromamba-win-64.exe"
if !errorlevel! neq 0 (
    echo [ERROR] Stage 2 Failed: Download of micromamba.exe failed. Check internet connection.
    echo.
    pause
    exit /b 1
)

set "_HASH="
for /f "skip=1 delims=" %%H in ('%SystemRoot%\System32\certutil.exe -hashfile "%_MM%" SHA256') do if not defined _HASH set "_HASH=%%H"
if not defined _HASH (
    echo [ERROR] Stage 2 Failed: Could not calculate checksum of micromamba.exe.
    if exist "%_MM%" del /f /q "%_MM%"
    echo.
    pause
    exit /b 1
)
set "_HASH=!_HASH: =!"
if /i not "!_HASH!"=="%_MM_SHA256%" (
    echo [ERROR] Stage 2 Failed: micromamba checksum verification failed.
    if exist "%_MM%" del /f /q "%_MM%"
    echo.
    pause
    exit /b 1
)

:check_env
if not exist "%_SPEC%" (
    echo [ERROR] Stage 2 Failed: Environment spec missing at "%_SPEC%".
    echo.
    pause
    exit /b 1
)

set "_SPEC_HASH="
for /f "skip=1 delims=" %%H in ('%SystemRoot%\System32\certutil.exe -hashfile "%_SPEC%" SHA256') do if not defined _SPEC_HASH set "_SPEC_HASH=%%H"
set "_SPEC_HASH=!_SPEC_HASH: =!"
set "_SPEC_MARKER=%_ENV%\.2step-environment.sha256"

if exist "%_PY%" (
    set "_INSTALLED_SPEC_HASH="
    if exist "%_SPEC_MARKER%" set /p _INSTALLED_SPEC_HASH=<"%_SPEC_MARKER%"
    if /i not "!_INSTALLED_SPEC_HASH!"=="!_SPEC_HASH!" (
        echo Environment specification changed -- updating dependencies...
        "%_MM%" install --prefix "%_ENV%" --file "%_SPEC%" --yes
        if !errorlevel! neq 0 (
            echo [ERROR] Stage 2 Failed: Environment update failed.
            echo.
            pause
            exit /b 1
        )
    )
    goto :check_deps
)

echo Creating standalone Python environment for 2STEP Converter (one-time setup)...
"%_MM%" create --prefix "%_ENV%" --file "%_SPEC%" --yes
if !errorlevel! neq 0 (
    echo [ERROR] Stage 2 Failed: Python environment creation failed.
    echo.
    pause
    exit /b 1
)

:check_deps
"%_PY%" -c "from OCC.Core.StlAPI import StlAPI_Reader; import numpy, trimesh, networkx, fast_simplification, matplotlib, open3d, PIL" >nul 2>&1
if !errorlevel! neq 0 (
    echo Python environment dependencies incomplete -- repairing environment...
    "%_MM%" install --prefix "%_ENV%" --file "%_SPEC%" --force-reinstall --yes
    if !errorlevel! neq 0 (
        echo [ERROR] Stage 2 Failed: Environment repair failed.
        echo.
        pause
        exit /b 1
    )
    "%_PY%" -c "from OCC.Core.StlAPI import StlAPI_Reader; import numpy, trimesh, networkx, fast_simplification, matplotlib, open3d, PIL" >nul 2>&1
    if !errorlevel! neq 0 (
        echo [ERROR] Stage 2 Failed: Python environment verification failed after repair.
        echo.
        pause
        exit /b 1
    )
)

> "%_SPEC_MARKER%" echo !_SPEC_HASH!
echo 2STEP Converter environment ready.

echo.
echo [3/4] Extracting STL from archive...
echo Archive: %ARCHIVE_FILE%
echo Target:  %EXTRACT_DIR%

"%SEVENZIP%" x "%ARCHIVE_FILE%" -o"%EXTRACT_DIR%" -y >nul
if !errorlevel! neq 0 (
    echo [ERROR] Stage 3 Failed: 7-Zip failed to extract "%ARCHIVE_FILE%".
    echo.
    pause
    exit /b 1
)

set "FOUND_STL="
for /r "%EXTRACT_DIR%" %%F in (*.stl *.STL) do (
    if not defined FOUND_STL set "FOUND_STL=%%~fF"
)

if not defined FOUND_STL (
    echo [ERROR] Stage 3 Failed: No .stl file found in extracted contents of "%ARCHIVE_FILE%".
    echo.
    pause
    exit /b 1
)

echo Found STL file: "!FOUND_STL!"

echo.
echo [4/4] Converting STL -^> STEP...
echo Input STL:  "!FOUND_STL!"
echo Output STEP: "%OUTPUT_STEP%"

"%_PY%" "%CONVERTER_DIR%\src\converter.py" "!FOUND_STL!" --output "%OUTPUT_STEP%" --reduce 0 --no-pause
if !errorlevel! neq 0 (
    echo [ERROR] Stage 4 Failed: Conversion from STL to STEP failed.
    echo.
    pause
    exit /b 1
)

if not exist "%OUTPUT_STEP%" (
    echo [ERROR] Stage 4 Failed: Output file "%OUTPUT_STEP%" was not created.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS: STL converted to STEP successfully!
echo Output STEP file: "%OUTPUT_STEP%"
echo ========================================
echo.
pause
