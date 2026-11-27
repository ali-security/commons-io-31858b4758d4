#!/usr/bin/env python3
"""Print the Surefire test totals and every skipped test with its reason.

Reads target/surefire-reports/TEST-*.xml. For a JUnit assumption skip, whose
recorded message is only "assumption is not true", the assume line of the
test method is quoted from the test source as the reason.
"""
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET


def assume_line(classname, method):
    path = os.path.join("src", "test", "java", *classname.split(".")) + ".java"
    try:
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
    except OSError:
        return None
    m = re.search(r"void\s+" + re.escape(method) + r"\s*\(", src)
    if not m:
        return None
    a = re.search(r"(assume\w*\s*\(.*?\));", src[m.end():m.end() + 2000])
    return a.group(1) if a else None


def main():
    total = failures = errors = skipped = 0
    lines = []
    for f in sorted(glob.glob("target/surefire-reports/TEST-*.xml")):
        root = ET.parse(f).getroot()
        total += int(root.get("tests", 0))
        failures += int(root.get("failures", 0))
        errors += int(root.get("errors", 0))
        skipped += int(root.get("skipped", 0))
        for tc in root.iter("testcase"):
            sk = tc.find("skipped")
            if sk is None:
                continue
            reason = (sk.get("message") or (sk.text or "").strip() or "no message").splitlines()[0]
            if reason.startswith("Assumption failed"):
                cond = assume_line(tc.get("classname"), tc.get("name"))
                if cond:
                    reason = "%s: %s does not hold on this platform/JDK" % (reason, cond)
            elif reason.endswith("is @Disabled"):
                reason = "annotated @Disabled upstream"
            lines.append("SKIPPED %s.%s -- %s" % (tc.get("classname"), tc.get("name"), reason))
    print("==== Surefire summary: tests=%d passed=%d failures=%d errors=%d skipped=%d"
          % (total, total - failures - errors - skipped, failures, errors, skipped))
    for line in lines:
        print(line)
    return 0 if total > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
