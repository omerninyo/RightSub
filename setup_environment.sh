#!/bin/bash
# ==============================================================================
# Subtitle Toolkit Master - Environment Setup Script
# ==============================================================================
set -e

echo "=== [1/4] Checking System & Homebrew ==="
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found! Please install Homebrew from https://brew.sh/"
        exit 1
    fi
    echo "Homebrew detected."
fi

echo "=== [2/4] Checking & Installing FFmpeg ==="
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg not found. Installing via Homebrew/apt..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ffmpeg
    elif command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y ffmpeg
    else
        echo "Please install ffmpeg manually for your OS."
        exit 1
    fi
else
    echo "FFmpeg is already installed: $(ffmpeg -version | head -n 1)"
fi

echo "=== [3/4] Checking Python3 & Installing Dependencies ==="
if ! command -v python3 &> /dev/null; then
    echo "python3 not found. Please install Python 3.9+."
    exit 1
fi

pip_cmd="pip3"
if ! command -v pip3 &> /dev/null; then
    pip_cmd="python3 -m pip"
fi

echo "Installing required Python packages: srt, pysubs2, requests, regex..."
$pip_cmd install --quiet --upgrade srt pysubs2 requests regex

echo "=== [4/4] Setting Permissions ==="
chmod +x "$scripts_dir"/*.py 2>/dev/null || true

echo "=================================================================="
echo " Environment setup complete! All tools and libraries are ready. "
echo "=================================================================="
