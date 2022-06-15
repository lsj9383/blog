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

我们应该避免浪费脑力去记住这些函数参数，避免浪费时间去查询函数调用的文档，我们有更具价值和意义的事情去做。我们期望通过函数调用方式，就能很方便猜测出函数调用的含义。

选择好的函数名是良好可读性的关键，但往往还不够。我们需要参数本身提供它们自身含义的线索。

例如，如果没见过 `string_view`，那么你可能光看 `absl::string_view s(x, y)` 并不知道其含义是什么，但是 `absl::string_view s(my_str.data(), my_str.size())` 或者 `absl::string_view s("foo");` 看起来就更加清晰易懂。

对于 bool 参数，调用时往往使用字面量的 true 或者 false，并且正如我们在 `ParseCommandLineFlags()` 示例中看到的那样，这给读者没有关于参数含义的上下文提示。

如果有多个bool参数，这个问题会更加复杂，因为现在还有一个额外的问题是要弄清楚哪个参数是哪个。

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
