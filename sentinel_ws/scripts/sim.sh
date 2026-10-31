#!/usr/bin/env bash
set -eo pipefail
workspace_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/humble/setup.bash
if [[ ! -f "$workspace_dir/install/setup.bash" ]]; then
  echo "请先运行 scripts/build.sh" >&2
  exit 1
fi
source "$workspace_dir/install/setup.bash"
cd "$workspace_dir"
exec ros2 launch sentry_bringup sim_teleop.launch.py "$@"
