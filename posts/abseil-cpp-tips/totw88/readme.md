# Initialization: =, (), and {}

Quicklink:

- [目录](../readme.md)
- [原文链接](https://abseil.io/tips/88)

C++11 提供了一种新的**统一初始化语法(uniform initialization syntax)**，它统一了各种初始化风格，避免了 [Most Vexing Parse](https://en.wikipedia.org/wiki/Most_vexing_parse) 问题。

## C++11 大括号初始化

一些统一初始化语法支持者会建议我们使用 {} 进行初始化（不使用 `=`，尽管大多数情况下调用的是相同的构造函数）：

```cpp
int x{2};
std::string foo{"Hello World"};
std::vector<int> v{1, 2, 3};
```

相对于：

```cpp
int x = 2;
std::string foo = "Hello World";
std::vector<int> v = {1, 2, 3};
```

这种方式有两个缺点：

首先，在某些情况下，调用什么以及如何调用方面仍然存在歧义（这个歧义是对于读者，而不是编译器，本质上是导致可读性差，代码令人困惑）：

```cpp
std::vector<std::string> strings{2}; // A vector of two empty strings.
std::vector<int> ints{2};            // A vector containing only the integer 2.
```

其次，这种语法并不直观。

## 初始化的最佳实践

**1. 使用预期值直接初始化、执行 struct 初始化、执行复制构造函数时，使用赋值语法**

这里提到的使用预期值直接初始化，包括：

- 使用字面量（例如 int, float, double）
- 使用智能指针
- 使用容器


```cpp
int x = 2;
std::string foo = "Hello World";
std::vector<int> v = {1, 2, 3};
std::unique_ptr<Matrix> matrix = NewMatrix(rows, cols);
MyStruct x = {true, 5.0};
MyProto copied_proto = original_proto;
```

代替：

```cpp
// Bad code
int x{2};
std::string foo{"Hello World"};
std::vector<int> v{1, 2, 3};
std::unique_ptr<Matrix> matrix{NewMatrix(rows, cols)};
MyStruct x{true, 5.0};
MyProto copied_proto{original_proto};
```

**2. 当初始化具有一些逻辑时，使用传统构造函数语法（带括号），而不是简单的把值组合在一起：**

```cpp
Frobber frobber(size, &bazzer_to_duplicate);
std::vector<double> fifty_pies(50, 3.14);
```

代替：

```cpp
// Bad code

// Could invoke an initializer list constructor, or a two-argument constructor.
Frobber frobber{size, &bazzer_to_duplicate};

// Makes a vector of two doubles.
std::vector<double> fifty_pies{50, 3.14};
```

**3. 仅当上述方式无法编译通过时，才使用不带 = 的 {} 初始化：**

```cpp
class Foo {
 public:
  Foo(int a, int b, int c) : array_{a, b, c} {}

 private:
  int array_[5];
  // Requires {}s because the constructor is marked explicit
  // and the type is non-copyable.
  EventManager em{EventManager::Options()};
};
```

**4. 切勿将 {} 和 auto 混用：**

```cpp
// Bad code
auto x{1};
auto y = {2}; // This is a std::initializer_list<int>!
```
