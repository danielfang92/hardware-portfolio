#!/usr/bin/env bash
# Run the Windows install of Vivado from WSL, in the current directory.
# Vivado is a Windows program, so it can't see Linux paths directly: wslpath
# turns $PWD into \\wsl.localhost\..., and pushd makes that the working
# directory so the build scripts' relative paths resolve.
#   scripts/vivado_wsl.sh -mode batch -source build_cpu.tcl
# Override the install location with VIVADO_BAT if it differs.
set -euo pipefail
VIVADO_BAT="${VIVADO_BAT:-C:\\AMDDesignTools\\2025.2\\Vivado\\bin\\vivado.bat}"
exec cmd.exe /c "pushd $(wslpath -w "$PWD") && $VIVADO_BAT $*"
