#ifndef ANSICOLORS_H
#define ANSICOLORS_H

#include <filesystem>
#include <string>

namespace Colors {
inline const std::string RESET = "\033[0m";
inline const std::string RED = "\033[31m";
inline const std::string GREEN = "\033[32m";
inline const std::string YELLOW = "\033[33m";
inline const std::string BLUE = "\033[34m";
inline const std::string MAGENTA = "\033[35m";
inline const std::string CYAN = "\033[36m";
inline const std::string WHITE = "\033[37m";

// Center text in a field of fixed width (excluding ANSI codes)
inline std::string label(const std::string& text, const std::string& color,
                         int width = 6) {
    int padding = width - text.length();
    int pad_left = padding / 2;
    int pad_right = padding - pad_left;
    return "[" + std::string(pad_left, ' ') + color + text + RESET +
           std::string(pad_right, ' ') + "]";
}

inline const std::string INFO = label("INFO", BLUE);
inline const std::string WARNING = label("WARN", YELLOW);
inline const std::string ERROR = label("ERR", RED);
inline const std::string OK = label("OK", GREEN);
inline const std::string CMD = label("EXEC", MAGENTA);
} // namespace Colors

#endif
