#!/usr/bin/env python3
"""Sanity-checks the mod's defs without launching RimWorld.

Catches the mistakes that are silent until runtime:
  * malformed XML
  * a recreation building that no JoyGiverDef lists, so pawns never use it
    (a joyKind on a ThingDef is only a label)
  * a texPath with no matching file, or a Graphic_Multi missing a rotation
  * a jobDef/thingDef/research reference this mod makes but never defines
  * an animation comp whose frame textures are missing
  * a def declaring a comp its parent also declares (def inheritance APPENDS
    list entries, so that silently gives the building two of them)
  * XML naming a C# class this mod's source does not define, or naming one at
    all when the assembly has not been built

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

# --- comps declared by both a def and its parent chain ----------------------
def comp_classes(node):
    return [li.get("Class") for li in node.findall("./comps/li") if li.get("Class")]


for name, node in thing_defs.items():
    own = comp_classes(node)
    parent = node.get("ParentName")
    chain = []
    while parent in named:
        chain.append((parent, comp_classes(named[parent])))
        parent = named[parent].get("ParentName")
    for ancestor, inherited in chain:
        clash = sorted(set(own) & set(inherited))
        if clash:
            fail("%s and its parent %s both declare %s - inheritance appends "
                 "list entries, so the building would get two of each"
                 % (name, ancestor, ", ".join(clash)))

# --- C# classes named from XML, and their animation frames ------------------
SRC = os.path.join(ROOT, "Source", "EntertainingIdeas")
ASSEMBLIES = [os.path.join(ROOT, v, "Assemblies", "EntertainingIdeas.dll")
               for v in ("1.5", "1.6")]

source_classes = set()
if os.path.isdir(SRC):
    for filename in os.listdir(SRC):
        if filename.endswith(".cs"):
            with open(os.path.join(SRC, filename)) as handle:
                for line in handle:
                    stripped = line.strip()
                    if stripped.startswith("public class ") or stripped.startswith("public abstract class "):
                        source_classes.add(stripped.split("class ", 1)[1].split()[0].split(":")[0])

our_classes_used = set()
for folder, _, files in os.walk(DEFS):
    for filename in files:
        if not filename.endswith(".xml"):
            continue
        root = ET.parse(os.path.join(folder, filename)).getroot()
        for node in root.iter():
            for value in [node.get("Class"), node.text]:
                if value and value.strip().startswith("EntertainingIdeas."):
                    our_classes_used.add(value.strip().split(".", 1)[1])
        # Every frame strip referenced anywhere must be complete on disk.
        for node in root.iter():
            frame_path = node.findtext("framePath")
            if not frame_path:
                continue
            count_text = node.findtext("frameCount")
            count = int(count_text) if count_text else 0
            if count < 1:
                fail("%s: frameCount must be at least 1" % frame_path)
                continue
            missing = [i for i in range(count)
                       if not os.path.isfile(os.path.join(TEX, frame_path.replace("/", os.sep)) + "_%d.png" % i)]
            if missing:
                fail("%s: missing frame textures %s"
                     % (frame_path, ", ".join(str(i) for i in missing)))

for klass in sorted(our_classes_used):
    if klass not in source_classes:
        fail("XML names EntertainingIdeas.%s but no C# source defines it" % klass)
built = [a for a in ASSEMBLIES if os.path.isfile(a)]
if our_classes_used and len(built) < len(ASSEMBLIES):
    missing = [os.path.relpath(a, ROOT) for a in ASSEMBLIES if not os.path.isfile(a)]
    fail("XML names C# classes but these assemblies are missing: %s - run "
         "Source/build.sh (defs naming a missing class will not load)"
         % ", ".join(missing))

print("%d C# classes referenced from XML, %d/%d version assemblies built"
      % (len(our_classes_used), len(built), len(ASSEMBLIES)))
print("%d ThingDefs, %d JoyGiverDefs, %d JobDefs, %d ResearchProjectDefs"
      % (len(thing_defs), len(joy_givers), len(job_defs), len(research_defs)))
if problems:
    print("\nFAILED:")
    for line in problems:
        print("  - " + line)
    sys.exit(1)
print("All checks passed.")
