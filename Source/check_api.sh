#!/usr/bin/env bash
# Checks the mod against every RimWorld version it claims to support.
#
# Two things can break across versions and neither shows up until the game
# loads: a C# API that changed shape (1.6 added a parameter to
# JoyUtility.JoyTickCheckEnd, which would have thrown at runtime on a 1.5-built
# assembly), and a class named from XML that no longer exists.
#
#   ./Source/check_api.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="${TMPDIR:-/tmp}/rimworld-refs"
VERSIONS="${VERSIONS:-1.5.4409 1.6.4871}"
fail=0

for version in $VERSIONS; do
  dir="$WORK/$version"
  if [ ! -d "$dir/ref/net472" ]; then
    echo "Fetching RimWorld $version reference assemblies..."
    mkdir -p "$dir"
    curl -sSL -o "$dir/refs.nupkg" \
      "https://api.nuget.org/v3-flatcontainer/krafs.rimworld.ref/$version/krafs.rimworld.ref.$version.nupkg"
    python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" \
      "$dir/refs.nupkg" "$dir"
  fi
  refs="$dir/ref/net472"

  echo "== RimWorld $version =="
  # Class names the XML asks the game to construct. A typo or a removed class
  # here means the def silently fails to load.
  strings -n 3 "$refs/Assembly-CSharp.dll" > "$dir/strings.txt"
  while read -r name; do
    [ -z "$name" ] && continue
    case "$name" in EntertainingIdeas.*) continue ;; esac
    short="${name##*.}"
    if ! grep -qx "$short" "$dir/strings.txt"; then
      echo "  MISSING CLASS: $name"
      fail=1
    fi
  done < <(grep -rhoE '(Class="|<driverClass>|<giverClass>|<compClass>|<graphicClass>|<li>PlaceWorker_)[A-Za-z_.]+' "$ROOT/Defs" \
             | sed -E 's/.*(Class="|<driverClass>|<giverClass>|<compClass>|<graphicClass>|<li>)//' | tr -d '"' | sort -u)
  echo "  XML class references: ok"
done

if [ "$fail" -ne 0 ]; then
  echo "FAILED"
  exit 1
fi
echo "All versions check out. (Source/build.sh compiling cleanly for each"
echo "version is the matching check for the C# side.)"
