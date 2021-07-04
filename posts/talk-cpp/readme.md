# Talk C++

<!-- TOC -->

- [Talk C++](#talk-c)
    - [Overview](#overview)
    - [Language Usability Enhancements](#language-usability-enhancements)
        - [Variable Length Array](#variable-length-array)
        - [Constexpr](#constexpr)
            - [Constexpr Var](#constexpr-var)
            - [Constexpr Function](#constexpr-function)
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
