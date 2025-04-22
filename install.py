import os
import sys


print("Initializing intallation script.")

filename: str = os.path.basename(__file__)
abs_path: str =  os.path.realpath(__file__)
dir_path: str = abs_path.split(filename)[0]
os.chdir(os.path.join(dir_path,"src"))

print("Compiling suisave")
os.system("g++ main.cpp -o suisave")

homedir: str = os.environ.get('HOME')
bindir: str = os.path.join(homedir,'bin')

# check if HOME/bin is in PATH
if not os.path.isdir(os.path.join(homedir,'bin')):
    print(f"Creating... {bindir}")
    os.mkdir(bindir)
else:
    print(f"{bindir}... exists")

# check if configuration directory exists
configdir: str = os.path.join(homedir,'.config','suisave')
if not os.path.isdir(configdir):
    print(f"Creating... {configdir}")
    os.mkdir(configdir)
else:
    print(f"{configdir}... exists")

# move binaries to $HOME/bin
print(f"Moving binaries to {bindir}")
os.system(f"mv suisave {bindir}")

# check if $HOME/bin is in PATH
in_path: bool = True
pathlist: list = os.environ.get('PATH').split(":")
if not (bindir in pathlist):
    print(f"[\033[33mWARNING\033[0m] {bindir}  is not in PATH, add it later")
    in_path = False

# check if configuration file exists
configfile: str = os.path.join(configdir,'config.toml')
if os.path.exists(configfile):
    print("Configuration file exists. Exiting")
    sys.exit()

# this part will execute if there is no configuration file,
# and will try to help you configure it
