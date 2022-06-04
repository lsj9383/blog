# Disappearing Act

Quicklink:

- [目录](../readme.md)
- [原文链接](https://abseil.io/tips/5)

有些时候，为了正确使用 C++ 库，你需要同时理解库和语言。那么下面的代码有什么问题？

```cpp
// DON’T DO THIS
std::string s1, s2;
...
const char* p1 = (s1 + s2).c_str();             // Avoid!
const char* p2 = absl::StrCat(s1, s2).c_str();  // Avoid!
```

无论是 **s1 + s2** 和 **absl::StrCat(s1, s2)** 创建临时对象，并且 `c_str()` 返回一个指针指向一个临时变量的字符串内存，因此 p1 和 p2 指向的内存生命周期，将和临时变量生命周期一致。

那么这样的临时变量生命周期是多长呢？根据 C++17 标准，在评估完整表达式的最后一步进行临时变量的销毁：

> Temporary objects are destroyed as the last step in evaluating the full-expression that (lexically) contains the point where they were created.

什么是完整表达式呢？只要不是一个别的表达式的子表达式，那么该表达式就是一个完整表达式（即树形的根）。

> A “full-expression” is “an expression that is not a subexpression of another expression”

在上面的每个例子中，赋值运算符右侧的表达式一完成，临时值就被销毁，返回值从 c_str() 变成了一个悬空指针。

## 选项一：在完整表达式结束之前完成使用临时对象

完整表达式结束前，临时对象都是可用的：

```cpp
// Safe (albeit a silly example):
size_t len1 = strlen((s1 + s2).c_str());
size_t len2 = strlen(absl::StrCat(s1, s2).c_str());
```

## 选项二：存储临时对象

无论如何，临时对象也是在栈空间上创建了一个对象，那为什么不进行显示的创建，让该对象多存在一段时间呢？

同时，又因为 RVO，因此在栈空间上创建一个新的对象成本也并非太大。

```cpp
// Safe (and more efficient than you might think):
std::string tmp_1 = s1 + s2;
std::string tmp_2 = absl::StrCat(s1, s2);
// tmp_1.c_str() and tmp_2.c_str() are safe.
```

## 选项三：存储临时对象的引用

C++17 标准中提到：将临时变量绑定到引用，或是临时变量的子对象绑定到引用，临时对象在引用的生命周期内持续存在。

> The temporary to which the reference is bound or the temporary that is the complete object of a sub-object to which the reference is bound persists for the lifetime of the reference.

因为 RVO，这种方式并不比存储临时对象（选项二）方式性能更好，反而这种形式会令人困惑和担忧。

```cpp
// Equally safe:
const std::string& tmp_1 = s1 + s2;
const std::string& tmp_2 = absl::StrCat(s1, s2);
// tmp_1.c_str() and tmp_2.c_str() are safe.

// 以下行为非常微妙：
// 如果编译器可以看到您正在存储对临时对象内部的引用，它将使整个临时对象保持活动状态。
struct Person { string name;}
// GeneratePerson() returns an object; GeneratePerson().name
const std::string& person_name = GeneratePerson().name; // safe

// 如果编译器无法判断，您就有风险了。
class DiceSeries_DiceRoll { const string& nickname() }
// GenerateDiceRoll() returns an object; the compiler can’t tell
// 编译器并不知道临时变量的 nickname() 返回是否为临时对象内部的引用，它很可能只是 nickname 函数中的的一个局部变量。
const std::string& nickname = GenerateDiceRoll().nickname(); // BAD!
```

## 选项四：设计你的函数并使他们不返回对象

很多函数都遵循这种方式，但是也有许多会返回对象，毕竟函数直接返回对象的形式，比传递一个指针作为输出参数的形式可读性要好。

在对临时对象进行操作时，任何返回指向内部的指针或者引用都可能是一个问题。

c_str() 的问题最为明显，protobuf 的 getters 也存在统一的问题。