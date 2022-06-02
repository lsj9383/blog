# Return Policy

很多旧的 C++ 代码库对返回值时的复制对象存在畏惧。幸运的是，我们能够 “复制” 而又不是真正的拷贝对象，这种优化技术被称为返回值优化（[RVO](https://en.wikipedia.org/wiki/Return_value_optimization)）。

RVO 基本上是所有 C++ 编译器都支持的特性。

考虑下面的 C++98 代码，存在一个拷贝构造函数，以及一个赋值构造运算符。并假设这些函数执行的代价非常昂贵：

```cpp
class SomeBigObject {
 public:
  SomeBigObject() { ... }
  SomeBigObject(const SomeBigObject& s) {
    printf("Expensive copy ...\n", ...);
    ...
  }
  SomeBigObject& operator=(const SomeBigObject& s) {
    printf("Expensive assignment ...\n", ...);
    ...
    return *this;
  }
  ~SomeBigObject() { ... }
  ...
};
```

如果针对这个类，有以下工厂方法，你会担忧吗？

```cpp
static SomeBigObject SomeBigObjectFactory(...) {
  SomeBigObject local;
  ...
  return local;
}
```

看起来效率很低效对吗？如果我们运行以下代码会发生什么？

```cpp
SomeBigObject obj = SomeBigObject::SomeBigObjectFactory(...);
```

简单的答案：你可能会认为创建一个临时对象，并且存在两次拷贝构造函数的调用：

- SomeBigObjectFactory 函数中的 local 拷贝给临时对象。
- 临时对象拷贝给 SomeBigObjectFactory 函数外的 obj。

正确的答案是：不打印任何信息，因为复制构造函数和赋值操作都不会发生。

这是怎么发生的？许多 C++ 程序员为了编写高效代码，通常会创建一个对象，并将该对象的地址（指针）传递给函数，该函数使用指针或引用来对原始对象进行操作。

编译器可以将低效代码转换为高效代码，同时也不必 C++ 程序员通过这么复杂繁琐的操作来保证高效。

引用 C++98 标准：每当使用复制构造函数复制临时对象时，允许实现将原始类对象和副本视为引用同一对象的两种不同方式，并且根本不执行复制。对于具有返回类型的函数，如果 return 语句中的表达式是本地对象的名称，允许实现省略创建临时对象。

> Whenever a temporary class object is copied using a copy constructor … an implementation is permitted to treat the original and the copy as two different ways of referring to the same object and not perform a copy at all, even if the class copy constructor or destructor have side effects. For a function with a class return type, if the expression in the return statement is the name of a local object … an implementation is permitted to omit creating the temporary object to hold the function return value …

虽然 C++98 标准中提到的是 **允许**，不具有强制性，但所幸的是目前所有现代的 C++ 编译器，都默认执行 RVO。

## 如何确定编译器执行了 RVO 优化

被调用的函数应该为返回值定义一个单独的变量：

```cpp
SomeBigObject SomeBigObject::SomeBigObjectFactory(...) {
  SomeBigObject local;
  ...
  return local;
}
```

同时调用函数时应该将函数返回值分配给一个新的变量：

```cpp
// No message about expensive operations:
SomeBigObject obj = SomeBigObject::SomeBigObjectFactory(...);
```

通过上面这样的方式，就能使用 RVO 优化。

但是，编译器对于下述情况不会执行 RVO 优化：

- 调用函数时，将返回值传递给一个已经存在的对象（这种情况下通过移动语义可以进行优化）：

  ```cpp
  // RVO won’t happen here; prints message "Expensive assignment ...":
  obj = SomeBigObject::SomeBigObjectFactory(s2);
  ```

- 被调用的函数如果使用了多个不同的对象作为返回值，也无法使用 RVO 优化：

  ```cpp
  // RVO won’t happen here:
  static SomeBigObject NonRvoFactory(...) {
    SomeBigObject object1, object2;
    object1.DoSomethingWith(...);
    object2.DoSomethingWith(...);
    if (flag) {
        return object1;
    } else {
        return object2;
    }
  }
  ```

不过，如果同一个变量在不同的地方进行返回，也是可以进行 RVO 优化的。

```cpp
// RVO will happen here:
SomeBigObject local;
if (...) {
  local.DoSomethingWith(...);
  return local;
} else {
  local.DoSomethingWith(...);
  return local;
}
```

## 还有一个注意点：临时对象

RVO 可以优化临时变量，而不仅仅是有命名的变量。这意味着你可以直接返回一个临时变量，而不用担心拷贝问题，因为者这被 RVO 优化：

```cpp
// RVO works here:
SomeBigObject SomeBigObject::ReturnsTempFactory(...) {
  return SomeBigObject::SomeBigObjectFactory(...);
}

// 在不同的地方使用临时变量，也可以被 RVO 优化
SomeBigObject SomeBigObject::ReturnsTempFactory2(flag) {
  if (flag) {
    return SomeBigObject::SomeBigObjectFactory(...);
  } else {
    return SomeBigObject::SomeBigObjectFactory(...);
  }
}
```

当调用函数立即使用返回值（存储在临时对象）中，也可以被 RVO 优化：

```cpp
// No message about expensive operations:
EXPECT_EQ(SomeBigObject::SomeBigObjectFactory(...).Name(), s);
```

同时需要注意：

- 任何使用临时变量的地方，都可以通过 RVO 优化。

## 附录一：关闭 RVO

我们可以在编译时，设置关闭 RVO 的选项，以便调试。

对于 g++ 而言，可以使用下面的编译选项：

```sh
g++ main.cc -fno-elide-constructors
```

## 附录二：拷贝构造函数和赋值函数

拷贝构造函数和赋值函数有什么区别？

```cpp
class SomeBigObject {
 public:
  SomeBigObject() { ... }
  SomeBigObject(const SomeBigObject& s) {
    printf("Expensive copy ...\n", ...);
    ...
  }
  SomeBigObject& operator=(const SomeBigObject& s) {
    printf("Expensive assignment ...\n", ...);
    ...
    return *this;
  }
  ~SomeBigObject() { ... }
  ...
};

int main(void) {
  SomeBigObject obj1;
  SomeBigObject obj2(obj1);     // 调用拷贝构造函数
  SomeBigObject obj3 = obj1;    // 调用拷贝构造函数

  obj1 = obj3;                  // 调用赋值函数
  return 0;
}
```

## 附录三、参考文献

1. [链接、装载与库——进程的栈](https://kongkongk.github.io/2020/06/29/process-stack/)
