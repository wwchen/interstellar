#!/bin/bash

[[ -f database.sqlite3 ]] && rm database.sqlite3
for i in reviews/*; do
  echo "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
  echo "Processing $i"
  ./main.py "$i"
  echo "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
done
./main.py
