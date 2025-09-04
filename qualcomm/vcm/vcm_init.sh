#!/bin/bash
echo r 240 1 1 > /sys/kernel/debug/qcom,actuator12/slave
ret=$(cat /sys/kernel/debug/qcom,actuator12/u8)

if [ $ret -ne 165 ]; then
           echo "step 1 init fail, return $ret"
              exit
fi

echo w 224 1 1 1 > /sys/kernel/debug/qcom,actuator12/slave
sleep 0.1

echo r 179 1 1 > /sys/kernel/debug/qcom,actuator12/slave
ret=$(cat /sys/kernel/debug/qcom,actuator12/u8)

if [ $ret -ne 0 ]; then
           echo "step 2 init fail"
              exit
fi

echo w 168 10 1 1 > /sys/kernel/debug/qcom,actuator12/slave

echo "vcm initial complete"
