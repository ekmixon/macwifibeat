from __future__ import print_function

import glob
import os
import datetime
import argparse
import json
import csv
import re


def read_file(filename):

    if not os.path.isfile(filename):
        print(f"File not found {filename}")
        return ""

    try:
        with open(filename, 'r') as f:
            return f.read()
    except UnicodeDecodeError:
        # try latin-1
        with open(filename, 'r', encoding="ISO-8859-1") as f:
            return f.read()


def get_library_path(license):
    """
    Get the contents up to the vendor folder.
    """
    split = license.split(os.sep)
    return next(
        (
            "/".join(split[i + 1 :])
            for i, word in reversed(list(enumerate(split)))
            if word == "vendor"
        ),
        "/".join(split),
    )


def read_versions(vendor):
    libs = []
    with open(os.path.join(vendor, "vendor.json")) as f:
        govendor = json.load(f)
        libs.extend(iter(govendor["package"]))
    return libs


def gather_dependencies(vendor_dirs, overrides=None):
    dependencies = {}   # lib_path -> [array of lib]
    for vendor in vendor_dirs:
        libs = read_versions(vendor)

        # walk looking for LICENSE files
        for root, dirs, filenames in os.walk(vendor):
            licenses = get_licenses(root)
            for filename in licenses:
                lib_path = get_library_path(root)
                if lib_search := [
                    l for l in libs if l["path"].startswith(lib_path)
                ]:
                    lib = lib_search[0]
                else:
                    print(f"WARNING: No version information found for: {lib_path}")
                    lib = {"path": lib_path}
                lib["license_file"] = os.path.join(root, filename)

                lib["license_contents"] = read_file(lib["license_file"])
                lib["license_summary"] = detect_license_summary(lib["license_contents"])
                if lib["license_summary"] == "UNKNOWN":
                    print(f"WARNING: Unknown license for: {lib_path}")

                if revision := overrides.get(lib_path, {}).get("revision"):
                    lib["revision"] = revision

                if lib_path not in dependencies:
                    dependencies[lib_path] = [lib]
                else:
                    dependencies[lib_path].append(lib)

            # don't walk down into another vendor dir
            if "vendor" in dirs:
                dirs.remove("vendor")
    return dependencies


def get_licenses(folder):
    """
    Get a list of license files from a given directory.
    """
    licenses = []
    for filename in sorted(os.listdir(folder)):
        if filename.startswith("LICENSE") and "docs" not in filename:
            licenses.append(filename)
        elif filename.startswith("APLv2"):  # gorhill/cronexpr
            licenses.append(filename)
    return licenses


def has_license(folder):
    """
    Checks if a particular repo has a license files.

    There are two cases accepted:
        * The folder contains a LICENSE
        * The folder only contains subdirectories AND all these
          subdirectories contain a LICENSE
    """
    if len(get_licenses(folder)) > 0:
        return True, ""

    for subdir in os.listdir(folder):
        if not os.path.isdir(os.path.join(folder, subdir)):
            return False, folder
        if len(get_licenses(os.path.join(folder, subdir))) == 0:
            return False, os.path.join(folder, subdir)
    return True, ""


def check_all_have_license_files(vendor_dirs):
    """
    Checks that everything in the vendor folders has a license one way
    or the other. This doesn't collect the licenses, because the code that
    collects the licenses needs to walk the full tree. This one makes sure
    that every folder in the `vendor` directories has at least one license.
    """
    issues = []
    for vendor in vendor_dirs:
        for root, dirs, filenames in os.walk(vendor):
            if root.count(os.sep) - vendor.count(os.sep) == 2:  # two levels deep
                # Two level deep means folders like `github.com/elastic`.
                # look for the license in root but also one level up
                ok, issue = has_license(root)
                if not ok:
                    print(f"No license in: {issue}")
                    issues.append(issue)
    if issues:
        raise Exception(
            f"I have found licensing issues in the following folders: {issues}"
        )


def write_notice_file(f, beat, copyright, dependencies):

    now = datetime.datetime.now()

    # Add header
    f.write(f"{beat}\n")
    f.write("Copyright 2014-{0} {1}\n".format(now.year, copyright))
    f.write("\n")
    f.write("This product includes software developed by The Apache Software \n" +
            "Foundation (http://www.apache.org/).\n\n")

    # Add licenses for 3rd party libraries
    f.write("==========================================================================\n")
    f.write(f"Third party libraries used by the {beat} project:\n")
    f.write("==========================================================================\n\n")

    # Sort licenses by package path, ignore upper / lower case
    for key in sorted(dependencies, key=str.lower):
        for lib in dependencies[key]:
            f.write("\n--------------------------------------------------------------------\n")
            f.write(f"Dependency: {key}\n")
            if "version" in lib:
                f.write(f'Version: {lib["version"]}\n')
            if "revision" in lib:
                f.write(f'Revision: {lib["revision"]}\n')
            f.write(f'License type (autodetected): {lib["license_summary"]}\n')
            f.write(f'{lib["license_file"]}:\n')
            f.write("--------------------------------------------------------------------\n")
            if lib["license_summary"] != "Apache-2.0":
                f.write(lib["license_contents"])
            else:
                # it's an Apache License, so include only the NOTICE file
                f.write("Apache License 2.0\n\n")

                # Skip NOTICE files which are not needed
                if os.path.join(os.path.dirname(lib["license_file"])) in SKIP_NOTICE:
                    continue

                for notice_file in glob.glob(os.path.join(os.path.dirname(lib["license_file"]), "NOTICE*")):
                    notice_file_hdr = f"-------{os.path.basename(notice_file)}-----\n"
                    f.write(notice_file_hdr)
                    f.write(read_file(notice_file))


def write_csv_file(csvwriter, dependencies):
    csvwriter.writerow(["name", "url", "version", "revision", "license"])
    for key in sorted(dependencies, key=str.lower):
        for lib in dependencies[key]:
            csvwriter.writerow([key, get_url(key), lib.get("version", ""), lib.get("revision", ""),
                                lib["license_summary"]])


def get_url(repo):
    words = repo.split("/")
    if words[0] != "github.com":
        return repo
    return f"https://github.com/{words[1]}/{words[2]}"


def create_notice(filename, beat, copyright, vendor_dirs, csvfile, overrides=None):
    dependencies = gather_dependencies(vendor_dirs, overrides=overrides)
    if not csvfile:
        with open(filename, "w+") as f:
            write_notice_file(f, beat, copyright, dependencies)
            print(f"Available at {filename}")
    else:
        with open(csvfile, "wb") as f:
            csvwriter = csv.writer(f)
            write_csv_file(csvwriter, dependencies)
            print(f"Available at {csvfile}")
    return dependencies


APACHE2_LICENSE_TITLES = [
    "Apache License Version 2.0",
    "Apache License, Version 2.0",
    re.sub(r"\s+", " ", """Apache License
    ==============

    _Version 2.0, January 2004_"""),
]

MIT_LICENSES = [
    re.sub(r"\s+", " ", """Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
    """),
    re.sub(r"\s+", " ", """Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies."""),
]

BSD_LICENSE_CONTENTS = [
    re.sub(r"\s+", " ", """Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:"""),
    re.sub(r"\s+", " ", """Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer."""),
    re.sub(r"\s+", " ", """Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
""")]

BSD_LICENSE_3_CLAUSE = [
    re.sub(r"\s+", " ", """Neither the name of"""),
    re.sub(r"\s+", " ", """nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.""")
]

BSD_LICENSE_4_CLAUSE = [
    re.sub(r"\s+", " ", """All advertising materials mentioning features or use of this software
   must display the following acknowledgement"""),
]

CC_SA_4_LICENSE_TITLE = [
    "Creative Commons Attribution-ShareAlike 4.0 International"
]

LGPL_3_LICENSE_TITLE = [
    "GNU LESSER GENERAL PUBLIC LICENSE Version 3"
]

MPL_LICENSE_TITLES = [
    "Mozilla Public License Version 2.0",
    "Mozilla Public License, version 2.0"
]


# return SPDX identifiers from https://spdx.org/licenses/
def detect_license_summary(content):
    # replace all white spaces with a single space
    content = re.sub(r"\s+", ' ', content)
    # replace smart quotes with less intelligent ones
    content = content.replace(b'\xe2\x80\x9c', '"').replace(b'\xe2\x80\x9d', '"')
    if any(sentence in content[:1000] for sentence in APACHE2_LICENSE_TITLES):
        return "Apache-2.0"
    if any(sentence in content[:1000] for sentence in MIT_LICENSES):
        return "MIT"
    if all(sentence in content[:1000] for sentence in BSD_LICENSE_CONTENTS):
        if any(
            sentence not in content[:1000] for sentence in BSD_LICENSE_3_CLAUSE
        ):
            return "BSD-2-Clause"
        if all(
            sentence in content[:1000] for sentence in BSD_LICENSE_4_CLAUSE
        ):
            return "BSD-4-Clause"
        return "BSD-3-Clause"
    if any(sentence in content[:300] for sentence in MPL_LICENSE_TITLES):
        return "MPL-2.0"
    if any(sentence in content[:3000] for sentence in CC_SA_4_LICENSE_TITLE):
        return "CC-BY-SA-4.0"
    if any(sentence in content[:3000] for sentence in LGPL_3_LICENSE_TITLE):
        return "LGPL-3.0"

    return "UNKNOWN"


ACCEPTED_LICENSES = [
    "Apache-2.0",
    "MIT",
    "BSD-4-Clause",
    "BSD-3-Clause",
    "BSD-2-Clause",
    "MPL-2.0",
]
SKIP_NOTICE = []

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate the NOTICE file from all vendor directories available in a given directory")
    parser.add_argument("vendor",
                        help="directory where to search for vendor directories")
    parser.add_argument("-b", "--beat", default="Elastic Beats",
                        help="Beat name")
    parser.add_argument("-c", "--copyright", default="Elasticsearch BV",
                        help="copyright owner")
    parser.add_argument("--csv", dest="csvfile",
                        help="Output to a csv file")
    parser.add_argument("-e", "--excludes", default=["dev-tools", "build"],
                        help="List of top directories to exclude")
    # no need to be generic for now, no other transitive dependency information available
    parser.add_argument("--beats-origin", type=argparse.FileType('r'),
                        help="path to beats vendor.json")
    parser.add_argument("-s", "--skip-notice", default=[],
                        help="List of NOTICE files to skip")
    args = parser.parse_args()

    cwd = os.getcwd()
    notice = os.path.join(cwd, "NOTICE.txt")
    vendor_dirs = []

    excludes = args.excludes
    if not isinstance(excludes, list):
        excludes = [excludes]
    SKIP_NOTICE = args.skip_notice

    for root, dirs, files in os.walk(args.vendor):

        # Skips all hidden paths like ".git"
        if '/.' in root:
            continue

        if 'vendor' in dirs:
            vendor_dirs.append(os.path.join(root, 'vendor'))
            dirs.remove('vendor')   # don't walk down into sub-vendors

        for exclude in excludes:
            if exclude in dirs:
                dirs.remove(exclude)

    overrides = {}  # revision overrides only for now
    if args.beats_origin:
        govendor = json.load(args.beats_origin)
        overrides = {package['path']: package for package in govendor["package"]}

    print(f"Get the licenses available from {vendor_dirs}")
    check_all_have_license_files(vendor_dirs)
    dependencies = create_notice(notice, args.beat, args.copyright, vendor_dirs, args.csvfile, overrides=overrides)

    # check that all licenses are accepted
    for _, deps in dependencies.items():
        for dep in deps:
            if dep["license_summary"] not in ACCEPTED_LICENSES:
                raise Exception(
                    f'Dependency {dep["path"]} has invalid license {dep["license_summary"]}'
                )
