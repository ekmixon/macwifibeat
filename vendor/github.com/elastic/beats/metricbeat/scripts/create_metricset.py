import os
import argparse

# Creates a new metricset with all the necessary file
# In case the module does not exist, also the module is created


def generate_metricset(base_path, metricbeat_path, module, metricset):

    generate_module(base_path, metricbeat_path, module, metricset)
    metricset_path = f"{base_path}/module/{module}/{metricset}"
    meta_path = f"{metricset_path}/_meta"

    if os.path.isdir(metricset_path):
        print(f"Metricset already exists. Skipping creating metricset {metricset}")
        return

    os.makedirs(meta_path)

    templates = f"{metricbeat_path}/scripts/module/metricset/"

    content = load_file(f"{templates}metricset.go.tmpl", module, metricset)
    with open(f"{metricset_path}/{metricset}.go", "w") as f:
        f.write(content)

    content = load_file(f"{templates}fields.yml", module, metricset)
    with open(f"{meta_path}/fields.yml", "w") as f:
        f.write(content)

    content = load_file(f"{templates}docs.asciidoc", module, metricset)
    with open(f"{meta_path}/docs.asciidoc", "w") as f:
        f.write(content)

    content = load_file(f"{templates}data.json", module, metricset)
    with open(f"{meta_path}/data.json", "w") as f:
        f.write(content)

    print(f"Metricset {metricset} created.")


def generate_module(base_path, metricbeat_path, module, metricset):

    module_path = f"{base_path}/module/{module}"
    meta_path = f"{module_path}/_meta"

    if os.path.isdir(module_path):
        print(f"Module already exists. Skipping creating module {module}")
        return

    os.makedirs(meta_path)

    templates = f"{metricbeat_path}/scripts/module/"

    content = load_file(f"{templates}fields.yml", module, "")
    with open(f"{meta_path}/fields.yml", "w") as f:
        f.write(content)

    content = load_file(f"{templates}docs.asciidoc", module, "")
    with open(f"{meta_path}/docs.asciidoc", "w") as f:
        f.write(content)

    content = load_file(f"{templates}config.yml", module, metricset)
    with open(f"{meta_path}/config.yml", "w") as f:
        f.write(content)

    content = load_file(f"{templates}doc.go.tmpl", module, "")
    with open(f"{module_path}/doc.go", "w") as f:
        f.write(content)

    print(f"Module {module} created.")


def load_file(file, module, metricset):
    content = ""
    with open(file) as f:
        content = f.read()

    return content.replace("{module}", module).replace("{metricset}",
                                                       metricset)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Creates a metricset")
    parser.add_argument("--module", help="Module name")
    parser.add_argument("--metricset", help="Metricset name")

    parser.add_argument("--path", help="Beat path")
    parser.add_argument("--es_beats",
                        help="The path to the general beats folder")

    args = parser.parse_args()

    if args.path is None:
        args.path = './'
        print(f"Set default path for beat path: {args.path}")

    if args.es_beats is None:
        args.es_beats = '../'
        print(f"Set default path for es_beats path: {args.es_beats}")

    if args.module is None or args.module == '':
        args.module = raw_input("Module name: ")

    if args.metricset is None or args.metricset == '':
        args.metricset = raw_input("Metricset name: ")

    path = os.path.abspath(args.path)
    metricbeat_path = os.path.abspath(f"{args.es_beats}/metricbeat")

    generate_metricset(path, metricbeat_path, args.module.lower(),
                       args.metricset.lower())
