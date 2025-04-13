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

// ANSI color codes
const std::string RESET = "\033[0m";
const std::string RED = "\033[31m";
const std::string GREEN = "\033[32m";
const std::string YELLOW = "\033[33m";
const std::string BLUE = "\033[34m";
const std::string MAGEN = "\033[35m";
const std::string CYAN = "\033[36m";
const std::string WHITE = "\033[37m";
const std::string INFO = "[" + YELLOW + "INFO" + RESET + "]";

using namespace std::literals;

// ===== GLOBAL VARIABLES ===== //
const std::filesystem::path HOME = std::getenv("HOME");
const std::filesystem::path CONFIG = ".config/suisave/config.toml";

// ===== FUNCTION SIGNATURE ===== //
std::vector<std::string>
get_sources(const toml::table& backup_table,
            const std::vector<std::string>& default_sources = {});

void get_drives(const toml::table& config,
                std::vector<std::string>& drive_labels,
                std::vector<std::string>& drive_uuids);

void default_backup(const toml::table& config, toml::array* backups,
                    std::vector<std::string>& drive_uuids);

std::string get_hostname();
std::string get_mountpoint(std::string uuid);

std::string hostname = get_hostname();
const std::filesystem::path BASE_BACKUP_DIR = "pc_backups/" + hostname;

int main() {

    std::string bk_name;
    std::vector<std::string> drive_labels, drive_uuids, bk_sources,
        bk_dirs; // init

    auto config = toml::parse_file((HOME / CONFIG).string());

    get_drives(config, drive_labels, drive_uuids);

    // accessing the sources
    auto backups = config["default"].as_array();
    if (backups) {
        default_backup(config, backups, drive_uuids);
    } else {
        std::cout << INFO << " ";
        std::cout << "No default backups are configured" << "\n";
    }

    return 0;
}

// ===== FUNCTION DEFINITION =====//
std::string get_hostname() {
    char buffer[128];
    FILE* fp = popen("uname -n", "r");
    if (!fp) {
        std::cerr << "Failed to run 'uname -n'" << std::endl;
        return ""; // Return empty string on error
    }

    std::string hostname;
    if (fgets(buffer, sizeof(buffer), fp) != nullptr) {
        hostname = buffer;
        trim(hostname);
    } else {
        std::cerr << "Failed to read hostname" << std::endl;
    }

    pclose(fp); // Always close the stream
    return hostname;
}

// ===== FUNCTION DEFINITION =====//
std::string get_mountpoint(std::string uuid) {
    std::string command = "findmnt -rn -S UUID=" + uuid + " -o TARGET";
    char buffer[128];
    FILE* fp = popen(command.c_str(), "r");

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

void get_drives(const toml::table& config,
                std::vector<std::string>& drive_labels,
                std::vector<std::string>& drive_uuids) {

    // accessing the external drives information
    auto drives = config["drives"].as_array();

    std::string label, uuid; // init (local)
    if (drives) {
        for (auto&& drive : *drives) {
            if (auto drive_table = drive.as_table()) {
                label = drive_table->get("label")->value_or("");
                uuid = drive_table->get("uuid")->value_or("");

                drive_labels.push_back(label);
                drive_uuids.push_back(uuid);
            }
        }
    }
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

// ===== FUNCTION DEFINITION =====//
// parse the sources list into a vector of strings
std::vector<std::string>
get_sources(const toml::table& backup_table,
            const std::vector<std::string>& default_sources) {
    std::vector<std::string> sources;

    if (backup_table.contains("sources")) {
        if (auto sources_node = backup_table["sources"].as_array()) {
            for (const auto& item : *sources_node) {
                if (auto str = item.value<std::string>()) {
                    sources.push_back(*str);
                }
            }
        }
    }

    return sources.empty() ? default_sources : sources;
}
