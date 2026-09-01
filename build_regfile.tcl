# build_regfile.tcl
set part    xc7a35tcpg236-1
set top     regfile
set rtl     projects/riscv_cpu/rtl/regfile.sv
set outdir  ./vivado_regfile

file mkdir $outdir
create_project -force regfile_proj $outdir/proj -part $part

add_files -norecurse $rtl
set_property top $top [current_fileset]
update_compile_order -fileset sources_1

# Out-of-context: regfile has 113 top-level ports but the cpg236 package has
# only ~106 bonded user I/O pins. A register file is an INTERNAL block, never
# wired to the chip boundary, so we characterize it OOC — no I/O buffers, no
# physical pin placement. This is the standard way to get block-level area/timing.
synth_design -top $top -part $part -mode out_of_context

# Clock must be created AFTER synth_design: get_ports needs an open
# (synthesized) design to resolve the clk port. Constraining the synthesized
# netlist here gives real post-route timing against a 100 MHz (10 ns) target.
create_clock -period 10.000 -name clk [get_ports clk]

opt_design
place_design
route_design

report_timing_summary -file $outdir/timing_summary.rpt
report_utilization     -file $outdir/utilization.rpt

puts "DONE. Open $outdir/timing_summary.rpt and $outdir/utilization.rpt"
