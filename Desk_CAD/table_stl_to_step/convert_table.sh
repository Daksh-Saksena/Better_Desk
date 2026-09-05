#!/usr/bin/env bash

set -e

echo "========================================"
echo "Table STL -> STEP Converter"
echo "========================================"
echo ""

# Get script directory
PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "${PROJ_DIR}/final_table_1.5m.7z" ]; then
    ARCHIVE_FILE="${PROJ_DIR}/final_table_1.5m.7z"
else
    ARCHIVE_FILE="${PROJ_DIR}/final_table_1-5m.7z"
fi
EXTRACT_DIR="${PROJ_DIR}/input_extracted"
OUTPUT_DIR="${PROJ_DIR}/output"
BUILD_DIR="${PROJ_DIR}/build"
CONVERTER_DIR="${PROJ_DIR}/2STEP-Converter"
OUTPUT_STEP="${OUTPUT_DIR}/final_table_1-5m.step"

echo "[1/4] Preparing 2STEP Converter..."

# --- Check 7-Zip / Extractor ---
SEVENZIP=""
if command -v 7zz >/dev/null 2>&1; then
    SEVENZIP="7zz"
elif command -v 7z >/dev/null 2>&1; then
    SEVENZIP="7z"
elif [ -f "/opt/homebrew/bin/7zz" ]; then
    SEVENZIP="/opt/homebrew/bin/7zz"
elif [ -f "/usr/local/bin/7zz" ]; then
    SEVENZIP="/usr/local/bin/7zz"
fi

if [ -z "$SEVENZIP" ]; then
    echo "[ERROR] Stage 1 Failed: 7-Zip (7zz or 7z) was not found on your system."
    echo "Please install it via Homebrew ('brew install sevenzip') or manually add it to PATH."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# --- Check Source Code Directory ---
if [ ! -f "${CONVERTER_DIR}/src/converter.py" ]; then
    echo "[INFO] 2STEP Converter source code missing. Cloning from GitHub..."
    if ! command -v git >/dev/null 2>&1; then
        echo "[ERROR] Stage 1 Failed: Git is required to clone the repository, but git was not found."
        echo "Please install Git or manually place 2STEP Converter source inside \"${CONVERTER_DIR}\"."
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
    git clone https://github.com/yaneony/2STEP-Converter.git "${CONVERTER_DIR}"
    if [ $? -ne 0 ]; then
        echo "[ERROR] Stage 1 Failed: Git clone failed."
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

# --- Check Input Archive ---
if [ ! -f "${ARCHIVE_FILE}" ]; then
    echo "[ERROR] Stage 1 Failed: Input archive missing at \"${ARCHIVE_FILE}\"."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

mkdir -p "${BUILD_DIR}" "${OUTPUT_DIR}" "${EXTRACT_DIR}"

echo ""
echo "[2/4] Building 2STEP Converter environment..."

_MM_ROOT="${BUILD_DIR}"
_MM="${_MM_ROOT}/micromamba"
_ENV="${_MM_ROOT}/env"
_PY="${_ENV}/bin/python"
_SPEC="${CONVERTER_DIR}/src/environment.yml"

# Detect Mac Architecture (ARM64 Apple Silicon vs x86_64 Intel)
ARCH="$(uname -m)"
if [ "$ARCH" = "arm64" ]; then
    MM_URL="https://github.com/mamba-org/micromamba-releases/releases/download/2.8.1-1/micromamba-osx-arm64"
    _MM_SHA256="9618a2866a2ffb3d36b55e9520f64d63dcd6dc2e622a351ca3cbe8e2cc90c757"
else
    MM_URL="https://github.com/mamba-org/micromamba-releases/releases/download/2.8.1-1/micromamba-osx-64"
    _MM_SHA256="d6fce18e56d7c6bf2331b0ee1b372a581c70f09b509cc9e924cdd131e053b58a"
fi

export MAMBA_ROOT_PREFIX="${_MM_ROOT}"
export CONDA_PKGS_DIRS="${_MM_ROOT}"
export PYTHONNOUSERSITE=1
export PATH="${_ENV}/bin:${PATH}"

if [ ! -f "${_MM}" ]; then
    echo "Downloading portable Python environment manager (micromamba for macOS)..."
    curl -L --progress-bar -o "${_MM}" "${MM_URL}"
    if [ $? -ne 0 ]; then
        echo "[ERROR] Stage 2 Failed: Download of micromamba failed. Check internet connection."
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
    chmod +x "${_MM}"

    _HASH="$(shasum -a 256 "${_MM}" | awk '{print $1}')"
    if [ "${_HASH}" != "${_MM_SHA256}" ]; then
        echo "[ERROR] Stage 2 Failed: micromamba checksum verification failed."
        rm -f "${_MM}"
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

if [ ! -f "${_SPEC}" ]; then
    echo "[ERROR] Stage 2 Failed: Environment spec missing at \"${_SPEC}\"."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

_SPEC_HASH="$(shasum -a 256 "${_SPEC}" | awk '{print $1}')"
_SPEC_MARKER="${_ENV}/.2step-environment.sha256"

if [ -f "${_PY}" ]; then
    _INSTALLED_SPEC_HASH=""
    if [ -f "${_SPEC_MARKER}" ]; then
        _INSTALLED_SPEC_HASH="$(cat "${_SPEC_MARKER}")"
    fi
    if [ "${_INSTALLED_SPEC_HASH}" != "${_SPEC_HASH}" ]; then
        echo "Environment specification changed -- updating dependencies..."
        "${_MM}" install --prefix "${_ENV}" --file "${_SPEC}" --yes
        if [ $? -ne 0 ]; then
            echo "[ERROR] Stage 2 Failed: Environment update failed."
            echo ""
            read -p "Press Enter to exit..."
            exit 1
        fi
    fi
else
    echo "Creating standalone Python environment for 2STEP Converter (one-time setup)..."
    "${_MM}" create --prefix "${_ENV}" --file "${_SPEC}" --yes
    if [ $? -ne 0 ]; then
        echo "[ERROR] Stage 2 Failed: Python environment creation failed."
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

# Verification and dependency sanity check
if ! "${_PY}" -c "from OCC.Core.StlAPI import StlAPI_Reader; import numpy, trimesh, networkx, fast_simplification, matplotlib, open3d, PIL" >/dev/null 2>&1; then
    echo "Python environment dependencies incomplete -- repairing environment..."
    "${_MM}" install --prefix "${_ENV}" --file "${_SPEC}" --force-reinstall --yes
    if [ $? -ne 0 ]; then
        echo "[ERROR] Stage 2 Failed: Environment repair failed."
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
    if ! "${_PY}" -c "from OCC.Core.StlAPI import StlAPI_Reader; import numpy, trimesh, networkx, fast_simplification, matplotlib, open3d, PIL" >/dev/null 2>&1; then
        echo "[ERROR] Stage 2 Failed: Python environment verification failed after repair."
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

echo "${_SPEC_HASH}" > "${_SPEC_MARKER}"
echo "2STEP Converter environment ready."

# Configure 2STEP Converter to allow open surface shells and disable redundant validation
mkdir -p "${CONVERTER_DIR}/data"
cat << 'EOF' > "${CONVERTER_DIR}/data/config.json"
{
    "SEWING_TOLERANCE": 0.01,
    "DEFAULT_REDUCTION_PERCENT": 0,
    "AUTO_REDUCTION_ENABLED": true,
    "AUTO_REDUCTION_TARGET_TRIANGLES": 50000,
    "ASK_FOR_REDUCTION": true,
    "SKIP_UP_TO_DATE_OUTPUTS": true,
    "PLANAR_MERGE_ANGLE_RADIANS": 0.01,
    "SEWING_TIMEOUT_SECONDS": 3600,
    "SEW_PARTS_SEPARATELY": true,
    "DEFAULT_STEP_FORMAT": "ap203",
    "GENERATE_PNG_PREVIEW": true,
    "INPUT_FOLDER_NAME": "models",
    "CHECK_MESH_QUALITY": true,
    "REPAIR_MESH_BEFORE_CONVERSION": true,
    "VERTEX_MERGE_DISTANCE": 0.0,
    "FIX_TRIANGLE_ORIENTATION": true,
    "REMOVE_NON_MANIFOLD_TRIANGLES": false,
    "REJECT_NON_MANIFOLD_MESH": false,
    "FILL_SMALL_MESH_HOLES": false,
    "FILL_SMALL_PLANAR_BREP_GAPS": true,
    "MAX_BREP_GAP_EDGE_COUNT": 8,
    "MAX_BREP_GAP_AREA_RATIO": 0.005,
    "CHECK_SELF_INTERSECTIONS": true,
    "SELF_INTERSECTION_CHECK_MAX_TRIANGLES": 50000,
    "REJECT_SELF_INTERSECTING_MESH": false,
    "USE_SCALE_AWARE_SEWING_TOLERANCE": true,
    "SCALE_AWARE_SEWING_TOLERANCE_RATIO": 1e-06,
    "REQUIRE_SOLID_OUTPUT": false,
    "VALIDATE_STEP_AFTER_WRITING": false,
    "PRESERVE_BOUNDARIES_DURING_REDUCTION": true,
    "REDUCTION_BOUNDARY_WEIGHT": 10.0,
    "MAX_REDUCTION_SIZE_CHANGE_PERCENT": 10.0,
    "MAX_REDUCTION_VOLUME_CHANGE_PERCENT": 10.0,
    "EXPERIMENTAL_PARAMETRIC_RECONSTRUCTION": false,
    "EXPERIMENTAL_PARAMETRIC_FIT_ERROR_RATIO": 0.0005,
    "EXPERIMENTAL_PARAMETRIC_MAX_VOLUME_CHANGE_PERCENT": 0.1,
    "RECONSTRUCT_ANALYTIC_PRIMITIVES": true,
    "ANALYTIC_PRIMITIVE_FIT_ERROR_RATIO": 0.001,
    "ANALYTIC_PRIMITIVE_MIN_TRIANGLES": 32,
    "RECONSTRUCT_ANALYTIC_THROUGH_HOLES": true,
    "RECONSTRUCT_ANALYTIC_BLIND_HOLES": true,
    "ANALYTIC_HOLE_FIT_ERROR_RATIO": 0.002,
    "ANALYTIC_HOLE_MIN_SIDES": 12,
    "ANALYTIC_HOLE_MAX_RADIUS_DIFFERENCE_RATIO": 0.002,
    "ANALYTIC_HOLE_AXIS_TOLERANCE_RADIANS": 0.005,
    "ANALYTIC_HOLE_MAX_VOLUME_CHANGE_PERCENT": 0.1,
    "STL_FILE_EXTENSION": ".stl",
    "THREE_MF_FILE_EXTENSION": ".3mf",
    "OBJ_FILE_EXTENSION": ".obj",
    "IGES_FILE_EXTENSION": ".igs",
    "AMF_FILE_EXTENSION": ".amf",
    "STEP_FILE_EXTENSION": ".stp"
}
EOF

echo ""
echo "[3/4] Extracting STL from archive..."
echo "Archive: ${ARCHIVE_FILE}"
echo "Target:  ${EXTRACT_DIR}"

"${SEVENZIP}" x "${ARCHIVE_FILE}" -o"${EXTRACT_DIR}" -y >/dev/null
if [ $? -ne 0 ]; then
    echo "[ERROR] Stage 3 Failed: 7-Zip failed to extract \"${ARCHIVE_FILE}\"."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

FOUND_STL="$(find "${EXTRACT_DIR}" -type f \( -iname "*.stl" \) | head -n 1)"

if [ -z "${FOUND_STL}" ]; then
    echo "[ERROR] Stage 3 Failed: No .stl file found in extracted contents of \"${ARCHIVE_FILE}\"."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Found STL file: \"${FOUND_STL}\""

echo ""
echo "[4/4] Converting STL -> STEP..."
echo "Input STL:  \"${FOUND_STL}\""
echo "Output STEP: \"${OUTPUT_STEP}\""

"${_PY}" "${CONVERTER_DIR}/src/converter.py" "${FOUND_STL}" --output "${OUTPUT_STEP}" --reduce 80 --no-pause
if [ $? -ne 0 ]; then
    echo "[ERROR] Stage 4 Failed: Conversion from STL to STEP failed."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

if [ ! -f "${OUTPUT_STEP}" ]; then
    echo "[ERROR] Stage 4 Failed: Output file \"${OUTPUT_STEP}\" was not created."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "========================================"
echo "SUCCESS: STL converted to STEP successfully!"
echo "Output STEP file: \"${OUTPUT_STEP}\""
echo "========================================"
echo ""
read -p "Press Enter to continue..."
