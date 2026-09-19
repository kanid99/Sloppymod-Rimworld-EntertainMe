#!/usr/bin/env bash
# Builds Assemblies/EntertainingIdeas.dll.
#
# The only C# in this mod is the arcade screen animation. Everything else is
# XML and works without the assembly — but the cocktail table's ThingDef names
# the comp, so the DLL has to be present or that def will not load.
#
# Needs a C# compiler (mono-devel provides mcs; dotnet's csc works too) and
# network access to nuget.org for RimWorld's reference assemblies.
set -euo pipefail

REF_VERSION="${REF_VERSION:-1.5.4409}"   # 1.5 refs; the result runs on 1.5 and 1.6
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="${TMPDIR:-/tmp}/rimworld-refs-$REF_VERSION"
REFS="$WORK/ref/net472"

if [ ! -d "$REFS" ]; then
  echo "Fetching RimWorld $REF_VERSION reference assemblies..."
  mkdir -p "$WORK"
  curl -sSL -o "$WORK/refs.nupkg" \
    "https://api.nuget.org/v3-flatcontainer/krafs.rimworld.ref/$REF_VERSION/krafs.rimworld.ref.$REF_VERSION.nupkg"
  python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" \
    "$WORK/refs.nupkg" "$WORK"
fi

mkdir -p "$ROOT/Assemblies"
echo "Compiling..."
mcs -target:library -langversion:latest -nostdlib -noconfig \
  -out:"$ROOT/Assemblies/EntertainingIdeas.dll" \
  -r:"$REFS/mscorlib.dll" -r:"$REFS/System.dll" -r:"$REFS/System.Core.dll" \
  -r:"$REFS/Assembly-CSharp.dll" -r:"$REFS/UnityEngine.CoreModule.dll" \
  -r:"$REFS/UnityEngine.dll" \
  "$ROOT/Source/EntertainingIdeas/"*.cs

echo "Built $ROOT/Assemblies/EntertainingIdeas.dll"
