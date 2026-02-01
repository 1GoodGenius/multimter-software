#!/bin/bash
set -e
g++ -std=c++11 tests/test_calculator.cpp -O2 -o tests/test_calculator
g++ -std=c++11 tests/test_autorange.cpp -O2 -o tests/test_autorange
g++ -std=c++11 tests/test_trigger.cpp -O2 -o tests/test_trigger
g++ -std=c++11 tests/test_calibration.cpp -O2 -o tests/test_calibration

printf "Running calculator tests...\n"
./tests/test_calculator
printf "Running autorange tests...\n"
./tests/test_autorange
printf "Running trigger tests...\n"
./tests/test_trigger
printf "All host tests ran.\n" 
