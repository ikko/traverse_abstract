set -x
date
rm pids/wip/abs/*
for i in {1..2}; do
  python abstract.py &
done
date
