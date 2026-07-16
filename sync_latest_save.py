import os
import shutil
import sys


def say(message):
    sys.stdout.write(message + os.linesep)


def say_error(message):
    sys.stderr.write(message + os.linesep)


def script_directory():
    return os.path.dirname(os.path.abspath(__file__))


def ensure_directory(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def is_save_file(name):
    return name.lower().endswith(".sav")


def find_saves(directory):
    if not os.path.isdir(directory):
        return []

    saves = []
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if os.path.isfile(path) and is_save_file(name):
            saves.append(path)
    return saves


def latest_save(paths):
    newest_path = None
    newest_time = -1

    for path in paths:
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue

        if mtime > newest_time:
            newest_time = mtime
            newest_path = path

    return newest_path


def same_path(left, right):
    left = os.path.normcase(os.path.abspath(left))
    right = os.path.normcase(os.path.abspath(right))
    return left == right


def copy_save(source, target):
    if same_path(source, target):
        return False
    shutil.copy2(source, target)
    return True


def remove_other_scenario_saves(scenario_save_dir, latest_name):
    for path in find_saves(scenario_save_dir):
        if os.path.basename(path) != latest_name:
            os.remove(path)


def main():
    base_dir = script_directory()
    conquests_dir = os.path.abspath(os.path.join(base_dir, os.pardir, os.pardir))
    conquests_save_dir = os.path.join(conquests_dir, "Saves")
    conquests_auto_dir = os.path.join(conquests_save_dir, "Auto")
    scenario_save_dir = os.path.join(base_dir, "Saves")

    if not os.path.isdir(conquests_save_dir):
        say_error("Could not find Civ 3 save directory: {0}".format(conquests_save_dir))
        return 1

    ensure_directory(scenario_save_dir)

    conquests_root_saves = find_saves(conquests_save_dir)
    scenario_saves = find_saves(scenario_save_dir)
    all_saves = conquests_root_saves + find_saves(conquests_auto_dir) + scenario_saves

    conquests_root_latest = latest_save(conquests_root_saves)
    scenario_latest = latest_save(scenario_saves)
    newest_save = latest_save(all_saves)

    if newest_save is None:
        say(
            "No .SAV files found in {0}, {1}, or {2}".format(
                conquests_save_dir, conquests_auto_dir, scenario_save_dir
            )
        )
        return 0

    latest_name = os.path.basename(newest_save)
    latest_time = os.path.getmtime(newest_save)
    scenario_target = os.path.join(scenario_save_dir, latest_name)
    conquests_target = os.path.join(conquests_save_dir, latest_name)
    copied_any = False

    if scenario_latest is None or os.path.getmtime(scenario_latest) < latest_time:
        copy_save(newest_save, scenario_target)
        remove_other_scenario_saves(scenario_save_dir, latest_name)
        say("Updated scenario save: {0}".format(scenario_target))
        copied_any = True

    if conquests_root_latest is None or os.path.getmtime(conquests_root_latest) < latest_time:
        copy_save(newest_save, conquests_target)
        say("Updated Civ 3 save: {0}".format(conquests_target))
        copied_any = True

    if not copied_any:
        say("Both save locations are already current: {0}".format(latest_name))

    return 0


if __name__ == "__main__":
    sys.exit(main())
