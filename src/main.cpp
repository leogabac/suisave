#include "../include/ansicolors.h"
#include "../include/backup_utils.h"
#include "../include/toml.hpp"
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <string>
#include <unistd.h>
#include <vector>

using namespace std::literals;
using namespace BackupUtils;

// ===== FUNCTION SIGNATURES ===== //
void default_backup(const toml::table& config, toml::array* backups,
                    std::vector<std::string>& drive_uuids);

void custom_backup(const toml::table& config, toml::array* bkarray);

// ===== GLOBAL VARIABLES ===== //
const std::filesystem::path HOME = std::getenv("HOME");
const std::filesystem::path CONFIG = ".config/suisave/config.toml";


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
    std::cout << Colors::OK << " ";
    std::cout << "Configuration file exists." << "\n";

    auto config = toml::parse_file((HOME / CONFIG).string());

    get_drives(config, drive_labels, drive_uuids);

    // exit if not default drives are configures
    if (drive_uuids.empty()) {
        std::cerr << Colors::ERROR << " ";
        std::cerr << "There are no configured drives. Exiting" << std::endl;
        return 1;
    }
    std::cout << Colors::OK << " ";
    std::cout << "Default drives are configured." << "\n";

    // check if at least one of the default drives is mounted
    bool is_any_mounted = false;
    for (const auto& uuid : drive_uuids) {
        if (!get_mountpoint(uuid).empty()) {
            is_any_mounted = true;
            break;
        }
    }
    // exit if there are no mounted drives
    if (!is_any_mounted) {
        std::cerr << Colors::ERROR
                  << " No default drive is mounted! Exiting.\n";
        return 1;
    }
    std::cout << Colors::OK << " ";
    std::cout << "Default drives are mounted." << "\n";

    // make the default backups
    std::cout << Colors::INFO << " ";
    std::cout << "Making default backups." << "\n";

    auto backups = config["default"].as_array();
    if (backups) {
        default_backup(config, backups, drive_uuids);
    } else {
        std::cout << Colors::INFO << " ";
        std::cout << "No default backups are configured" << "\n";
    }

    std::cout << Colors::INFO << " ";
    std::cout << "Making custom backups." << "\n";
    auto custom_bktable = config["custom"].as_array();
    if (custom_bktable) {
        custom_backup(config, custom_bktable);
    } else {
        std::cout << Colors::INFO << " ";
        std::cout << "No custom backups are configured" << "\n";
    }

    return 0;
}

/**
 * @brief Makes the default backup, i.e. cp sources -> drive
 *
 * @param config Parsed table from toml
 * @param backups Array of toml tables
 * @param drive_uuids Vector of drive UUIDs
 * @return void
 *
 * @note This function performs filesystem operations
 * @warning May block on filesystem access
 */
void default_backup(const toml::table& config, toml::array* backups,
                    std::vector<std::string>& drive_uuids) {

    std::vector<std::string> bk_sources;
    std::string bk_name;
    std::string default_flags = config["general"]["rsync_flags"].value_or("");
    for (auto&& backup : *backups) {
        if (auto backup_table = backup.as_table()) {

            bk_name = backup_table->get("name")->value_or("");
            bk_sources = get_sources(*backup_table);
        }
    }

    // getting the mountpoints of each drive
    // here i prefer to produce the mountpoints, and then loop across them
    // this way, i will already have discarded the nonmounted drives

    std::filesystem::path pcname = config["general"]["pcname"].value_or("");
    std::filesystem::path tgbase = config["general"]["tgbase"].value_or("");
    if (tgbase.empty()) {
        tgbase = "pc_backups";
    }
    if (pcname.empty()) {
        pcname = get_hostname();
    }
    std::filesystem::path backup_dir = (tgbase/pcname);

    std::vector<std::string> bk_dirs;
    for (auto&& cu_uuid : drive_uuids) {
        std::string mountpoint = get_mountpoint(cu_uuid);
        if (mountpoint.empty()) {
            continue;
        }
        std::filesystem::path fs_mountpoint = mountpoint;
        std::filesystem::path full_path = fs_mountpoint / backup_dir / "";
        bk_dirs.push_back(full_path.string());
    }

    for (auto&& tg_mount : bk_dirs) {
        // create the tgmount directory
        system(("mkdir -p " + tg_mount).c_str());
        for (auto&& src_dir : bk_sources) {
            std::string command =
                "rsync " + default_flags + " " + src_dir + " " + tg_mount;
            std::cout << Colors::MAGENTA;
            std::cout << command << Colors::RESET << "\n";
            system(command.c_str());
        }
    }
}

void custom_backup(const toml::table& config, toml::array* bkarray) {

    std::string bkname, drive_label, drive_uuid, flags;
    std::vector<std::string> bksources;
    for (auto&& backup : *bkarray) {
        if (auto bktable = backup.as_table()) {
            bkname = bktable->get("name")->value_or("");
            drive_label = bktable->get("label")->value_or("");
            drive_uuid = bktable->get("uuid")->value_or("");
            flags = bktable->get("rsync_flags")->value_or("");
            std::filesystem::path tgbase = bktable->get("tgbase")->value_or("");
            std::filesystem::path mountpoint = get_mountpoint(drive_uuid);
            std::string full_path = (mountpoint / tgbase / "").string();

            bksources = get_sources(*bktable);
            for (auto&& src : bksources) {
                std::string command =
                    "rsync " + flags + " " + src + " " + full_path;
                std::cout << Colors::MAGENTA;
                std::cout << command << Colors::RESET << "\n";
                system(command.c_str());
            }
        }
    }
}
