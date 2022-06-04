# Copies, Abbrv

Quicklink:

- [目录](../readme.md)
- [原文链接](https://abseil.io/tips/24)

## 一个名称，没有拷贝；两个名称，两个副本

在评估数据是否存在副本时（包括 RVO），请检查有多少名称引用了你的数据。

同时，你的数据如果存在两个副本，也意味着有两个名称分别引用这两个副本。对于其他任何情况，编译器都会省略多余的副本。

对于**移动语义**和**复制构造函数省略**，正在收敛于这个规则，不仅提供了副本数量的下限，而且提供了保证。如果你在测试中发现有多个副本存在，则可能编译器有问题。

**注意：**

- 复制构造函数省略（copy constructor elision），其实就是 RVO 优化。

因此，如果你的代码结构使得在执行期间的某个时间点有两个名称，那么理论上会存在一次拷贝。如果你避免使用名称去引用数据，将有助于编译器去省略拷贝。

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
