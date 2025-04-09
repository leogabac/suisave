#include "include/toml.hpp"
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

int main() {

  // accessing the rsync default flags
  std::string default_flags, bk_name;
  std::vector<std::string> drive_labels, drive_uuids, bk_sources; // init

  parse_config(default_flags, drive_labels, drive_uuids, bk_name, bk_sources);

  return 0;
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
