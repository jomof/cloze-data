#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <output_dir> <file1> [file2 …]"
  exit 1
fi

outdir=$1
shift

# Recreate the output directory
rm -rf "$outdir"
mkdir -p "$outdir"

# Ensure the directory is writeable by everyone
chmod a+rwx "$outdir"

for file in "$@"; do
  if [ -e "$file" ]; then
    cp "$file" "$outdir/"
    # Make the copied file readable & writeable by all
    chmod a+rw "$outdir/$(basename "$file")"
  else
    echo "Warning: '$file' does not exist, skipping."
  fi
done
