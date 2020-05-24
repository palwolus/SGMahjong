#!/bin/bash


python3 client.py -name Test1 -key '1111111111' -address "http://localhost:5000/" &
export TEST_1=$!
python3 client.py -name Test2 -key '2222222222' -address "http://localhost:5000/" &
export TEST_2=$!
python3 client.py -name Test3 -key '3333333333' -address "http://localhost:5000/" &
export TEST_3=$!
python3 client.py -name Test4 -key '4444444444' -address "http://localhost:5000/" &
export TEST_4=$!

# shellcheck disable=SC2162
read -p "Status"

kill -9 $TEST_1
kill -9 $TEST_2
kill -9 $TEST_3
kill -9 $TEST_4

#killall -9 python3