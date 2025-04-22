# ==============================================================================
# The idea of this script is to automate installation
# basically, compile the binaries, move them to somewhere else, and make a few checks
# ==============================================================================
import os
import subprocess
import sys
import re


# ANSI escape sequences for colored terminal text
RESET: str = "\033[0m"

BLACK: str = "\033[30m"
RED: str = "\033[31m"
GREEN: str = "\033[32m"
YELLOW: str = "\033[33m"
BLUE: str = "\033[34m"
MAGENTA: str = "\033[35m"
CYAN: str = "\033[36m"
WHITE: str = "\033[37m"

OK: str = f"[{GREEN}OK{RESET}]"
INFO: str = f"[{CYAN}INFO{RESET}]"
WARNING: str = f"[{YELLOW}WARNING{RESET}]"
INPUT: str = f"[{MAGENTA}INPUT{RESET}]"

print(f"{OK} Initializing intallation script.")

filename: str = os.path.basename(__file__)
abs_path: str =  os.path.realpath(__file__)
dir_path: str = abs_path.split(filename)[0]
os.chdir(os.path.join(dir_path,"src"))

print(f"{INFO} Compiling suisave")
os.system("g++ main.cpp -o suisave")
print(f"{OK} Compiled binaries.")

homedir: str = os.environ.get('HOME')
bindir: str = os.path.join(homedir,'bin')

# check if HOME/bin is in PATH
if not os.path.isdir(os.path.join(homedir,'bin')):
    print(f"{INFO} Creating... {bindir}")
    os.mkdir(bindir)
    print(f"{OK} {bindir} was created successfully.")
else:
    print(f"{INFO} {bindir}... exists")

# check if configuration directory exists
configdir: str = os.path.join(homedir,'.config','suisave')
if not os.path.isdir(configdir):
    print(f"{INFO} Creating... {configdir}")
    os.mkdir(configdir)
    print(f"{OK} {configdir} was created successfully.")
else:
    print(f"{INFO} {configdir}... exists")

# move binaries to $HOME/bin
print(f"{INFO} Moving binaries to {bindir}")
os.system(f"mv suisave {bindir}")
print(f"{OK} Binaries were moved to {bindir}")

# check if $HOME/bin is in PATH
pathlist: list = os.environ.get('PATH').split(":")
in_path: bool = bindir in pathlist

if in_path:
    print(f"{OK} {bindir} is in PATH.")
else:
    print(f"{WARNING} {bindir}  is not in PATH, add it later")

# check if configuration file exists
configfile: str = os.path.join(configdir,'config.toml')
if os.path.exists(configfile):

    print(f"{INFO} Configuration file exists. Exiting")
    is_default: bool = input(f"{INPUT} Do you want to make another one? [y/N] ").lower() not in ('y', 'yes')
    if is_default:
        print("Exiting")
        sys.exit() # early exit
    else:
        bakfile: str = os.path.join(configdir,"config.bak")
        print(f"{INFO} Backing up current configuration into {bakfile}")
        os.system(f"mv {configfile} {bakfile}")
else:

    print(f"{INFO} There is no configuration file.")
    is_default: bool = input(f"{INPUT} Do you want to make a configuration file? [Y/n] ").lower() not in ('n', 'no')
    if not is_default:
            print("Exiting")
            sys.exit() # early exit

# this part will execute if the user wanted to make a config file
os.system("clear")
print("===============================================")
print("CONFIGURATION SETUP")
print("===============================================")

print(f"{INFO} The following prompts will help you create a basic configuration file")
input(f"{INPUT} press ENTER to continue")

os.system("clear")
print("===== Default rsync flags =====")
is_default: bool = input(f"{INPUT} Do you want use the default flags (-avh --delete)? [Y/n] ").lower() not in ('n', 'no')
if is_default:
    rsync_flags = "-avh --delete"
else:
    rsync_flags = input(f"{INPUT} Please enter your preferred rsync flags: ").strip()


os.system("clear")
print("===== Default drive selection =====")
print(f"{INFO} Connect your drive to your computer")
input(f"{INPUT} press ENTER to continue")

result: str = subprocess.run(['lsblk', '-o', 'NAME,LABEL,UUID'], capture_output=True, text=True)
# Regex pattern to match sda* drives and capture label and UUID
pattern: str = r'^(└─|├─)?(sda\d*)\s+([^\s]*)\s+([A-F0-9-]+)'

# Find all matches
matches = re.finditer(pattern, result.stdout, re.MULTILINE)

# Process and print the results
print("{:<5} {:<10} {:<15} {:<20}".format("#","DEVICE", "LABEL", "UUID"))
print("-" * 50)

devices: list = []
labels: list = []
uuids: list = []
for i,match in enumerate(matches):
    device = match.group(2)  # sda or sda1
    label = match.group(3) if match.group(3) else "N/A"
    uuid = match.group(4)
    print("{:<5} {:<10} {:<15} {:<20}".format(i, device, label, uuid))
    devices.append(device)
    labels.append(label)
    uuids.append(uuid)

selection: int = int(input(f"{INPUT} Please choose a # from the table above (0,1,2,...): "))
sel_label: str = labels[selection]
sel_uuid: str = uuids[selection]


os.system("clear")
print("===== Default locations =====")
print(f"{INFO} By default, the following locations will be backed up. You can change it later")

default_locs = [d for d in os.listdir(homedir) if os.path.isdir(os.path.join(homedir, d))]
default_locs = [d for d in default_locs if not d.startswith(".")]

for location in default_locs:
        print(os.path.join(homedir,location))

locations = [os.path.join(homedir,location) for location in default_locs]

config_str = f"""[general]
rsync_flags = "{rsync_flags}"

[[drives]]
label = "{sel_label}"
uuid = "{sel_uuid}"

[[default]]
name = "general"
sources = [{', '.join(f'"{item}"' for item in locations)}] 
"""

with open(os.path.join(configdir,'config.toml'), 'w') as f:
    f.write(config_str)
print(f"{OK} Configuration file written to {configfile}")
