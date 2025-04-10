// string_utils.h
#pragma once

#include <string>
#include <algorithm>
#include <cctype>

// In-place trimming
inline void trim(std::string &s) {
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), [](unsigned char ch) {
        return !std::isspace(ch);
    }));
    
    s.erase(std::find_if(s.rbegin(), s.rend(), [](unsigned char ch) {
        return !std::isspace(ch);
    }).base(), s.end());
}

// Returns a trimmed copy
inline std::string trimmed(std::string s) {
    trim(s);
    return s;
}

// For C++17 string_view support (no copying)
#if __cplusplus >= 201703L
#include <string_view>
inline std::string_view trimmed_view(std::string_view sv) {
    constexpr auto whitespace = " \t\n\r\f\v";
    auto start = sv.find_first_not_of(whitespace);
    if (start == sv.npos) return "";
    
    auto end = sv.find_last_not_of(whitespace);
    return sv.substr(start, end - start + 1);
}
#endif
