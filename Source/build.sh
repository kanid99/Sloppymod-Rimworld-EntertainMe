#!/usr/bin/env bash
# Builds the mod's assemblies, one per supported RimWorld version.
#
# 1.6 changed APIs this mod uses - JoyUtility.JoyTickCheckEnd takes the elapsed
# tick count now, and Toil gained tickIntervalAction - so a single DLL cannot
# serve both. Each version gets its own build from the same sources, guarded by
# #if RW16, and LoadFolders.xml points each game version at its own folder.
#
# Needs a C# compiler (mono-devel provides mcs) and network access to nuget.org
# for RimWorld's reference assemblies.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="${TMPDIR:-/tmp}/rimworld-refs"

fetch_refs() {
  local version="$1" dir="$WORK/$version"
  if [ ! -d "$dir/ref/net472" ]; then
    echo "Fetching RimWorld $version reference assemblies..." >&2
    mkdir -p "$dir"
    curl -sSL -o "$dir/refs.nupkg" \
      "https://api.nuget.org/v3-flatcontainer/krafs.rimworld.ref/$version/krafs.rimworld.ref.$version.nupkg"
    python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" \
      "$dir/refs.nupkg" "$dir" >&2
  fi
  echo "$dir/ref/net472"
}

build() {
  local version="$1" outdir="$2" defines="${3:-}"
  local refs; refs="$(fetch_refs "$version")"
  local args=(-target:library -langversion:latest -nostdlib -noconfig)
  [ -n "$defines" ] && args+=("-define:$defines")
  # 1.6's UnityEngine references netstandard types; 1.5's does not ship it.
  [ -f "$refs/netstandard.dll" ] && args+=("-r:$refs/netstandard.dll")

  mkdir -p "$ROOT/$outdir"
  echo "Compiling for $version -> $outdir"
  mcs "${args[@]}" \
    -out:"$ROOT/$outdir/EntertainingIdeas.dll" \
    -r:"$refs/mscorlib.dll" -r:"$refs/System.dll" -r:"$refs/System.Core.dll" \
    -r:"$refs/Assembly-CSharp.dll" -r:"$refs/UnityEngine.CoreModule.dll" \
    -r:"$refs/UnityEngine.dll" \
    "$ROOT/Source/EntertainingIdeas/"*.cs
}

build "${REF_15:-1.5.4409}" "1.5/Assemblies"
build "${REF_16:-1.6.4871}" "1.6/Assemblies" "RW16"
echo "Built both assemblies."
