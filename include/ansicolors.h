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

// Note: INFO and ERROR can't be constexpr because they involve runtime
// concatenation
inline const std::string INFO = "[  " + BLUE + "INFO" + RESET + "  ]";
inline const std::string WARNING = "[  " + YELLOW + "WARNING" + RESET + "  ]";
inline const std::string ERROR = "[  " + RED + "ERROR" + RESET + "  ]";
inline const std::string OK = "[  " + GREEN + "OK" + RESET + "  ]";
inline const std::string CMD = "[  " + MAGENTA + "CMD" + RESET + "  ]";
} // namespace Colors

#endif
