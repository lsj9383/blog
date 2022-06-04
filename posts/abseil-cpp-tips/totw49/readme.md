# Argument-Dependent Lookup

Quicklink:

- [目录](../readme.md)
- [原文链接](https://abseil.io/tips/49)

## 概览

对于一个函数调用，例如： **func(a,b,c)**，该函数名没有使用 **::** 范围运算符，这种称为`无限定(unqualified)`。

当 C++ 代码使用一个无限定的函数名时，编译器将搜索匹配的函数声明。

令人惊讶的是，除了调用者的词法范围外，搜索范围还会被扩充。而扩充的部分是：与函数参数类型关联的命名空间。

这种额外的查找，被称作 `ADL（基于参数的查找）`。

## 名称查找基础

一个函数调用一定会被编译器映射到一个函数定义，这种匹配是在两个独立的串行阶段处理完成的。

- 首先，在名称查找阶段，名称查找将会应用一些范围搜索规则，找到一组函数名匹配的重载。
- 然后，在重载解析阶段，采用该名称搜索查找出来的重载，并尝试为调用给出参数，选择最佳匹配的重载。

名称查找阶段作为第一个阶段，它不会尝试函数是否匹配，甚至不考虑参数个数是否匹配，它只是在作用域中搜索函数名。

重载解析阶段是另外一个复杂的话题，这里不做讨论。

最常见的搜索是在调用的作用域范围向外搜索：

```cpp
namespace b {

void func();

namespace internal {

void test() { func(); } // ok: finds b::func().

} // b::internal
} // b
```

这样的查找与 ADL 无关（毕竟函数连参数都没有），这只是函数调用位置向外搜索：

1. 首先在函数的作用域
1. 再到类作用域
1. 再到封闭类作用域
1. 然后到命名空间作用域
1. 接着到封闭命名空间
1. 最后到 **::** 全局命名空间

随着查询的范围逐步扩大，只要找到具有目标名称的函数（仅看函数名，不看参数），这个范围扩大过程就会停止。

同时，当前范围内的所有相同名称函数都会被搜索出来，这些同名函数则是后面重载解析的输入。

```cpp
namespace b {

void func(const string&);  // b::func

namespace internal {

void func(int);  // b::internal::func

namespace deep {

void test() {
  string s("hello");
  func(s);  // error: finds only b::internal::func(int).
}

}  // b::internal::deep
}  // b::internal
}  // b
```

由于在名称查找阶段不考虑参数类型，因此编译器找到了一个叫做的东西 func 并停在 **b::internal** 作用域，随后找到该作用域中的所有 func 重载，并匹配最佳的函数。

所以重载解析阶段，甚至从未没见过 `b::func(const string&)` 函数。

作用域搜寻的一个重要含义是：搜索顺序中较早出现的作用域中的重载，会对后面的作用域隐藏重载。

> An important implication of the scoped search order is that overloads in a scope appearing earlier in the search order will hide overloads from later scopes.

## 基于参数的查找（Argument-Dependent Lookup - ADL）

当一个函数传递参数，会执行更大范围的名字查询。这些额外的查找主要是参考了调用参数关联的命名空间，这种查找方式叫做 ADL。

如此，在名称查找阶段，会进行以下并行查找：

- 调用点的作用域查找（也被称为词法查找）。
- 所有参数的 ADL。

以上并行查找结果合并在一起，作为函数重载集，在重载解析阶段会匹配其中最佳匹配的函数。

参考以下示例：

```cpp
namespace aspace {

struct A {};

void func(const A&);  // found by ADL name lookup on 'a'.

}  // namespace aspace

namespace bspace {

void func(int);  // found by lexical scope name lookup

void test() {
  aspace::A a;
  func(a);  // aspace::func(const aspace::A&)
}

}  // namespace bspace
```

针对 `func(a)` 的调用，编译器会启动两个名称查找：

- 词法查找（调用点作用域的查找）。
- 参数 a 的 ADL。

对于词法查找的顺序如下：

- 首先在 `bspace::test()` 的空间中，没有找到 `func()`，因此向外扩搜索范围。
- 接着在 `bspace` 的空间中，找到了 `func(int)`，停止外扩搜索范围。

对于参数 a 的 ADL 顺序如下：

- 首先在 `aspace` 的空间（参数 a 的空间）中命名查询。
- 查到了 `func(const A&)`，停止外扩搜索。

如此，重载解析有两个候选者：`func(int)` 和 `func(const A&)`，很明显，最终会选择 `func(const A&)`。

## 类型相关的命名空间

前面的 ADL 是一个简单的例子，一个复杂的类（比如模板类）可能并不会关联一个命名空间，而是会关联很多命名空间，这些空间都会被作为 ADL 搜索的扩展。

例如单个参数类型为 `a::A<b::B, c::internal::C*>`，ADL 会涉及：

- `namespace a`
- `namespace b`
- `namespace c::internal`

下面是一个更具体的例子：

```cpp
namespace aspace {

struct A {};
template <typename T> struct AGeneric {};
void func(const A&);
template <typename T> void find_me(const T&);

}  // namespace aspace

namespace bspace {

typedef aspace::A AliasForA;
struct B : aspace::A {};
template <typename T> struct BGeneric {};

void test() {
  // ok: base class namespace searched.
  func(B());
  // ok: template parameter namespace searched.
  find_me(BGeneric<aspace::A>());
  // ok: template namespace searched.
  find_me(aspace::AGeneric<int>());
}

}  // namespace bspace
```

## 注意事项

在理解名称查找后，考虑以下事项，可能会对你有所帮助。

### 类型别名

通过 `typdef` 和 `using` 可以为类型声明别名，但是别名和原类型可能并不在相同的命名空间中。

需要注意的是，在进行命名查找前，编译器已经将别名换算成了原类型，因此其实是在原类型的命名空间中进行搜索的。

由于 typedef 和 using 的存在，可能会让你对搜索的空间做误判。

```cpp
namespace aspace {

struct A {};

}  // namespace aspace

namespace bspace {

using AliasForA = aspace::A;

}  // namespace bspace

namespace cspace {

// ok: note that this searches aspace, not bspace.
void test() {
  func(bspace::AliasForA());
}

}  // namespace cspace
```

### 迭代器

小心迭代器，因为你并不知道迭代器到底关联的命名空间是什么。因此不要依赖 ADL 来解决依赖迭代器的函数调用。

它们可能关联了指向的元素，也可能关联的是容器的命名空间（无关实现的私有命名空间）。

```cpp
namespace d {
int test() {
  std::vector<int> vec(a);
  // maybe this compiles, maybe not!
  return count(vec.begin(), vec.end(), 0);
}
}  // namespace d
```

### 重载运算符

重载运算符本质上就是一个函数，例如 `operator+(a, b)` 或 `operator<<(a, b)`，并且重载运算符调用时，都是非限定的调用。

ADL 最重要的应用场景之一，就是 `operator<<` 使用的搜索，例如 `std::cout << obj`，这就像是调用了非限定函数一样：

```cpp
operator<<(std::ostream&, const O::Obj&)
```

因此，他会通过 ADL 去 `namespace std` 的范围查找，也会去 `namespace O` 的范围查找，当然也会在调用的词法范围去查找。

可见，将这些运算符放置在与它们要操作的用户定义类型相同的命名空间中很重要。

假设把 `operator<<` 对 `O::obj` 的操作，重载到全局空间中，那么不小心在 `namespace O` 下放置了一个对其他类型的 `operator<<` 重载，那么编译器就永远也找不到 `operator<<(std::ostream&, const O::Obj&)` 了，因为在 `namespace O` 中就找到了运算符，所以停止向外搜索了。

因此，最好遵循的原则是将 `operator<<` 放置到离对象最近的地方：

> It takes a bit of discipline but saves a lot of confusion later to follow the simple rule of defining all operators and other associated nonmember functions next to the type’s definition in the same namespace.

### 基本类型

基本类型（例如 int, float）与名称空间无关，这些类型的参数是不会启动 ADL 的。

对于指针，则是看其指向的类型。

对于数组，则是看起元素的类型。
