#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
conquests_dir="$(cd -- "$script_dir/../.." && pwd)"
conquests_save_dir="$conquests_dir/Saves"
conquests_auto_dir="$conquests_save_dir/Auto"
scenario_save_dir="$script_dir/Saves"

file_mtime() {
    stat -c %Y "$1" 2>/dev/null || stat -f %m "$1"
}

find_conquests_saves() {
    find_conquests_root_saves
    if [[ -d "$conquests_auto_dir" ]]; then
        find "$conquests_auto_dir" -maxdepth 1 -type f -iname '*.sav' -print0
    fi
}

find_conquests_root_saves() {
    find "$conquests_save_dir" -maxdepth 1 -type f -iname '*.sav' -print0
}

find_scenario_saves() {
    find "$scenario_save_dir" -maxdepth 1 -type f -iname '*.sav' -print0
}

latest_from_stream() {
    local newest_path=""
    local newest_time=-1
    local path mtime

    while IFS= read -r -d '' path; do
        mtime="$(file_mtime "$path")"
        if (( mtime > newest_time )); then
            newest_time="$mtime"
            newest_path="$path"
        fi
    done

    printf '%s' "$newest_path"
}

if [[ ! -d "$conquests_save_dir" ]]; then
    echo "Could not find Civ 3 save directory: $conquests_save_dir" >&2
    exit 1
fi

mkdir -p "$scenario_save_dir"

conquests_root_latest="$(latest_from_stream < <(find_conquests_root_saves))"
scenario_latest="$(latest_from_stream < <(find_scenario_saves))"
latest_save="$(latest_from_stream < <(find_conquests_saves; find_scenario_saves))"

if [[ -z "$latest_save" ]]; then
    echo "No .SAV files found in $conquests_save_dir, $conquests_auto_dir, or $scenario_save_dir"
    exit 0
fi

latest_name="$(basename -- "$latest_save")"
latest_time="$(file_mtime "$latest_save")"
scenario_target="$scenario_save_dir/$latest_name"
conquests_target="$conquests_save_dir/$latest_name"
copied_any=0

if [[ -z "$scenario_latest" ]] || (( $(file_mtime "$scenario_latest") < latest_time )); then
    cp -p -- "$latest_save" "$scenario_target"
    find "$scenario_save_dir" -maxdepth 1 -type f -iname '*.sav' ! -name "$latest_name" -delete
    echo "Updated scenario save: $scenario_target"
    copied_any=1
fi

if [[ -z "$conquests_root_latest" ]] || (( $(file_mtime "$conquests_root_latest") < latest_time )); then
    cp -p -- "$latest_save" "$conquests_target"
    echo "Updated Civ 3 save: $conquests_target"
    copied_any=1
fi

if (( copied_any == 0 )); then
    echo "Both save locations are already current: $latest_name"
fi
