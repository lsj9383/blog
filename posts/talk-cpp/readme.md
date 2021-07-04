# Talk C++

<!-- TOC -->

- [Talk C++](#talk-c)
    - [Overview](#overview)
    - [Language Usability Enhancements](#language-usability-enhancements)
        - [Variable Length Array](#variable-length-array)
        - [Constexpr](#constexpr)
            - [Constexpr Var](#constexpr-var)
            - [Constexpr Function](#constexpr-function)
            - [Constexpr If](#constexpr-if)
        - [If/Switch Define Var](#ifswitch-define-var)
        - [Initializer List](#initializer-list)
        - [Aggregate initialization](#aggregate-initialization)
        - [Structured bindings](#structured-bindings)
        - [Type Inference](#type-inference)
    - [Class Constructor](#class-constructor)
        - [Synthesized Constructor](#synthesized-constructor)
        - [Default Constructor](#default-constructor)
        - [Converting Constructor](#converting-constructor)
        - [List](#list)
        - [Delete Constructor](#delete-constructor)
        - [Const Overload](#const-overload)
    - [Left/Right Value](#leftright-value)
    - [Template](#template)
    - [Lambda](#lambda)
    - [References](#references)

<!-- /TOC -->

## Overview

作为一名长期 C With Class 的程序员，很惭愧没有深入学习过 C++ 的特性，几乎是会涉及到什么特性才会去看某个特性。

为了便于本人回顾翻阅，本文不定期更新，记录 C++ 中或常见，或生涩的特性。

## Language Usability Enhancements

C++ 11/14 关于编译时行为的一些强化在本章展示，本节源于 [现代 C++ 教程](https://changkun.de/modern-cpp/zh-cn/00-preface/) 的第 2 章，但在此基础上做了很多补充。

### Variable Length Array

C++ 的数组似乎是一个简单的问题，毕竟在 C 语言中就存在，一直沿用至今。这是一个数组定义的 Demo：

```cpp
int main() {
  int nums[10];
  return 0;
}
```

上述 Demo 定义了一个数组，数组有 10 个元素。定义数组时，我们通常要求数组的长度在编译期已知，即是一个常量表达式。在 ISO C++ 中要求：

> ISO C++ 不允许变长数组。

下面是一个不合法的定义：

```cpp
int main() {
  int size = 10;
  // size 是变量，编译期不可知，所以是错误的
  int nums[size];
  return 0;
}
```

有意思的问题来了：`用 g++ 编译上面的代码是没有问题的`。

这在 Stackoverflow 中也有相关讨论：[C++ declare an array based on a non-constant variable?](https://stackoverflow.com/questions/19473638/c-declare-an-array-based-on-a-non-constant-variable)。

这其实是由编译器进行的非标准 C++ 扩展，但若我们在 g++ 编译时，强制使用 ISO C++ 标准，编译器仍然是会报错的：

```sh
g++ main.cc -pedantic-errors -std=c++1y
main.cc: 在函数‘int main()’中:
main.cc:4:16: 错误：ISO C++ 不允许变长数组‘nums’ [-Wvla]
   int nums[size];
```

这个扩展其实来自于对 C99 的变长数组（Variable Length Array - VLA）支持。关于变长数组的更多信息可以参考：[C 语言中的变长数组与零长数组](https://xhy3054.github.io/c-ArrayOfVariableLength/) 和 [6.20 Arrays of Variable Length](https://gcc.gnu.org/onlinedocs/gcc/Variable-Length.html)。

### Constexpr

`constexpr` 是 C++ 11 引入的关键字，可以用于修饰变量和函数，指出这是一个常量表达式。

我们先看一下什么是常量表达式，这在 C++ Primer 中如此提到：

> 常量表达式是指值不会改变，并且编译过程就能得到计算结果的表达式。

#### Constexpr Var

字面量都属于常量表达式，对于非字面量，一个常量表达式由数据类型和初始值共同决定：

- 数据类型是只读类型，即 `const`（也可以是经由 `constexpr` 修饰的类型），例如：

  ```cpp
  const int a = 0;
  constexpr int b = 1;
  ```

- 初始值必须是常量表达式，例如：

  ```cpp
  const int b = 5;      // b 是常量表达式，字面量是常量表达式。
  const int c = b;      // c 是常量表达式，因为初始值 b 是个常量表达式

  int n = 10;
  const int a = n;      // a 不是常量表达式，因为初始值不是常量表达式
  ```

很明显，判断常量表达式是比较麻烦，从数据类型修饰上我们并不能判断是否为常量表达式。那我们如何保证一个变量是常量表达式呢？constexpr 就该出场了：

- constexpr 修饰的变量，编译器会在编译期判断是否为常量表达式，如果不是常量表达式，就不能编译通过。

通过 `constexpr` 修饰变量，可以由编译器保证这是常量表达式，这是一个错误的 Demo：

```cpp
int main() {
  int n = 10;
  constexpr int a = n;
  return 0;
}
```

编译后会有错误提示：

```sh
$ g++ test.cc
test.cc: In function ‘int main()’:
test.cc:3:21: error: the value of ‘n’ is not usable in a constant expression
   constexpr int a = n;
                     ^
test.cc:2:7: note: ‘int n’ is not const
   int n = 10;
```

#### Constexpr Function

上面是 constexpr 对变量的修饰，那么当 constexpr 对函数修饰时，是什么含义呢？

C++ Primer 指出：

> constexpr 函数是指能用于常量表达式的函数。

constexpr function 返回值也是常量表达式，因此 constexpr function 可以在编译期间就能计算出函数结果，而不用在运行时计算。

不过需要指出的是，C++ 11 和 C++ 14 对 constexpr function 的约束是非常不同的。

先看 C++ 11 对 constexpr function 的约束：

- 函数的返回类型，所有参数类型，都必须是常量表达式。
- 函数体必须只有一条 return 语句。

因此，在 C++ 11 中，这样定义 constexpr function 是有效的：

```cpp
constexpr int fun(int n) {
  return n;
}

int main() {
  constexpr int a = fun(10);
  return 0;
}
```

但是下面的搞法在 C++ 11 中都是无效的：

```cpp
constexpr int fun(int n) {
  if (n < 0) {
    return 0;
  }
  return n;
}

int main() {
  constexpr int a = fun(10);
  return 0;
}
```

可以看到编译错误：

```sh
# 需要指定 C++ 11 编译
$ g++ test.cc -std=c++11
test.cc: In function ‘constexpr int fun(int)’:
test.cc:6:1: error: body of ‘constexpr’ function ‘constexpr int fun(int)’ not a return-statement
 }
 ^
test.cc: In function ‘int main()’:
test.cc:9:24: error: ‘constexpr int fun(int)’ called in a constant expression
   constexpr int a = fun(10);
```

但是 C++ 14 中 constexpr function 的条件更加宽松，并且是否真的作为编译期运行也将视其使用环境而定。

C++ 14 中 constexpr function 中可以编写复杂的逻辑语句，包括条件判断，函数调用，循环等等。并当 constexpr function 不满足编译期运行条件时，会在运行时执行。

例如这是一个 constexpr function 在编译期间运行的例子：

```cpp
constexpr int fun(int n) {
  for (int i = 0; i < 1000; ++i) {
    for (int j = 0; j < 100; ++j) {
      for (int k = 0; k < 50; ++k) {}
    }
  }
  return n;
}

int main() {
  const int n = 10;
  int a = fun(n);
  return 0;
}
```

当执行 `g++ test.cc -std=c++14` 时，可以明显感受到编译变慢，这是因为 constexpr function 满足编译期间执行的条件，而它在其中进行了延时。

但若如下编码：

```cpp
constexpr int fun(int n) {
  for (int i = 0; i < 1000; ++i) {
    for (int j = 0; j < 100; ++j) {
      for (int k = 0; k < 50; ++k) {}
    }
  }
  return n;
}

int main() {
  int n = 10;
  int a = fun(n);
  // constexpr int b = fun(n);  // 错误，因为 fun(n) 返回的已经不再是常量表达式了。
  return 0;
}
```

执行 `g++ test.cc -std=c++14` 并不会感受到编译变慢，而是在运行时感受到变慢，这是因为 constexpr function 不满足编译时运行的条件，因此在编译期间不运行。当这种情况时，constexpr function 返回的已不再是 constexpr 了，因此若使用 `constexpr int b = fun(n)` 会编译错误。

更多 C++ 11/14 在 constexpr 相关的限制，可以参考 [constexpr](https://zh.wikipedia.org/wiki/Constexpr)。

#### Constexpr If

在 C++ 17 开始，可以为 if 语句使用 constexpr，以提前计算出常量表达式会使用的分支，具体请看：[if statement](https://en.cppreference.com/w/cpp/language/if)。

Constexpr If 要求 if 的 condition express 是一个常量表达式：

```cpp
#include <iostream>
  
int main() {
  constexpr int a = 10;
  if constexpr (a) {
    std::cout << "if" << std::endl;
  } else {
    std::cout << "else" << std::endl;
  }
  return 0;
}
```

要求使用 C++ 17 进行编译：`g++ test.cc -std=c++17`。

### If/Switch Define Var

我们在 for 循环语句中非常容易定义一个仅在 for 语句块内使用的变量：

```cpp
for (int i = 0; i < 10; ++i) {}
```

但是在以前，并不能定义仅 if/switch 语句块内使用的变量。

在 C++ 17 对仅用作 if/switch 语句块的变量做了支持，可以参考 [selection statements with initializer](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2016/p0305r1.html)。

```cpp
int main() {
  if (int number = 10; number < 10) {
    return 0;
  } else {
    return number;
  }
}
```

switch 语句也是类似的。

### Initializer List

在 C++ 11 中开始提供了 Initializer List，详情可以参考 [std::initializer_list](https://en.cppreference.com/w/cpp/utility/initializer_list)。

这个命名其实不是太好，容易和类成员函数的初始化列表搞混淆，因此一定要注意区分。在 cppreference.com 中提到：

> not to be confused with member initializer list.

```cpp
template < class T >
class initializer_list;
```

`std::initializer_list` 是一个容器，里面引用了多个 T 类型的对象，并提供了对 `const T` 的访问。

我们开发 C++ 代码通常不会主动去构造 initializer_list，而是由 C++ 自动进行 initializer_list 的构造，因此我们需要看 C++ 有些自动构造 initializer_list 的场景：

- 通过花括号初始化列表，进行列表初始化一个对象时，相应的构造函数会接收一个 `std::initializer_list` 对象：

  ```cpp
  class MagicFoo {
   public:
    MagicFoo(std::initializer_list<int> list) {}
  };

  int main() {
    // 列表初始化
    MagicFoo a = {1, 2, 3, 4, 5};
    MagicFoo b{1, 2, 3, 4, 5};
  }
  ```

- 花括号初始化列表作为赋值运算符右值时，或者作为函数参数调用时，相应函数会接收一个 `std::initializer_list` 对象。

  ```cpp
  class MagicFoo {
   public:
    test(std::initializer_list<int> list) {}
    MagicFoo& operator=(std::initializer_list<int> list) { returh *this; }
  };

  int main() {
    // 列表初始化
    MagicFoo a;
    a.test({1, 2, 3, 4, 5});
    a = {1, 2}
  }
  ```

- a braced-init-list is bound to auto, including in a ranged for loop.

  ```cpp
  auto al = {10, 11, 12};             // al 是 std::initializer_list

  for (int x : {-1, -2, -3}) {        // {-1, -2, -3} 这个临时变量是 std::initializer_list
    std::cout << x << std::endl;
  }
  ```

### Aggregate initialization

聚合初始化，是在 [Initializer List](#initializer-list) 基础上的延申，可以参考 [Aggregate initialization](https://en.cppreference.com/w/cpp/language/aggregate_initialization)。

虽然在 [Initializer List](#initializer-list) 中，`{}` 中的所有元素类型必须相同，但是在 `Aggregate initialization` 场景下，`{}` 的每个元素类型不必相同。

[Aggregate initialization](https://en.cppreference.com/w/cpp/language/aggregate_initialization) 列出了满足聚合的条件，我们直接看聚合初始化的效果：

```cpp
// demo 1
struct A { int x; int y; int z; };
A a{.y = 2, .x = 1}; // error; designator order does not match declaration order
A b{.x = 1, .z = 2}; // ok, b.y initialized to 0


// demo 2
union u { int a; const char* b; };
u f = { .b = "asdf" };         // OK, active member of the union is b
u g = { .a = 1, .b = "asdf" }; // Error, only one initializer may be provided

// demo 3
struct A {
  string str;
  int n = 42;
  int m = -1;
};
A{.m=21}  // Initializes str with {}, which calls the default constructor
          // then initializes n with = 42
          // then initializes m with = 21
```



### Structured bindings

Structured bindings 是类似于其他脚本语言将一个集合拆成多个变量的技术，例如在 python 中，可以把一个二维数组进行拆分：

```python
a = [1, 2]
x, y = a
# x == 1
# y == 2
```

C++ 17 支持类似的语法，这在 C++ 中叫做结构化绑定，可以参考 [Structured binding declaration](https://en.cppreference.com/w/cpp/language/structured_binding)。

结构化绑定支持三种类型：

- 绑定一个数组：

  ```cpp
  int a[2] = {1,2};
 
  auto [x,y] = a;       // creates e[2], copies a into e, then x refers to e[0], y refers to e[1]
  auto& [xr, yr] = a;   // xr refers to a[0], yr refers to a[1]
  ```

- 绑定一个 tuple-like 类型:

  ```cpp
  std::tuple<int, double, bool> tup(10, 5.3, true);
  const auto& [a,b,c] = tup;
  ```

- 绑定一个 Class Member

  ```cpp
  class A {
   public:
    int a = 10;
    bool b = true;
  };

  A a;
  auto [x, y] = a;
  ```


### Type Inference

通过 `auto` 关键词作为变量的类型说明符，可以让编译器分析表达式推导出变量类型。

auto 让编译器通过初始值来推算变量类型，也因此，auto 的变量必须要由初始值：

```cpp
auto i = 10;

std::vector<int> vect; 
for(auto it = vect.begin(); it != vect.end(); ++it) {
  std::cin >> *it;
}

auto ptr = [](double x){return x*x;};

template <class T, class U>
void Multiply(T t, U u) {
  auto v = t * u;
  std::cout << v;
}

// C++ 14 支持返回值是 auto 类型
auto add(int x, int y) {
  return x + y;
}
```

auto 的推到规则并非表面那么简单，尤其是在考虑复合类型时，例如 const，指针，引用等场景，可以参考：[auto(C++)](https://zh.wikipedia.org/wiki/Auto_(C%2B%2B))。

简单来说，auto 作为类型推导时，会施加以下规则：

1. 如果初始化表达式是引用，首先去除引用；
1. 如果剩下的初始化表达式有顶层的 const 且/或 volatile 限定符，去除掉。

```cpp
const int v1 = 101;
auto v2 = v1;           // v2 类型是 int，脱去初始化表达式的顶层 const

int v3 = 10;
int& v4 = v3;
auto v5 = v4;           // v5 类型是 int，去除掉引用
```

**注意：**

- 顶层 const，表示任意对象是个常量。
- 底层 const，表示指针或引用指向的对象是个常量。
- 对于指针可以简单的记作，靠右的 const 是顶层 const，靠左的 const 是底层 const。

如果要保留顶层 const，可以为 auto 添加 const 限定符：

```cpp
const int v1 = 101;
const auto v2 = v1;       // v2 是 const int 类型
```

如果要使用引用，也需要明确指定，并且如果使用了引用，顶层 const 不会被剔除：

```cpp
int v1 = 101;
auto& v2 = v1;

const int v3 = 10;
auto& v4 = v3;      // v4 是 const int&
```

auto 的使用也有一些限制：

- auto 不能用于函数传参，这种情况应该使用模板。
- auto 还不能用于推导数组类型。

C++ 11 还提供了 `decltype` 关键词，它可以根据表达式推导变量类型，又不需要像 auto 那样必须要提供初始值：

```cpp
int fun() {
  return 10;
}

int main(void) {
  decltype(fun()) a;      // a 是 int 类型
  decltype(10 + 20) b;    // b 是 int 类型
  return 0;
}
```

decltype 进行推导时，并不会进行实际的表达式运算，只会根据表达式的类型去分析。

decltype 的推导规则和 auto 稍有不同，这里不详细列出，具体可参考 [decltype specifier](https://en.cppreference.com/w/cpp/language/decltype)。

decltype 比较常见的场景是为模板函数的返回值进行类型推导，因为在 C++ 14 前，我们不能定义 auto 类型的返回值，因此为了让模板函数可以自行推导返回值，我们使用 decltype:

```cpp
template<typename T, typename U>
auto add2(T x, U y) -> decltype(x+y) {
    return x + y;
}
```

所幸的是，这在 C++ 14 中得到了解决，C++ 14 中可以直接使用 auto 进行返回了，这更方便：

```cpp
template<typename T, typename U>
auto add2(T x, U y) {
    return x + y;
}
```

## Class Constructor

### Synthesized Constructor

### Default Constructor

参考 C++ Primer 中对默认构造函数的定义：

> 没有提供任何实参时使用的构造函数。

很明显，根据这个定义，无论是编译器自动生成的还是我们自己实现的，只要构造函数没有任何参数，就是默认构造函数，例如：

```cpp
// 编译器自动生成默认构造函数
class A {
};

// 编译器自动生成默认构造函数
class B {
 public:
  B() = default;
}

// 自己实现的默认构造函数
class C {
 public:
  C() {}
};
```

我们在看代码和写代码时，往往涉及到 `= defualt`，什么时候使用它呢？

默认构造函数会有编译器自动生成，但是当编译器中定义构造函数后，编译器就不会自动生成默认构造函数了：

```cpp
// 生成默认构造函数
class A {
};

// 不生成默认构造函数
class B {
 public:
  B(int num) {}
};

int main() {
  A a;            // 编译正确
  B b(10);        // 编译正确
  B b;            // 编译错误，因为不具备 B 的默认构造函数
}
```

但是我们实际上可能需要编译器自动生成的默认构造函数，为了维持编译器自动生成这一行为，就可以使用 `= default`：

```cpp
class C {
 public:
  C() = default;
  C(int num) {}
};

int main() {
  C b(10);        // 编译正确
  C b;            // 编译正确
}
```

那么编译器自动生成的默认构造函数具备哪些行为呢？其实编译器自动生成的默认构造函数，就是调用父类的默认构造函数，并初始化每个成员变量。为了更形象的说明，以下 A、B、C 类的默认构造函数行为其实是一样的：

```cpp
// 编译器自动生成默认构造函数
class A {
};

// 编译器自动生成默认构造函数
class B {
 public:
  B() = default;
}

// A 和 B 的默认构造函数其实和这个一样
class C {
 public:
  C() {}
};
```

既然如此，为什么当我们需要定义默认构造函数时，会选择使用 `ClassName() = default` 不直接使用 `ClassName() {}` 呢？

其实是为了区别于 `编译器实现` 和 `用户实现`，前者是编译器实现，后者是用户实现。使用 `ClassName() = default` 会更加规范和统一，并为阅读者强调，这是编译器实现的默认构造函数，而不是用户实现的。

对于这个问题，更多信息可以参考 [The new syntax “= default” in C++11](https://stackoverflow.com/questions/20828907/the-new-syntax-default-in-c11) 和 [How is “=default” different from “{}” for default constructor and destructor?](https://stackoverflow.com/questions/13576055/how-is-default-different-from-for-default-constructor-and-destructor) 的讨论。

C++ Primer 中提到的最佳实践：

> 在实际中，如果定义了其他构造函数，那么最好也提供一个默认构造函数。

### Converting Constructor

转换构造函数在 C++ Primer 中的定义：

> 可以用一个实参调用的非显示构造函数。这样的函数隐式地将参数类型转换为类类型。

其本质上就是有单个参数的构造函数，这类构造函数都属于一个 Converting Consructor。这在函数传值，以及赋值时往往可以看到：

```cpp
class A {
 public:
  A(int num) : num_(num) {}
  int num() { return num_; }

 private:
  int num_;
};

void fun(A a) {
}

int main() {
  // 触发 Converting Constructor
  A a1(30);

  // 触发 Converting Constructor
  A a2 = 30;

  // 触发 Converting Constructor
  fun(30);
}
```

多数情况，都不希望进行隐式的类型转换，此时可以定义 `explicit` 关键字：

```cpp
class A {
 public:
  explicit A(int num) : num_(num) {}
  int num() { return num_; }

 private:
  int num_;
};

void fun(A a) {
}

int main() {
  A a1(30);     // 正常
  fun(A(30));   // 正常，触发单参数构造函数（等价于 A a = A(30)）

  A a2 = 30;    // 失败，不能进行隐式转换
  fun(30);      // 失败，不能进行隐式转换
}
```

Google C++ Code Style 会建议我们：

> 不要定义隐式类型转换. 对于转换运算符和单参数构造函数, 请使用 explicit 关键字.

### List 

### Delete Constructor


### Const Overload

## Left/Right Value

## Template

## Lambda

## References

1. [现代 C++ 教程](https://changkun.de/modern-cpp/zh-cn/00-preface/)
1. [Google C++ 风格指南](https://zh-google-styleguide.readthedocs.io/en/latest/google-cpp-styleguide/contents/)
1. [C++ 11 智能指针的简单对比](https://simonfang1.github.io/blog/2018/08/23/smart-pointer/)
1. [C 语言中的变长数组与零长数组](https://xhy3054.github.io/c-ArrayOfVariableLength/)
1. [6.20 Arrays of Variable Length](https://gcc.gnu.org/onlinedocs/gcc/Variable-Length.html)
1. [Selection statements with initializer](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2016/p0305r1.html)
1. [Structured binding declaration](https://en.cppreference.com/w/cpp/language/structured_binding)
