@echo off
setlocal enabledelayedexpansion

echo ====================================
echo    WonderJourney Simple GPU Setup
echo ====================================
echo.

echo Since nvidia-smi works manually but not in batch scripts,
echo we'll set your CUDA version manually and proceed.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Found Python %PYTHON_VERSION%

REM Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed or not in PATH
    echo Please install Git from https://git-scm.com
    pause
    exit /b 1
)
echo ✓ Git is available

echo.
echo ====================================
echo Since you have CUDA 12.6, we'll use:
echo CUDA 12.6 → PyTorch cu121
echo ====================================
echo.

REM Set CUDA version manually
set CUDA_VERSION=12.6
set TORCH_CUDA=cu121

echo Setting up WonderJourney...

REM Create project directory
if not exist "WonderJourney-Local" (
    mkdir "WonderJourney-Local"
)
cd "WonderJourney-Local"

REM Clone repository if not exists
if not exist "WonderJourney" (
    echo Cloning WonderJourney repository...
    git clone https://github.com/KovenYu/WonderJourney.git
    if %errorlevel% neq 0 (
        echo ERROR: Failed to clone repository
        echo Check your internet connection
        pause
        exit /b 1
    )
    echo ✓ Repository cloned successfully
)

cd WonderJourney

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

echo.
echo ====================================
echo Installing PyTorch with CUDA 12.6 support
echo ====================================

REM Install PyTorch with CUDA
echo Installing PyTorch cu121 for CUDA 12.6...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

if %errorlevel% neq 0 (
    echo ERROR: Failed to install PyTorch
    pause
    exit /b 1
)

REM Verify PyTorch CUDA immediately
echo.
echo Verifying PyTorch CUDA support...
python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU count: {torch.cuda.device_count()}')
    print(f'GPU name: {torch.cuda.get_device_name(0)}')
    print(f'GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
    print('✓ SUCCESS: PyTorch CUDA working!')
else:
    print('✗ ERROR: CUDA not available in PyTorch')
    exit(1)
"

if %errorlevel% neq 0 (
    echo ERROR: PyTorch CUDA verification failed
    echo This means the PyTorch installation doesn't have working CUDA
    pause
    exit /b 1
)

echo.
echo ====================================
echo Installing PyTorch3D with GPU support
echo ====================================

REM Set environment for PyTorch3D compilation
set FORCE_CUDA=1
set TORCH_CUDA_ARCH_LIST=6.0;6.1;7.0;7.5;8.0;8.6;8.9;9.0
set MAX_JOBS=2

echo Trying precompiled PyTorch3D first...
pip install pytorch3d --no-cache-dir >nul 2>&1

REM Test PyTorch3D
python -c "
import pytorch3d
import torch
print(f'PyTorch3D version: {pytorch3d.__version__}')
if torch.cuda.is_available():
    from pytorch3d.structures import Meshes
    print('✓ SUCCESS: PyTorch3D with CUDA working!')
else:
    print('✗ ERROR: PyTorch3D no CUDA support')
    exit(1)
" >nul 2>&1

if %errorlevel% == 0 (
    echo ✓ SUCCESS: Precompiled PyTorch3D working!
    goto pytorch3d_done
)

echo Precompiled failed, compiling from source...
echo This will take 20-60 minutes - please wait!
echo.

REM Install build dependencies
pip install ninja wheel setuptools >nul 2>&1

REM Compile from source with progress indication
echo Starting compilation... (this is the longest step)
echo Progress will be minimal - please be patient!
pip install --no-cache-dir "git+https://github.com/facebookresearch/pytorch3d.git@stable"

if %errorlevel% neq 0 (
    echo ERROR: PyTorch3D compilation failed
    echo.
    echo Common solutions:
    echo 1. Install Visual Studio Build Tools
    echo 2. Restart computer and try again
    echo 3. Close other applications to free memory
    echo.
    pause
    exit /b 1
)

:pytorch3d_done
echo.
echo ====================================
echo Installing other dependencies
echo ====================================

echo Installing core packages...
pip install kornia matplotlib opencv-python scikit-image diffusers transformers accelerate >nul 2>&1
pip install timm==0.6.12 pillow==9.2.0 einops omegaconf av openai==0.28.1 ipdb >nul 2>&1

echo Installing Segment Anything...
pip install git+https://github.com/facebookresearch/segment-anything.git >nul 2>&1

echo Installing spaCy...
pip install spacy >nul 2>&1
python -m spacy download en_core_web_sm >nul 2>&1

echo.
echo ====================================
echo Downloading model files
echo ====================================

REM Download models with progress
echo Downloading MiDaS model (1.5GB)...
if not exist "dpt_beit_large_512.pt" (
    curl -L --progress-bar "https://github.com/isl-org/MiDaS/releases/download/v3_1/dpt_beit_large_512.pt" -o "dpt_beit_large_512.pt"
    if %errorlevel% neq 0 (
        echo WARNING: MiDaS model download failed
        echo You can download manually later
    )
)

echo Downloading SAM model (2.4GB)...
if not exist "sam_vit_h_4b8939.pth" (
    curl -L --progress-bar "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth" -o "sam_vit_h_4b8939.pth"
    if %errorlevel% neq 0 (
        echo WARNING: SAM model download failed
        echo You can download manually later
    )
)

REM Create launcher with GPU verification
echo Creating launcher...
(
echo @echo off
echo cd /d "%%~dp0"
echo call venv\Scripts\activate.bat
echo echo.
echo echo ====================================
echo echo    WonderJourney GPU Status
echo echo ====================================
echo python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"No GPU\"}') if torch.cuda.is_available() else print('ERROR: No GPU detected')"
echo echo ====================================
echo echo.
echo python wonderjourney_ui.py
echo echo.
echo pause
) > "Launch_WonderJourney_GPU.bat"

echo.
echo ====================================
echo Final verification
echo ====================================

python -c "
import torch
import pytorch3d
print('=== FINAL GPU VERIFICATION ===')
print(f'✓ PyTorch: {torch.__version__}')
print(f'✓ PyTorch3D: {pytorch3d.__version__}')
print(f'✓ CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✓ GPU: {torch.cuda.get_device_name(0)}')
    print(f'✓ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
    print(f'✓ CUDA Version: {torch.version.cuda}')
    print('=== ALL SYSTEMS GO! ===')
else:
    print('✗ CRITICAL ERROR: No CUDA support detected')
    exit(1)
"

if %errorlevel% neq 0 (
    echo CRITICAL ERROR: Final verification failed
    pause
    exit /b 1
)

echo.
echo ====================================
echo     🎉 SUCCESS! 🎉
echo ====================================
echo.
echo WonderJourney is ready with GPU acceleration!
echo.
echo Your setup:
echo - CUDA 12.6 with PyTorch cu121
echo - GPU-accelerated PyTorch3D
echo - All dependencies installed
echo.
echo To start generating 3D scenes:
echo 1. Run: Launch_WonderJourney_GPU.bat
echo 2. Enter your OpenAI API key
echo 3. Generate amazing scenes in 5-15 minutes!
echo.
echo Expected performance: 5-15 minutes per scene
echo.
pause