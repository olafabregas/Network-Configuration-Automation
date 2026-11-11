# Sourced by docs/media/netauto-demo.tape before the visible frames.
# Not a standalone demo. From the repository root:
#   vhs docs/media/netauto-demo.tape

_pace_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
_project=$(cd "${_pace_dir}/../../network-automation-project" && pwd) || return 1
cd "${_project}" || return 1

export PYTHONDONTWRITEBYTECODE=1
export PS1='\[\033[38;5;150m\]network-automation-project\[\033[0m\] $ '

# The recording types `python netauto.py ...`. This function runs that program
# unchanged and only delays its stdout so the walkthrough can be read.
python() {
  command python3 -u "$@" | python3 "${_pace_dir}/pace_lines.py"
}
