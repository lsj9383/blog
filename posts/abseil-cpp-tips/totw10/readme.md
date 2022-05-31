# Splitting Strings, not Hairs

Quicklink: [Abseil：C++ Tips of the Week](../readme.md)

将字符串拆分为子字符串是任何通用编程语言中的常见任务，C++ 也不例外。

Google 早期存在大量根据不同语义进行字符串拆分的函数，非常难以使用。

为了解决这个问题，Google 的 C++ 库团队实现了一个通用的拆分字符串 API：[absl/strings/str_split.h](https://github.com/abseil/abseil-cpp/blob/master/absl/strings/str_split.h)。

话不多说，让我们看一些例子：

```cpp
// Splits on commas. Stores in vector of string_view (no copies).
std::vector<absl::string_view> v = absl::StrSplit("a,b,c", ',');

// Splits on commas. Stores in vector of string (data copied once).
std::vector<std::string> v = absl::StrSplit("a,b,c", ',');

// Splits on literal string "=>" (not either of "=" or ">")
std::vector<absl::string_view> v = absl::StrSplit("a=>b=>c", "=>");

// Splits on any of the given characters (',' or ';')
using absl::ByAnyChar;
std::vector<std::string> v = absl::StrSplit("a,b;c", ByAnyChar(",;"));

// Stores in various containers (also works w/ absl::string_view)
std::set<std::string> s = absl::StrSplit("a,b,c", ',');
std::multiset<std::string> s = absl::StrSplit("a,b,c", ',');
std::list<std::string> li = absl::StrSplit("a,b,c", ',');

// Equiv. to the mythical SplitStringViewToDequeOfStringAllowEmpty()
std::deque<std::string> d = absl::StrSplit("a,b,c", ',');

// Yields "a"->"1", "b"->"2", "c"->"3"
std::map<std::string, std::string> m = absl::StrSplit("a,1,b,2,c,3", ',');
```

更多关于如何使用 **StrSplit** 的信息请参考 [absl/strings/str_split.h](https://github.com/abseil/abseil-cpp/blob/master/absl/strings/str_split.h)，以及相应的测试用例 [absl/strings/str_split_test.cc](https://github.com/abseil/abseil-cpp/blob/master/absl/strings/str_split_test.cc)。
