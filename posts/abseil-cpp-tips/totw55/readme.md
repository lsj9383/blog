# Name Counting and unique_ptr

Quicklink: [Abseil：C++ Tips of the Week](../readme.md)

由于对 `std::unique_ptr` 的行为要求，我们需要确保任何保存在 `std::unique_ptr` 中的值，只有一个名称。

需要注意的是，C++ 委员会为 `std::unique_ptr` 选择了一个非常恰当的名称：任何存储在 `std::unique_ptr` 中的非空指针值，在任意时刻都只能出现在一个 std::unique_ptr 中，同时标准库设计时也会突出这种特性。

对使用 `std::unique_ptr` 的代码进行编译时，遇到的大部分问题都可以通过识别如何计算 `std::unique_ptr` 的名称来解决：一个名称是可以的，但是一个指针值有多个名称是不行的。

> Many common problems compiling code that uses std::unique_ptr can be resolved by learning to recognize how to count the names for a std::unique_ptr: one is OK, but multiple names for the same pointer value are not.

让我们为这些名字计数：在每一行计算在该点活动的名称数量，这些名称引用包含相同指针的 `std::unique_ptr`。 如果您发现同一指针值具有多个名称的任何行，那就是错误！

```cpp
std::unique_ptr<Foo> NewFoo() {
  return std::unique_ptr<Foo>(new Foo(1));
}

void AcceptFoo(std::unique_ptr<Foo> f) { f->PrintDebugString(); }

void Simple() {
  AcceptFoo(NewFoo());
}

void DoesNotBuild() {
  std::unique_ptr<Foo> g = NewFoo();
  AcceptFoo(g); // DOES NOT COMPILE!
}

void SmarterThanTheCompilerButNot() {
  Foo* j = new Foo(2);
  // Compiles, BUT VIOLATES THE RULE and will double-delete at runtime.
  // 编译可以通过，但违反规则，这将导致在运行时双重删除（对 j 指向的内存重复释放）。
  std::unique_ptr<Foo> k(j);
  std::unique_ptr<Foo> l(j);
}
```

在 **Simple()** 函数中，用 **NewFoo()** 分配的 `std::unique_ptr` 只有 **AcceptFoo()** 中的名称 **f**（存在临时变量，但临时变量不认为是有名称）。

对于 **DoesNotBuild()** 函数，其中使用 **NewFoo()** 分配的 `std::unique_ptr` 有两个引用它的名称：

- **DoesNotBuild()** 中的名称 **g**。
- **AcceptFoo()** 中的名称 **f**。

因此在 **DoesNotBuild()** 中存在典型的唯一性违规：

```sh
scratch.cc: error: call to deleted constructor of std::unique_ptr<Foo>'
  AcceptFoo(g);
```

即使编译器没有拦截你，运行时的 `std::unique_ptr` 的行为也会存在问题。

例如在 **SmarterThanTheCompilerButNot()** 函数中，引入了多个 `std::unique_ptr` 的名称，它可能会编译通过，但是在运行时会遇到内存问题。

现在的问题变成了：如何删除一个名称？C++ 中提供了一种解决方法，即 `std::move()`。

```cpp
 void EraseTheName() {
   std::unique_ptr<Foo> h = NewFoo();
   AcceptFoo(std::move(h)); // Fixes DoesNotBuild with std::move
}
```

调用 `std::move()` 实际上是执行了一个名称删除器：从概念说你停止了名称 **h** 作为一个名称对指针的计数。

这将通过名称规则：在分配给 **NewFoo()** 的 `std::unique_ptr` 上有一个名称 **h**，并且在对 **AcceptFoo()** 的调用中再次只有一个名称 **f**。 通过使用 `std::move()`，我们保证在为它分配新值之前不会再次读取 **h**。

对于不熟悉左值、右值等微妙之处的人来说，名称技术是一个方便的技巧：它可以帮助你识别出不必要的副本的可能性，并且帮助你正确的使用 `std::unique_ptr`。

计数后，如果你发现某个点的名词过多，使用 `std::move()` 去擦除不需要的名词。
