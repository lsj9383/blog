# String Concatenation and operator+ vs. StrCat()

Quicklink:

- [目录](../readme.md)
- [原文链接](https://abseil.io/tips/3)

不少人对 “不要使用字符串拼接运算符，它的效率不高” 感到困惑，怎么可能 **std::string::operator+** 的效率不高呢？

> Users are often surprised when a reviewer says, “Don’t use the string concatenation operator, it’s not that efficient.” How can it be that std::string::operator+ is inefficient? Isn’t it hard to get that wrong?

事实证明，这种低效不是非常明确的。在实践中，下面两段代码具有接近的性能：

```cpp
std::string foo = LongString1();
std::string bar = LongString2();
std::string foobar = foo + bar;

std::string foo = LongString1();
std::string bar = LongString2();
std::string foobar = absl::StrCat(foo, bar);
```

然而下面代码的性能差别却是比较大的：

```cpp
std::string foo = LongString1();
std::string bar = LongString2();
std::string baz = LongString3();
string foobar = foo + bar + baz;

std::string foo = LongString1();
std::string bar = LongString2();
std::string baz = LongString3();
std::string foobar = absl::StrCat(foo, bar, baz);
```

由于 **std::string::operator+** 是两个参数的重载，因此三个字符串相加必然会生成一个临时变量。

因此，对于 **std::string foobar = foo + bar + baz** 的运算，实际上执行的是类似如下代码：

```cpp
std::string temp = foo + bar;
std::string foobar = std::move(temp) + baz;
```

具体而言，对于 foo 和 bar，一定会拷贝到临时变量 temp 中，然后才能放进 foobar。

C++11 允许第二个拼接不创建新的字符串对象，对于 `std::move(temp) + baz` 等价于 `std::move(temp.append(baz))`。

然而 **baz** 的字符串大小可能会超过 temp 中分配的内存大小，导致重新分配内存大小，并进行一次复制。所以，最坏的情况下，n 个字符串的拼接，可能会有 `o(n)` 复杂度的内存分配。

最好使用 **absl::StrCat()**，声明于 [absl/strings/str_cat.h](https://github.com/abseil/abseil-cpp/blob/master/absl/strings/str_cat.h)，它计算必要的字符串长度，保留该大小，并将所有输入连接到输出中。

对于以下的情况：

```cpp
foobar += foo + bar + baz;
```

也可以使用 `absl::StrCat()` 进行优化：

```cpp
absl::StrAppend(&foobar, foo, bar, baz);
```
