# build_cpu.tcl
set part    xc7a35tcpg236-1
set top     cpu
set outdir  ./vivado_cpu

file mkdir $outdir
create_project -force cpu_proj $outdir/proj -part $part

# Add all RV32I sources. riscv_pkg.sv defines the package imported by the
# others; update_compile_order lets Vivado resolve dependency order itself.
# alu.sv lives in projects/alu/rtl and is instantiated by cpu.sv.
add_files -norecurse [list \
    projects/riscv_cpu/rtl/riscv_pkg.sv \
    projects/riscv_cpu/rtl/regfile.sv \
    projects/riscv_cpu/rtl/decoder.sv \
    projects/riscv_cpu/rtl/control.sv \
    projects/riscv_cpu/rtl/program_counter.sv \
    projects/riscv_cpu/rtl/imem.sv \
    projects/alu/rtl/alu.sv \
    projects/riscv_cpu/rtl/cpu.sv \
]
set_property top $top [current_fileset]
update_compile_order -fileset sources_1

synth_design -top $top -part $part

# Clock created AFTER synth_design so get_ports can resolve the clk port.
create_clock -period 10.000 -name clk [get_ports clk]

opt_design
place_design
route_design

report_timing_summary -file $outdir/timing_summary.rpt
report_utilization     -file $outdir/utilization.rpt

puts "DONE. Open $outdir/timing_summary.rpt and $outdir/utilization.rpt"
