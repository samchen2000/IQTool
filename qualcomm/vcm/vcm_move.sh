sition=$(($1+0))
if [[ $position -gt 511  && $position -lt -512 ]]; then
                echo "invalid position"
                        exit
fi

input=$(($position+512))
echo w 132 $input 1 2 > /sys/kernel/debug/qcom,actuator12/slave
