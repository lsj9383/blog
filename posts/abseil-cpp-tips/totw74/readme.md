# Delegating and Inheriting Constructors

Quicklink:

- [目录](../readme.md)
- [原文链接](https://abseil.io/tips/74)

当一个类具有多个构造函数，往往这些构造函数执行的初始化操作是比较类似的，在很多老版的 C++ 类实现中会使用一个私有的 **SharedInit()** 方法，如下所示：

```cpp
class C {
 public:
  C(int x, string s) { SharedInit(x, s); }
  explicit C(int x) { SharedInit(x, ""); }
  explicit C(string s) { SharedInit(0, s); }
  C() { SharedInit(0, ""); }
 private:
  void SharedInit(int x, string s) { … }
};
```

C++11 提供了一种新的机制：委托构造函数（delegating constructors）。

通过允许使用一个构造函数去定义另一个构造函数，可以使此类场景处理起来更加清晰可读：

```cpp
class C {
 public:
  C(int x, string s) { … }
  explicit C(int x) : C(x, "") {}
  explicit C(string s) : C(0, s) {}
  C() : C(0, "") {}
};
```

需要注意的是，如果该构造函数使用了代理，那么该构造函数就不能使用成员初始化列表了：

```cpp
class C {
 public:
  C(int x, string s) { … }
  explicit C(int x) : C(x, "") {}
  explicit C(string s) : C(0, s), x(10) {}      // 编译失败，不能使用成员初始化列表
  C() : C(0, "") {}

 public:
  int x = 0;
};
```

**注意：**

- 在委托构造函数返回前，对象被认为是不完整的。这一点对于存在异常抛出的情况下，是比较重要的，因为这会让对象处于未完成状态。

另外，在继承一个具有多个构造函数的类时，会出现另一种不太常见的构造函数代码重复形式。

例如，考虑一个 C++ 的简单子类，它仅仅包含一个方法：

```cpp
class D : public C {
 public:
  void NewMethod();
};
```

但是 D 的构造函数呢？只有默认生成的构造函数，如果要继承构造函数，我们需要添加 D 的构造函数并转发给 C 才行：

```cpp
class D : public C {
 public:
  D(int x, string s) : C(x, s) {}
  explicit D(int x) : C(x) {}
  explicit D(string s) : C(s) {}
  explicit D() : C() {}

 public:
  void NewMethod();
};
```

我们希望简单的充要 C 的构造函数，而不是写出他们的转发。C++11 中通过新的**继承构造函数**机制来实现这一点：

```cpp
class D : public C {
 public:
  using C::C;  // inherit all constructors from C
  void NewMethod();
};
```

**注意：**

- 只有当子类没有新的数据成员才应该使用继承构造函数。实际上，C++ 代码风格中时反对使用继承构造函数的，除非新成员具有类内初始化（类内初始化就是类内默认初始化）。
