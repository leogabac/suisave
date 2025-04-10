#include "include/string_utils.h"
#include "include/toml.hpp"
#include <algorithm>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <string>
#include <vector>

using namespace std::literals;

// ===== GLOBAL VARIABLES ===== //
const std::filesystem::path HOME = std::getenv("HOME");
const std::filesystem::path CONFIG = ".config/suisave/config.toml";

// in this first attempt, i will deal with the default behavior
// there are some default flags

// there are some default drives, there could be more than one
// if some drive is not mounted, just ignore it

// the default mode simply copies with the default flags into
// drive/pc_backups/hostname/source1
// drive/pc_backups/hostname/source2
// etc...

// the general [[backups]] table should have
// name, rsync_flags, sources, label, uuid, base directory destination,
// if some is not present, fallback to the defaults

// ===== FUNCTION SIGNATURE ===== //
std::vector<std::string>
get_sources(const toml::table &backup_table,
            const std::vector<std::string> &default_sources = {});

void parse_config(std::string &default_flags,
                  std::vector<std::string> &drive_labels,
                  std::vector<std::string> &drive_uuids, std::string &bk_name,
                  std::vector<std::string> &bk_sources);

void get_hostname(std::string &hostname);
std::string get_mountpoint(std::string uuid);

int main() {

  // accessing the rsync default flags
  std::string default_flags, bk_name;
  std::vector<std::string> drive_labels, drive_uuids, bk_sources,
      bk_dirs; // init

  parse_config(default_flags, drive_labels, drive_uuids, bk_name, bk_sources);

  std::string hostname;
  get_hostname(hostname);
  const std::filesystem::path base_backup_dir = "pc_backups/" + hostname;

  // getting the mountpoints of each drive
  // here i prefer to produce the mountpoints, and then loop across them
  // this way, i will already have discarded the nonmounted drives
  for (auto &&cu_uuid : drive_uuids) {
    std::string mountpoint = get_mountpoint(cu_uuid);
    if (mountpoint.empty()) {
      continue;
    }
    std::filesystem::path fs_mountpoint = mountpoint;
    std::filesystem::path full_path = fs_mountpoint / base_backup_dir;
    bk_dirs.push_back(full_path.string());
  }

  for (auto &&tg_mount : bk_dirs) {
    // create the tgmount directory
    system(("mkdir -p " + tg_mount).c_str());
    for (auto &&src_dir : bk_sources) {
      std::string command = "rsync " + default_flags + " " + src_dir + " " + tg_mount+"/";
      std::cout << command << "\n";
      system(command.c_str());
    }
  }

  return 0;
}

// ===== FUNCTION DEFINITION =====//
void get_hostname(std::string &hostname) {
  char buffer[128];
  FILE *fp = popen("uname -n", "r");

  if (fgets(buffer, sizeof(buffer), fp) != nullptr) {
    hostname = buffer;
    trim(hostname);
  } else {
    std::cerr << "Failed to read hostname" << std::endl;
  }
  fclose(fp);
}

// ===== FUNCTION DEFINITION =====//
std::string get_mountpoint(std::string uuid) {
  std::string command = "findmnt -rn -S UUID=" + uuid + " -o TARGET";
  char buffer[128];
  FILE *fp = popen(command.c_str(), "r");

  if (fgets(buffer, sizeof(buffer), fp) != nullptr) {
    std::string result = buffer;
    fclose(fp);
    trim(result);
    return result;

  } else {
    fclose(fp);
    return "";
  }
}

// ===== FUNCTION DEFINITION =====//
// parse the configuration file
void parse_config(std::string &default_flags,
                  std::vector<std::string> &drive_labels,
                  std::vector<std::string> &drive_uuids, std::string &bk_name,
                  std::vector<std::string> &bk_sources) {

  auto config = toml::parse_file((HOME / CONFIG).string());
  default_flags = config["general"]["rsync_flags"].value_or(""sv);

  // accessing the external drives information
  auto drives = config["drives"].as_array();

  std::string label, uuid; // init (local)
  if (drives) {
    for (auto &&drive : *drives) {
      if (auto drive_table = drive.as_table()) {
        label = drive_table->get("label")->value_or("");
        uuid = drive_table->get("uuid")->value_or("");

        drive_labels.push_back(label);
        drive_uuids.push_back(uuid);
      }
    }
  }

  // accessing the sources
  auto backups = config["backups"].as_array();
  if (backups) {
    for (auto &&backup : *backups) {
      if (auto backup_table = backup.as_table()) {

        // TODO: here i will need to handle default values somewhere in the
        bk_name = backup_table->get("name")->value_or("");
        bk_sources = get_sources(*backup_table);
      }
    }
  }
}

// ===== FUNCTION DEFINITION =====//
// parse the sources list into a vector of strings
std::vector<std::string>
get_sources(const toml::table &backup_table,
            const std::vector<std::string> &default_sources) {
  std::vector<std::string> sources;

  if (backup_table.contains("sources")) {
    if (auto sources_node = backup_table["sources"].as_array()) {
      for (const auto &item : *sources_node) {
        if (auto str = item.value<std::string>()) {
          sources.push_back(*str);
        }
      }
    }
  }

  return sources.empty() ? default_sources : sources;
}
