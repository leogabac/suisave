#include "include/toml.hpp"
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <string>
#include <vector>

using namespace std::literals;

// ===== GLOBAL VARIABLES ===== //
const std::filesystem::path HOME = std::getenv("HOME");
const std::filesystem::path CONFIG = ".config/chirpive/config.toml";

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
  std::vector<std::string> drive_labels, drive_uuids, bk_sources; // init

  parse_config(default_flags, drive_labels, drive_uuids, bk_name, bk_sources);

  size_t n = std::min(drive_labels.size(), drive_uuids.size());
  for (size_t i = 0; i < n; ++i) {
    std::string cu_label = drive_labels[i];
    std::string cu_uuid = drive_uuids[i];
    std::string mountpoint = get_mountpoint(cu_uuid);
    // skip if the drive is not mounted
    if (mountpoint.empty()) {
      continue;
    }
    // now in the mounted drive
    std::cout << "Drive Label: " << cu_label << ", UUID: " << cu_uuid << "\n";
    std::cout << mountpoint << "\n";
  }

  std::string hostname;
  get_hostname(hostname);

  return 0;
}

// ===== FUNCTION DEFINITION =====//
void get_hostname(std::string &hostname) {
  char buffer[128];
  FILE *fp = popen("uname -n", "r");

  if (fgets(buffer, sizeof(buffer), fp) != nullptr) {
    hostname = buffer;
  } else {
    std::cerr << "Failed to read hostname" << std::endl;
  }
  fclose(fp);
}

std::string get_mountpoint(std::string uuid) {

  // MOUNT_POINT=$(findmnt -rn -S UUID=$UUID -o TARGET)
  std::string command = "findmnt -rn -S UUID=" + uuid + " -o TARGET";
  char buffer[128];
  FILE *fp = popen(command.c_str(), "r");

  if (fgets(buffer, sizeof(buffer), fp) != nullptr) {
    fclose(fp);
    return buffer;
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
