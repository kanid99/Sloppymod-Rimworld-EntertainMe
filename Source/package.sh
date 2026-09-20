#!/usr/bin/env bash
#
# Builds a release zip that says what it is.
#
# Every zip handed over until now was anonymous: nothing inside it recorded
# which commit it came from, so "is this the build with X in it?" could only be
# answered by guessing. This stamps the commit, the date and a monotonic build
# number into About.xml, so the mod list in game shows exactly which build is
# installed, and BUILD.txt inside the folder repeats it for grepping.
#
# It also refuses to ship a zip whose contents contradict the mod's claims -
# see the checks at the bottom.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/EntertainingIdeas.zip}"
cd "$ROOT"

if [ -n "$(git status --porcelain)" ]; then
  echo "refusing to package: the working tree has uncommitted changes, so the" >&2
  echo "stamped commit would not describe what is actually in the zip." >&2
  git status --short >&2
  exit 1
fi

SHA="$(git rev-parse --short HEAD)"
DATE="$(git log -1 --format=%cd --date=format:%Y-%m-%d)"
BUILD="$(git rev-list --count HEAD)"
VERSION="0.9.$BUILD"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/EntertainingIdeas"
git archive HEAD | tar -x -C "$STAGE/EntertainingIdeas"
rm -rf "$STAGE/EntertainingIdeas/Source" "$STAGE/EntertainingIdeas/.gitignore"

python3 - "$STAGE/EntertainingIdeas/About/About.xml" "$VERSION" "$DATE" "$SHA" <<'PY'
import sys
path, version, date, sha = sys.argv[1:5]
s = open(path, encoding="utf-8").read()
stamp = "%s (%s, %s)" % (version, date, sha)
if "<modVersion>" in s:
    import re
    s = re.sub(r"<modVersion>.*?</modVersion>",
               "<modVersion>%s</modVersion>" % stamp, s, flags=re.S)
else:
    s = s.replace("</packageId>", "</packageId>\n  <modVersion>%s</modVersion>" % stamp, 1)
# Repeat it at the top of the description, which is what the mod info panel shows.
s = s.replace("<description>", "<description>Build %s\n\n" % stamp, 1)
open(path, "w", encoding="utf-8").write(s)
PY

cat > "$STAGE/EntertainingIdeas/BUILD.txt" <<TXT
Entertaining Ideas
version : $VERSION
built   : $DATE
commit  : $SHA
TXT

rm -f "$OUT"
(cd "$STAGE" && zip -qr "$OUT" EntertainingIdeas)

# --- what shipped, checked rather than assumed ------------------------------
# Claiming "no new research" is easy; a stale def file surviving in a zip is
# exactly the sort of thing nobody notices until it is in someone's game.
fail=0
if grep -rl "ResearchProjectDef>" "$STAGE/EntertainingIdeas/Defs" >/dev/null 2>&1; then
  echo "FAIL: this mod claims to add no research, but the zip defines some:" >&2
  grep -rl "ResearchProjectDef>" "$STAGE/EntertainingIdeas/Defs" >&2
  fail=1
fi
for want in About/About.xml Defs 1.5/Assemblies/EntertainingIdeas.dll \
            1.6/Assemblies/EntertainingIdeas.dll LoadFolders.xml; do
  if [ ! -e "$STAGE/EntertainingIdeas/$want" ]; then
    echo "FAIL: zip is missing $want" >&2
    fail=1
  fi
done
if [ -e "$STAGE/EntertainingIdeas/Source" ]; then
  echo "FAIL: Source/ leaked into the zip" >&2
  fail=1
fi
[ "$fail" -eq 0 ] || { rm -f "$OUT"; exit 1; }

echo "$OUT"
echo "  version $VERSION  ($DATE, $SHA)"
echo "  $(unzip -l "$OUT" | tail -1 | awk '{print $2}') files"
echo "  research defs: none"
