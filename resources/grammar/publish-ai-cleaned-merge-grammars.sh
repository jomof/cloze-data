#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <output_dir> <file1> [file2 …]"
  exit 1
fi

outdir=$1
shift

rm -rf "$outdir"
mkdir -p "$outdir"

for file in "$@"; do
  if [ -e "$file" ]; then
    cp "$file" "$outdir/"
  else
    echo "Warning: '$file' does not exist, skipping."
  fi
done
