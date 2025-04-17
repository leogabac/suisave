#include "../include/ansicolors.h"
#include "../include/backup_utils.h"
#include "../include/toml.hpp"
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <string>
#include <vector>

using namespace std::literals;
using namespace BackupUtils;

// ===== FUNCTION SIGNATURES ===== //
void default_backup(const toml::table& config, toml::array* backups,
                    std::vector<std::string>& drive_uuids);

// ===== GLOBAL VARIABLES ===== //
const std::filesystem::path HOME = std::getenv("HOME");
const std::filesystem::path CONFIG = ".config/suisave/config.toml";

std::string hostname = get_hostname();
const std::filesystem::path BASE_BACKUP_DIR = "pc_backups/" + hostname;

int main() {

    std::string bk_name;
    std::vector<std::string> drive_labels, drive_uuids, bk_sources,
        bk_dirs; // init

    std::string configfile = (HOME / CONFIG).string();
    if (!std::filesystem::exists(configfile)) {
        std::cerr << Colors::ERROR << " ";
        std::cerr << "Config file not found at " << configfile;
        std::cerr << "Exiting" << std::endl;
        return 1;
    }

    auto config = toml::parse_file((HOME / CONFIG).string());

    get_drives(config, drive_labels, drive_uuids);

    if (drive_uuids.empty()) {
        std::cerr << Colors::ERROR << " ";
        std::cerr << "There are no configured drives. Exiting" << std::endl;
        return 1;
    }

    // check if at least one of the default drives is mounted
    bool is_any_mounted = false;
    for (int i = 0; i < drive_uuids.size(); i++) {
        std::string mnt = get_mountpoint(drive_uuids[i]);
        if (mnt.empty()) {
            is_any_mounted = is_any_mounted || false;
        } else {
            is_any_mounted = is_any_mounted || true;
        }
    }
    if (!is_any_mounted) {
        std::cerr << Colors::ERROR << " ";
        std::cerr << "No default drive is mounted! Exiting." << std::endl;
        return 1;
    }

    // accessing the sources
    auto backups = config["default"].as_array();
    if (backups) {
        default_backup(config, backups, drive_uuids);
    } else {
        std::cout << Colors::INFO << " ";
        std::cout << "No default backups are configured" << "\n";
    }

    return 0;
}

void default_backup(const toml::table& config, toml::array* backups,
                    std::vector<std::string>& drive_uuids) {

    std::vector<std::string> bk_sources;
    std::string bk_name;
    std::string default_flags = config["general"]["rsync_flags"].value_or("");
    for (auto&& backup : *backups) {
        if (auto backup_table = backup.as_table()) {

            // TODO: here i will need to handle default values somewhere in the
            bk_name = backup_table->get("name")->value_or("");
            bk_sources = get_sources(*backup_table);
        }
    }

    // getting the mountpoints of each drive
    // here i prefer to produce the mountpoints, and then loop across them
    // this way, i will already have discarded the nonmounted drives
    std::vector<std::string> bk_dirs;
    for (auto&& cu_uuid : drive_uuids) {
        std::string mountpoint = get_mountpoint(cu_uuid);
        if (mountpoint.empty()) {
            continue;
        }
        std::filesystem::path fs_mountpoint = mountpoint;
        std::filesystem::path full_path = fs_mountpoint / BASE_BACKUP_DIR;
        bk_dirs.push_back(full_path.string());
    }

    for (auto&& tg_mount : bk_dirs) {
        // create the tgmount directory
        system(("mkdir -p " + tg_mount).c_str());
        for (auto&& src_dir : bk_sources) {
            std::string command =
                "rsync " + default_flags + " " + src_dir + " " + tg_mount + "/";
            std::cout << command << "\n";
            system(command.c_str());
        }
    }
}
