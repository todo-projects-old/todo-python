#!/bin/bash

lines=()
if read -t 0 -N 0;
then
    while read line
    do
        lines+=("$line")
    done <&0
fi
echo $@ $(echo "${lines[@]}")
$@ $(echo "${lines[@]}")
