# Default Member Initializers

Quicklink:

- [目录](../readme.md)
- [原文链接](https://abseil.io/tips/61)

## 声明默认成员初始化

```cpp
class Client {
 private:
  int chunks_in_flight_ = 0;
};
```

此类默认初始化传播到该类的所有构造函数。以这种方式初始化成员，对于拥有大量的数据成员的类很有用，特别是诸如 bool, int, double 和原始指针之类的类型。

默认成员初始化对于没有编写构造函数的简单结构，也非常适用：

```cpp
struct Options {
  bool use_loas = true;
  bool log_pii = false;
  int timeout_ms = 60 * 1000;
  std::array<int, 4> timeout_backoff_ms = { 10, 100, 1000, 10 * 1000 };
};
```

## 成员初始化覆盖

如果类构造函数，则构造函数中的初始化会取代默认值：

```cpp
class Frobber {
 public:
  Frobber() : ptr_(nullptr), length_(0) { }
  Frobber(const char* ptr, size_t length) : ptr_(ptr), length_(length) { }
  Frobber(const char* ptr) : ptr_(ptr) { }

 private:
  const char* ptr_;
  // length_ has a non-static class member initializer
  const size_t length_ = strlen(ptr_);
};
```

上述代码等效于如下旧代码：

```cpp
class Frobber {
 public:
  Frobber() : ptr_(nullptr), length_(0) { }
  Frobber(const char* ptr, size_t length) : ptr_(ptr), length_(length) { }
  Frobber(const char* ptr) : ptr_(ptr), length_(strlen(ptr_)) { }

 private:
  const char* ptr_;
  const size_t length_;
};
```

请注意，Frobber 的第一和第二个构造函数都有变量初始化，所以这两个构造函数不会使用 length_ 的默认初始化。

Frobber 的第三个构造函数没有 length_ 的初始化，因此对于 length_ 会使用默认初始化，即 `strlen(ptr_)`。

在 C++ 中，所有成员变量都按他们声明的顺序初始化。

## 结论

默认成员初始化不会让程序更快，但他们有助于减少遗漏的错误，尤其是当有人添加新的构造函数或新的数据成员时。
