#!/usr/bin/python3
import shutil
import sys
import json

from os.path import exists, join, basename, dirname
from os import listdir, mkdir, getcwd, remove


global_packages = ""
project_path = ""


def save_paths(obj):
    with open(join(getcwd(), 'history.json'), 'w') as his:
        json.dump(obj, his, indent=2)


def get_history():
    history = join(getcwd(), 'history.json')
    if exists(history):
        with open(history, 'r') as his:
            return json.loads(his.read())
    else:
        return


def prompt_again():
    global global_packages
    global project_path
    global_packages = input("Global packages>> ").strip()
    if not global_packages:
        print("Please enter global package")
        get_paths()
    elif not exists(global_packages):
        print("{} doesn't exist!".format(global_packages))
        get_paths()

    project_path = input("Project path>> ").strip()
    if not project_path:
        print("Please enter project path")
        get_paths()
    elif not exists(project_path):
        print("{} doesn't exist!".format(project_path))
        get_paths()

    save_paths({
        "global_packages": global_packages,
        "project_path": project_path
    })


def get_paths():
    global global_packages
    global project_path
    if len(sys.argv) >= 3:
        global_packages = sys.argv[1]
        project_path = sys.argv[2]
        save_paths({
            "global_packages": global_packages,
            "project_path": project_path
        })
    elif 1 <= len(sys.argv) <= 2:
        his = get_history()
        if his:
            if exists(his["global_packages"]):
                global_packages = his["global_packages"]
                print("Global package: {}".format(global_packages))
            else:
                print("{} doesn't exist anymore! please enter global package".format(
                    his["global_packages"]))
                remove(join(getcwd(), 'history.json'))
                prompt_again()

            if exists(his["project_path"]):
                project_path = his["project_path"]
                print("Project path: {}".format(project_path))
            else:
                print("{} doesn't exist anymore!".format(his["project_path"]))
                remove(join(getcwd(), 'history.json'))
                prompt_again()
        else:
            prompt_again()


def npm_init(path):
    print('''\nThis utility will walk you through creating a package.json file.
It only covers the most common items, and tries to guess sensible defaults.

Press ^C at any time to quit.\n''')

    package_name = input("package name: ({}) ".format(
        basename(path))).lower() or basename(path).lower()
    version = input("version: (1.0.0) ") or "1.0.0"
    description = input("description: ")
    entry_point = input("entry point: (index.js) ") or "index.js"
    # test_command = input("test command: ")
    # git_repository = input("git repository: ")
    # keywords = input("keywords: ")
    author = input("author: ")
    license = input("license: (ISC) ") or "ISC"

    package_json = {
        "name": package_name,
        "version": version,
        "description": description,
        "main": entry_point,
        "scripts": {
            "test": "echo \"Error: no test specified\" && exit 1"
        },
        "author": author,
        "license": license
    }

    print("About to write to {}/package.json:\n".format(path))
    print("{")
    print('  name": "{}",'.format(package_name))
    print('  "version": "{}",'.format(version))
    print('  "description": "{}",'.format(description))
    print('  "main": "{}",'.format(entry_point))
    print('''  "scripts": {
        "test": "echo Error: no test specified && exit 1"
  },''')
    print('  "author": "{}",'.format(author))
    print('  "license": "{}",'.format(license))
    print('}\n')

    sure = input("Is this OK? (yes) ").lower() or 'yes'
    if sure == "yes":
        with open(join(path, 'package.json'), 'w') as w_package:
            json.dump(package_json, w_package, indent=2)
            print("Created package.json file in {}".format(path))
    else:
        print("Aborted.\n")


def load_json(path):
    if exists(path):
        with open(path, 'r') as package_json:
            return json.loads(package_json.read())


def get_deps(path):
    if exists(path):
        if exists(join(path, 'package.json')):
            return load_json(join(path, 'package.json')).get('dependencies', [])
        else:
            npm_init(path)


def get_all_deps(arr, global_packages, deps=[]):
    if not len(arr):
        return deps
    else:
        res = get_deps(join(global_packages, arr[0]))
        if res:
            _deps = list(res.keys())
        else:
            _deps = []

        arr += check_nested_nodemod(arr[0], global_packages)

        _deps = [i for i in _deps if i not in arr[1:] and i not in deps]
        return get_all_deps((arr+_deps)[1:], global_packages, list(set(_deps+deps+[arr[0]])))


def copy_packages(packages, global_packages, project_path):
    if not exists(join(project_path, 'node_modules')):
        mkdir(join(project_path, 'node_modules'))

    for i in packages:
        if not exists(join(project_path, 'node_modules', i)):
            if exists(join(global_packages, i)):
                shutil.copytree(join(global_packages, i),
                                join(project_path, 'node_modules', i))


def prompt_user():
    packs = input("Enter space separated>> ")
    packs = [i.replace(" ", "")
             for i in packs.split(" ") if i.replace(" ", "")]
    return packs


def check_nested_nodemod(package, global_packages):
    packages = []
    path = join(global_packages, package)
    if exists(join(path, 'node_modules')):
        _packs = [i for i in listdir(
            join(path, 'node_modules')) if i[0] != '.']
        _path = join(path, 'node_modules')
        if _packs:
            for _pack in _packs:
                __packs = get_deps(join(_path, _pack))
                if __packs:
                    packages += list(__packs.keys())
                packages += [_pack]
    return list(set(packages))


def update_json(deps, project_path):
    prev = load_json(join(project_path, 'package.json'))
    prev['dependencies'] = deps
    with open(join(project_path, 'package.json'), 'w') as update:
        json.dump(prev, update, indent=2)


def add_packs(_p, global_packages, project_path, init=False):
    if _p:
        if init:
            _p = {}
        print("{} are the packages!".format(list(_p.keys())))
        packs = prompt_user()
        packs = [i for i in packs if i not in list(_p.keys())]
        packages = get_all_deps(packs[:], global_packages)

        if packs:
            packages = packages+packs
            for pack in packs:
                if exists(join(global_packages, pack)):
                    v = load_json(join(global_packages, pack, 'package.json')).get(
                        'version', '1.0.0')
                    _p[pack] = v
                else:
                    print("{} doesn't exists".format(pack))

            copy_packages(packages, global_packages, project_path)
            update_json(_p, project_path)
            main()
        else:
            print("You haven't added any package(s)")
            main()

    else:
        add_packs({'npm': 'init'}, global_packages, project_path, True)
        main()


def get_first_parent(path):
    if not dirname(path):
        return path
    else:
        return get_first_parent(dirname(path))


def get_common_packages(victim, packs, global_packages):
    victim_packs = set(get_all_deps([victim], global_packages))
    intersections = []
    for pack in packs:
        inters = set(get_all_deps([pack], global_packages))
        intersections += list(victim_packs.intersection(inters))
    return list(set(intersections))


def delete_packs(packs, project_path):
    for pack in packs:
        if dirname(pack):
            pack = get_first_parent(pack)
        pack_path = join(project_path, 'node_modules', pack)
        if exists(pack_path):
            shutil.rmtree(pack_path)

    if not listdir(join(project_path, 'node_modules')):
        shutil.rmtree(join(project_path, 'node_modules'))


def get_common_packages(victim, packs, global_packages):
    victim_packs = set(get_all_deps([victim], global_packages))
    intersections = []
    for pack in packs:
        inters = set(get_all_deps([pack], global_packages))
        intersections += list(victim_packs.intersection(inters))
    return list(set(intersections))


def remove_packs(_p, global_packages, project_path):
    if _p:
        print("Removable Packages>> {}".format(list(_p.keys())))
        packs = prompt_user()
        packs = [i for i in packs if i in list(_p.keys())]
        if packs:
            for pack in packs:
                if _p.get(pack, []):
                    del _p[pack]
                    intersections = get_common_packages(
                        pack, list(_p.keys()), global_packages)
                    packages = [i for i in get_all_deps(
                        packs, global_packages) if i not in intersections]
                    delete_packs(packages, project_path)
            update_json(_p, project_path)
            main()
        else:
            print("\nNo package was selected\n")
            remove_packs(_p, global_packages, project_path)
    else:
        print("There are no packages to remove")
        main()


def main():
    global global_packages
    global project_path
    if not global_packages or not project_path:
        get_paths()
    if exists(global_packages):
        _p = get_deps(project_path)
        which = '''
        Enter 'a' to add package(s)
        Enter 'r' to remove package(s)
        Enter 'c' to change paths
        Enter 'q' to exuut\n
        '''
        which = input(which+"(a/r/q) >>>").lower()
        if which == 'a':
            add_packs(_p, global_packages, project_path)
        elif which == 'r':
            remove_packs(_p, global_packages, project_path)
        elif which == 'c':
            print("""
        Enter 'g' to change global packages path
        Enter 'p' or press ENTER to change project's path
        Enter 'b' to change both paths""")
            which_change = input("\t>> ").lower() or 'p'
            if which_change == 'b':
                remove(join(getcwd(), 'history.json'))
                if len(sys.argv) == 3:
                    sys.argv = sys.argv[:1]
                get_paths()
                main()
            elif which_change == 'p':
                his = get_history()
                while True:
                    proj_path = input("Input project's path>> ")
                    if exists(proj_path):
                        break
                if his:
                    his["project_path"] = proj_path
                    save_paths(his)
                    main()
            elif which_change == 'g':
                his = get_history()
                while True:
                    global_packages = input("Input global packages' path>> ")
                    if exists(global_packages):
                        break
                if his:
                    his["global_packages"] = global_packages
                    save_paths(his)
                    main()
        elif which == 'q':
            print('bye')
            sys.exit()
        else:
            main()
    else:
        print("{} doesn't exist".format(global_packages))


if __name__ == "__main__":
    main()
