#ifndef BACKUP_UTILS_H
#define BACKUP_UTILS_H

#include "string_utils.h"
#include "toml.hpp"
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <unistd.h> // For gethostname()
#include <vector>

namespace BackupUtils {

inline std::vector<std::string>
get_sources(const toml::table& backup_table,
            const std::vector<std::string>& default_sources = {}) {
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

inline void get_drives(const toml::table& config,
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

inline std::string get_hostname() {
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

// Decodes \xHH sequences in strings (e.g., "\x20" -> ' ')
inline std::string decode_escaped(const std::string& input) {
    std::ostringstream out;
    for (size_t i = 0; i < input.length(); ++i) {
        if (input[i] == '\\' && i + 3 < input.length() && input[i + 1] == 'x') {
            std::string hex = input.substr(i + 2, 2);
            char ch = static_cast<char>(std::strtol(hex.c_str(), nullptr, 16));
            out << ch;
            i += 3; // Skip over \xHH
        } else {
            out << input[i];
        }
    }
    return out.str();
}

inline std::string get_mountpoint(std::string uuid) {
    std::string command = "findmnt -rn -S UUID=" + uuid + " -o TARGET";
    char buffer[256];
    FILE* fp = popen(command.c_str(), "r");

    if (fgets(buffer, sizeof(buffer), fp) != nullptr) {
        std::string result = buffer;
        fclose(fp);
        trim(result);
        return decode_escaped(result); // Decode \xHH sequences before returning
    } else {
        fclose(fp);
        return "";
    }
}

} // namespace BackupUtils

#endif // BACKUP_UTILS_H
