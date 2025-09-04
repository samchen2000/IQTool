#!/bin/bash
echo r 34 1 2 > /sys/kernel/debug/qcom,actuator12/slave
val=$(cat /sys/kernel/debug/qcom,actuator12/u16)
signed_max=32767
wrap_around=65536
if (( val > signed_max )); then
                ret=$(( val - wrap_around ))
        else
                        ret=$val
fi
ret=$(( ret >> 5 ))
echo $ret
