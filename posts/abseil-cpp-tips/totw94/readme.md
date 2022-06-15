# Callsite Readability and bool Parameters

Quicklink:

- [目录](../readme.md)
- [原文链接](https://abseil.io/tips/94)

假设你遇到过这样的代码：

```cpp
int main(int argc, char* argv[]) {
  ParseCommandLineFlags(&argc, &argv, false);
}
```

你能说出该代码在做什么，尤其是最后一个参数的含义么？

那么，我们如何修复该示例中的代码呢？一种可能的（但不好的）做法是这样：

```cpp
int main(int argc, char* argv[]) {
  ParseCommandLineFlags(&argc, &argv, false /* preserve flags */);
}
```

一种更好的方式是在注释中指明参数的名称：

```cpp
int main(int argc, char* argv[]) {
  ParseCommandLineFlags(&argc, &argv, /*remove_flags=*/false);
}
```

这更加清晰，同时更加方便让注释和代码保持一致，甚至可以通过 [Clang-tidy](https://clang.llvm.org/extra/clang-tidy/checks/bugprone-argument-comment.html) 来校验注释和参数名是否一致。

一个类似的变体如下：

```cpp
int main(int argc, char* argv[]) {
  const bool remove_flags = false;
  ParseCommandLineFlags(&argc, &argv, remove_flags);
}
```

然而编译器并不会检查解释变量名的正确性，因此他们可能是错的。

所有这些方法还依赖于程序员始终记得添加这些注释或变量，并正确地这样做（尽管 clang-tidy 将检查参数名称注释的正确性）。

在许多情况下，最好的解决方法是避免 bool 参数，而使用 enum 来代替：

```cpp
enum ShouldRemoveFlags {
  kDontRemoveFlags,
  kRemoveFlags
};

void ParseCommandLineFlags(int* argc, char*** argv, ShouldRemoveFlags remove_flags);

// 我们可以这样调用
int main(int argc, char* argv[]) {
  ParseCommandLineFlags(&argc, &argv, kDontRemoveFlags);
}
```

根据 [TotW 86](../totw86/readme.md) 所述，你也可以使用 `enum class`：

```cpp
enum class ShouldRemoveFlags {
  kNo,
  kYes
};

int main(int argc, char* argv[]) {
  ParseCommandLineFlags(&argc, &argv, ShouldRemoveFlags::kNo);
}
```

显然，这种方式需要你在定义 `ParseCommandLineFlags()` 时去实现声明枚举类，你不能让调用方去声明枚举。

所以当你定义一个函数时，特别是如果它要被广泛使用，你有责任仔细考虑调用点的外观，尤其是对 bool 参数持谨慎态度。

> Obviously, this approach has to be implemented when the function is defined; you can’t really opt into it at the callsite (you can fake it, but for little benefit). So when you’re defining a function, particularly if it’s going to be widely used, the onus is on you to think carefully about how the callsites will look, and in particular to be very skeptical of bool parameters.
