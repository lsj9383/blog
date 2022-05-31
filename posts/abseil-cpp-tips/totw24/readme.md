# Copies, Abbrv

Quicklink: [Abseil：C++ Tips of the Week](../readme.md)

## 例子

让我们看一些在例子：

```cpp
std::string build();

std::string foo(std::string arg) {
  return arg;  // no copying here, only one name for the data “arg”.
}

void bar() {
  std::string local = build();  // only 1 instance -- only 1 name

  // no copying, a reference won’t incur a copy
  std::string& local_ref = local;

  // one copy operation, there are now two named collections of data.
  std::string second = foo(local);
}
```

大多数时候，这些都不重要。最重要的是确保你代码的可读性和一致性，而不是担忧副本和性能。

怀疑存在性能问题，和往常一样：在优化前进行 profile。

但如果你发现你需要重头写代码，并且提供一个干净且一致的 API 来返回值，不要忽视看起来会复制的代码。

> everything you learned about copies in C++ a decade ago is wrong.
