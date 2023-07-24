import subprocess
import re

# Get the output from the 'ps aux' command
ps_aux_output = subprocess.check_output(["ps", "aux"]).decode()

# Find all lines containing 'gphoto'
gphoto_lines = re.findall(r'.*gphoto.*', ps_aux_output)

# Extract PID for each process except 'grep --color=auto gphoto'
pids_to_kill = [line.split()[1] for line in gphoto_lines if 'grep --color=auto gphoto' not in line]

# Kill each process using 'kill -9'
for pid in pids_to_kill:
    subprocess.run(['kill', '-9', pid])
