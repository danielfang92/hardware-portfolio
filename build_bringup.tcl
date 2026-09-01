set part    xc7a35tcpg236-1
set top     bringup_blink
set outdir  ./vivado_bringup

file mkdir $outdir
create_project -force bringup_proj $outdir/proj -part $part
add_files -norecurse projects/bringup/rtl/bringup_blink.sv
add_files -fileset constrs_1 -norecurse projects/bringup/constr/Basys3-Master.xdc
set_property top $top [current_fileset]

synth_design -top $top -part $part
opt_design
place_design
route_design
write_bitstream -force $outdir/bringup_blink.bit

report_timing_summary -file $outdir/timing_summary.rpt
report_utilization     -file $outdir/utilization.rpt
puts "DONE. Bitstream ready at $outdir/bringup_blink.bit"
