#!/usr/bin/env python3
"""Sanity-checks the mod's defs without launching RimWorld.

Catches the mistakes that are silent until runtime:
  * malformed XML
  * a recreation building that no JoyGiverDef lists, so pawns never use it
    (a joyKind on a ThingDef is only a label)
  * a texPath with no matching file, or a Graphic_Multi missing a rotation
  * a jobDef/thingDef/research reference this mod makes but never defines

Usage: python3 Source/validate.py
"""

import os
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DEFS = os.path.join(ROOT, "Defs")
TEX = os.path.join(ROOT, "Textures")

problems = []
thing_defs = {}      # defName -> element (concrete buildings)
named = {}           # Name="..." -> element (including Abstract parents)
joy_givers = []
job_defs = set()
research_defs = set()


def fail(msg):
    problems.append(msg)


for folder, _, files in os.walk(DEFS):
    for filename in sorted(files):
        if not filename.endswith(".xml"):
            continue
        path = os.path.join(folder, filename)
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            fail("%s: malformed XML (%s)" % (os.path.relpath(path, ROOT), exc))
            continue
        for node in root:
            name = node.findtext("defName")
            if node.tag == "ThingDef":
                if node.get("Name"):
                    named[node.get("Name")] = node
                if name:
                    thing_defs[name] = node
            elif node.tag == "JoyGiverDef":
                joy_givers.append(node)
            elif node.tag == "JobDef" and name:
                job_defs.add(name)
            elif node.tag == "ResearchProjectDef" and name:
                research_defs.add(name)

# --- every recreation building must be reachable through a JoyGiverDef ------
listed = {}
for giver in joy_givers:
    giver_name = giver.findtext("defName")
    for li in giver.findall("./thingDefs/li"):
        listed.setdefault(li.text, []).append(giver_name)
    job = giver.findtext("jobDef")
    if job and job.startswith("EI_") and job not in job_defs:
        fail("JoyGiverDef %s points at undefined jobDef %s" % (giver_name, job))

for name, node in thing_defs.items():
    if node.find("./building/joyKind") is None:
        continue
    if name not in listed:
        fail("%s has a joyKind but no JoyGiverDef lists it - pawns would never "
             "use it" % name)
    elif len(listed[name]) > 1:
        fail("%s is listed by several JoyGiverDefs: %s" % (name, listed[name]))

for name, givers in listed.items():
    if name not in thing_defs:
        fail("JoyGiverDef %s lists unknown ThingDef %s" % (givers[0], name))

# --- textures ---------------------------------------------------------------
for name, node in thing_defs.items():
    # graphicClass is often set once on an abstract parent, so walk up to it.
    tex = node.findtext("./graphicData/texPath")
    klass = node.findtext("./graphicData/graphicClass")
    parent = node.get("ParentName")
    while klass is None and parent in named:
        klass = named[parent].findtext("./graphicData/graphicClass")
        parent = named[parent].get("ParentName")
    if not tex:
        continue
    base = os.path.join(TEX, tex.replace("/", os.sep))
    if klass == "Graphic_Multi":
        missing = [r for r in ("north", "east", "south", "west")
                   if not os.path.isfile("%s_%s.png" % (base, r))]
        if missing:
            fail("%s: Graphic_Multi missing %s for %s"
                 % (name, ", ".join(missing), tex))
    elif not os.path.isfile(base + ".png"):
        fail("%s: no texture file for %s" % (name, tex))

# --- internal references ----------------------------------------------------
for name, node in thing_defs.items():
    for li in node.findall("./researchPrerequisites/li"):
        if li.text.startswith("EI_") and li.text not in research_defs:
            fail("%s requires undefined research %s" % (name, li.text))

for folder, _, files in os.walk(DEFS):
    for filename in files:
        if filename.endswith(".xml"):
            root = ET.parse(os.path.join(folder, filename)).getroot()
            for node in root.iter("prerequisites"):
                for li in node.findall("li"):
                    if li.text.startswith("EI_") and li.text not in research_defs:
                        fail("undefined research prerequisite %s" % li.text)

print("%d ThingDefs, %d JoyGiverDefs, %d JobDefs, %d ResearchProjectDefs"
      % (len(thing_defs), len(joy_givers), len(job_defs), len(research_defs)))
if problems:
    print("\nFAILED:")
    for line in problems:
        print("  - " + line)
    sys.exit(1)
print("All checks passed.")
