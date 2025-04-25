# ==============================================================================
# The idea of this script is to automate installation
# basically, compile the binaries, 
# move them to somewhere else,
# and make a few checks
# ==============================================================================

import os
import time
import subprocess
import sys
import re

# ==============================================================================
# GLOBAL VARIABLES
# ==============================================================================

# ANSI escape sequences for some colored text
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

# relevant paths
HOME: str = os.environ.get('HOME')
BIN_DIR: str = os.path.join(HOME,'bin')
CONFIG_DIR: str = os.path.join(HOME,'.config','suisave')
CONFIG_FILE: str = os.path.join(CONFIG_DIR,'config.toml')

# ==============================================================================
# COMPILATION
# ==============================================================================


print(f"{OK} Initializing intallation script.")

# ask for recompilation if the binaries exist
mkbin: bool = True
if os.path.exists(os.path.join(BIN_DIR,'suisave')):
    print(f"{INFO} The suisave binaries exist")
    # outputs True if default option (N)
    # invert to make true for recompilation
    mkbin = not (input(f"{INPUT} Do you want to recompile? [y/N] ").lower() not in ('y', 'yes'))

if mkbin:
    filename: str = os.path.basename(__file__)
    abs_path: str =  os.path.realpath(__file__)
    dir_path: str = abs_path.split(filename)[0]
    os.chdir(os.path.join(dir_path,"src"))

    print(f"{INFO} Compiling suisave")
    os.system("g++ main.cpp -o suisave")
    print(f"{OK} Compiled binaries.")

    # move binaries to $HOME/bin
    print(f"{INFO} Moving binaries to {BIN_DIR}")
    os.system(f"mv suisave {BIN_DIR}")
    print(f"{OK} Binaries were moved to {BIN_DIR}")


# check if HOME/bin is in PATH
if not os.path.isdir(os.path.join(HOME,'bin')):
    print(f"{INFO} Creating {BIN_DIR}")
    os.mkdir(BIN_DIR)
    print(f"{OK} {BIN_DIR} was created successfully.")
else:
    print(f"{INFO} {BIN_DIR} exists")

# check if configuration directory exists
if not os.path.isdir(CONFIG_DIR):
    print(f"{INFO} Creating {CONFIG_DIR}")
    os.mkdir(CONFIG_DIR)
    print(f"{OK} {CONFIG_DIR} was created successfully.")
else:
    print(f"{INFO} {CONFIG_DIR} exists")

# check if $HOME/bin is in PATH
pathlist: list = os.environ.get('PATH').split(":")
in_path: bool = BIN_DIR in pathlist
if in_path:
    print(f"{OK} {BIN_DIR} is in PATH.")
else:
    print(f"{WARNING} {BIN_DIR}  is not in PATH, add it later")

# check if configuration file exists
mkconfig: bool = False
if os.path.exists(CONFIG_FILE):

    print(f"{INFO} Configuration file exists.")
    mkconfig: bool = not (input(f"{INPUT} Do you want to make another one? [y/N] ").lower() not in ('y', 'yes'))
    if mkconfig:
        bakfile: str = os.path.join(CONFIG_DIR,"config.bak")
        print(f"{INFO} Backing up current configuration into {bakfile}")
        os.system(f"mv {CONFIG_FILE} {bakfile}")
        time.sleep(5)


else:

    print(f"{INFO} There is no configuration file.")
    mkconfig: bool = input(f"{INPUT} Do you want to make a configuration file? [Y/n] ").lower() not in ('n', 'no')

# ==============================================================================
# CONFIGURATION SETUP
# ==============================================================================

if mkconfig:
    os.system("clear")

    print("="*30 + "\n" + "CONFIGURATION SETUP" + "\n" + "="*30)

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

    selection: int = int(input(f"{INPUT} Please choose a # from the table above (default=0): ") or "0")
    print(selection)
    print(labels)
    print(uuids)
    sel_label: str = labels[selection]
    sel_uuid: str = uuids[selection]


    os.system("clear")
    print("===== Default locations =====")
    print(f"{INFO} By default, the following locations will be backed up. You can change it later")

    default_locs = [d for d in os.listdir(HOME) if os.path.isdir(os.path.join(HOME, d))]
    default_locs = [d for d in default_locs if not d.startswith(".")]

    for location in default_locs:
            print(os.path.join(HOME,location))

    locations = [os.path.join(HOME,location) for location in default_locs]

    config_str = f"""[general]
    rsync_flags = "{rsync_flags}"

    [[drives]]
    label = "{sel_label}"
    uuid = "{sel_uuid}"

    [[default]]
    name = "general"
    sources = [{', '.join(f'"{item}"' for item in locations)}] 
    """

    with open(os.path.join(CONFIG_DIR,'config.toml'), 'w') as f:
        f.write(config_str)
    print(f"{OK} Configuration file written to {CONFIG_FILE}")

