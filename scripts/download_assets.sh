#!/bin/bash
# Download the MoD Semantic Search media assets from S3 into ./sample_data
#
# The backend can also fetch files from S3 lazily at request time (see
# app/storage.py), so this bulk download is optional. Run it if you want all
# assets available offline, or to seed the database from local files.
#
# Requirements:
#   - AWS CLI v2 (https://aws.amazon.com/cli/)
#   - AWS credentials with read access to the bucket (aws configure)
#
# Usage:
#   ./scripts/download_assets.sh
#
# Environment overrides:
#   S3_BUCKET   (default: mod-semantic-demo)
#   S3_PREFIX   (default: sample_data)
#   DEST_DIR    (default: <repo>/sample_data)

set -euo pipefail

S3_BUCKET="${S3_BUCKET:-mod-semantic-demo}"
S3_PREFIX="${S3_PREFIX:-sample_data}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST_DIR="${DEST_DIR:-$REPO_ROOT/sample_data}"

if ! command -v aws >/dev/null 2>&1; then
    echo "❌ AWS CLI not found. Install it: https://aws.amazon.com/cli/"
    exit 1
fi

echo "📦 Downloading assets"
echo "   from: s3://${S3_BUCKET}/${S3_PREFIX}/"
echo "   to:   ${DEST_DIR}"
echo ""

mkdir -p "$DEST_DIR"
aws s3 sync "s3://${S3_BUCKET}/${S3_PREFIX}/" "$DEST_DIR/"

echo ""
echo "✅ Done. $(find "$DEST_DIR" -type f | wc -l) files in ${DEST_DIR}"
