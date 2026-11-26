#!/usr/bin/env bash
set -euo pipefail
# Run from the same activated venv that you will use to launch Assignment Reader.
# Example: source ~/assignment-reader-env/bin/activate && bash setup_piper_voice.sh
PYTHON_BIN="${PYTHON:-python}"
VOICE_DIR="${HOME}/assignment-reader/voices"
echo "Installing Piper neural TTS (internet required for this one-time step)..."
"${PYTHON_BIN}" -m pip install 'piper-tts[http]'
mkdir -p "${VOICE_DIR}"
echo "Downloading English voice model into ${VOICE_DIR}..."
"${PYTHON_BIN}" -m piper.download_voices en_US-lessac-medium --data-dir "${VOICE_DIR}"
echo "Done. Start Assignment Reader from this same Python environment and select Piper neural voice."
