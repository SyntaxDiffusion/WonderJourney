@echo off
setlocal enabledelayedexpansion

echo ====================================
echo    WonderJourney Quick Launcher
echo ====================================
echo.

REM Check if we're in the right directory
if not exist "run.py" (
    echo ERROR: This script must be run from the WonderJourney directory
    echo Please navigate to the WonderJourney folder and run again.
    pause
    exit /b 1
)

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found. Using system Python.
)

REM Create config directories if missing
if not exist "config" mkdir config
if not exist "config\more_examples" mkdir config\more_examples
REM Also create the base outputs directory if it might be used directly
if not exist "outputs" mkdir outputs
if not exist "outputs\wonderjourney" mkdir "outputs\wonderjourney"


REM Create config files if missing
if not exist "config\more_examples\library.yaml" (
    echo Creating default library.yaml...
    (
    echo scene_name: ['Library interior']
    echo entities: ['ancient bookshelves', 'reading tables', 'warm lighting']
    echo background: ['Cozy academic atmosphere with leather-bound books']
    echo runs_dir: 'outputs/wonderjourney'
    ) > "config\more_examples\library.yaml"
)

if not exist "config\more_examples\kitchen.yaml" (
    echo Creating default kitchen.yaml...
    (
    echo scene_name: ['Modern kitchen']
    echo entities: ['marble countertops', 'steel appliances', 'pendant lights']
    echo background: ['Clean modern design with natural lighting']
    echo runs_dir: 'outputs/wonderjourney'
    ) > "config\more_examples\kitchen.yaml"
)

if not exist "config\more_examples\garden.yaml" (
    echo Creating default garden.yaml...
    (
    echo scene_name: ['Garden scene']
    echo entities: ['colorful flowers', 'stone pathways', 'water fountain']
    echo background: ['Peaceful outdoor setting with natural sunlight']
    echo runs_dir: 'outputs/wonderjourney'
    ) > "config\more_examples\garden.yaml"
)

REM Try to download models if missing (optional - won't stop script if it fails)
if not exist "dpt_beit_large_512.pt" (
    echo MiDaS model missing - attempting download...
    curl -L "https://github.com/isl-org/MiDaS/releases/download/v3_1/dpt_beit_large_512.pt" -o "dpt_beit_large_512.pt" 2>nul
    if exist "dpt_beit_large_512.pt" (
        echo ✓ MiDaS downloaded
    ) else (
        echo Download failed - you can download manually later
    )
)

if not exist "sam_vit_h_4b8939.pth" (
    echo SAM model missing - attempting download...
    curl -L "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth" -o "sam_vit_h_4b8939.pth" 2>nul
    if exist "sam_vit_h_4b8939.pth" (
        echo ✓ SAM downloaded
    ) else (
        echo Download failed - you can download manually later
    )
)

REM Check for API key
if not defined OPENAI_API_KEY (
    echo.
    echo OpenAI API Key is required for WonderJourney.
    set /p api_key="Enter your OpenAI API key: "
    set "OPENAI_API_KEY=!api_key!"
    if not defined OPENAI_API_KEY (
        echo ERROR: No API key provided. Exiting.
        pause
        exit /b 1
    )
)

echo.
echo Available options:
echo 1. Run with GUI (recommended)
echo 2. Quick generate: Library scene
echo 3. Quick generate: Kitchen scene  
echo 4. Quick generate: Garden scene
echo 5. Custom scene description
echo 6. Use existing config file
echo.

set "choice="
set /p choice="Enter your choice (1-6): "

set "PYTHON_CMD_TO_RUN="
set "PYTHON_ARGS="

if "%choice%"=="1" (
    echo Starting GUI...
    set "PYTHON_CMD_TO_RUN=python wonderjourney_ui.py"
) else if "%choice%"=="2" (
    echo Generating library scene...
    set "PYTHON_CMD_TO_RUN=python run.py"
    set "PYTHON_ARGS=--example_config "config/more_examples/library.yaml""
) else if "%choice%"=="3" (
    echo Generating kitchen scene...
    set "PYTHON_CMD_TO_RUN=python run.py"
    set "PYTHON_ARGS=--example_config "config/more_examples/kitchen.yaml""
) else if "%choice%"=="4" (
    echo Generating garden scene...
    set "PYTHON_CMD_TO_RUN=python run.py"
    set "PYTHON_ARGS=--example_config "config/more_examples/garden.yaml""
) else if "%choice%"=="5" (
    set "description="
    set /p description="Enter scene description: "
    if not defined description (
        echo No description entered. Aborting.
        goto end_script_pause
    )
    echo Generating custom scene: !description!
    
    REM Create temporary config
    (
    echo scene_name: ['!description!']
    echo entities: []
    echo background: []
    echo runs_dir: 'outputs/wonderjourney'
    ) > "temp_custom.yaml"
    
    set "PYTHON_CMD_TO_RUN=python run.py"
    set "PYTHON_ARGS=--example_config "temp_custom.yaml""
    REM We will delete temp_custom.yaml after the python command runs
) else if "%choice%"=="6" (
    set "config_path="
    set /p config_path="Enter config file path: "
    if not defined config_path (
        echo No config path entered. Aborting.
        goto end_script_pause
    )
    REM Remove quotes if user accidentally added them
    set "config_path=!config_path:"=!"

    if exist "!config_path!" (
        echo Using config: !config_path!
        set "PYTHON_CMD_TO_RUN=python run.py"
        set "PYTHON_ARGS=--example_config "!config_path!""
    ) else (
        echo ERROR: Config file not found: "!config_path!"
        goto end_script_pause
    )
) else (
    echo Invalid choice. "%choice%". Please run again and select 1-6.
    goto end_script_pause
)

REM Execute the Python command if one was set
if defined PYTHON_CMD_TO_RUN (
    echo.
    echo Attempting to run: !PYTHON_CMD_TO_RUN! !PYTHON_ARGS!
    echo ----------------------------------------------------------------------
    !PYTHON_CMD_TO_RUN! !PYTHON_ARGS!
    IF ERRORLEVEL 1 (
        echo ----------------------------------------------------------------------
        echo.
        echo PYTHON SCRIPT FAILED! (Error Level %ERRORLEVEL%)
        echo Please check for any messages printed above by the Python script.
        echo If no messages, the Python script may have crashed silently or exited due to an internal error.
        echo You can try running the command directly in an activated venv:
        echo   !PYTHON_CMD_TO_RUN! !PYTHON_ARGS!
        echo.
    ) else (
        echo ----------------------------------------------------------------------
        echo.
        echo Python script execution finished. (Error Level %ERRORLEVEL%)
    )
    REM Clean up temp file for option 5
    if "%choice%"=="5" (
        if exist "temp_custom.yaml" (
            echo Deleting temporary config file: temp_custom.yaml
            del "temp_custom.yaml"
        )
    )
)

:end_script_pause
echo.
echo Script operations complete. Check outputs folder if generation was successful.
pause
endlocal
exit /b %ERRORLEVEL%

REM Note: Removed 'goto end' from individual choices to centralize the python execution and error checking.
REM The script will now flow to the PYTHON_CMD_TO_RUN block if a valid choice is made.
REM The final 'endlocal' and 'exit /b %ERRORLEVEL%' will be hit after the pause.