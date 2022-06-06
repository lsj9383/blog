# Putting Things in their Place

Quicklink:

- [目录](../readme.md)
- [原文链接](https://abseil.io/tips/65)

C++11 为标准容器（例如 `std::vector<>`）增加了新的插入方式：**emplace()** 方法族。

这些 **emplace()** 方法直接在容器内部创建对象，而不用先创建临时对象，然后再进行拷贝或移动到容器中。

## 老方式与新方式

让我们通过例子来比较下两种 **std::vector<>** 使用方式。

首先是老 C++ 代码：

```cpp
class Foo {
 public:
  Foo(int x, int y);
  …
};

void addFoo() {
  std::vector<Foo> v1;
  v1.push_back(Foo(1, 2));
}
```

使用 **push_back()** 方法，两个 Foo 对象将会建立：

- 参数的临时 Foo 对象
- 通过临时 Foo 对象，复制构造的 **std::vector** 容器中的 Foo 对象。

我们可以使用 C++11 的 **emplace_back()**，这样只会有一个对象会被构造，该对象即 **std::vector** 中的对象。

由于 `emplace` 系列函数将它们的参数转发给底层对象的构造函数，我们可以直接提供构造函数参数，无需创建一个临时的 Foo：

```cpp
void addBetterFoo() {
  std::vector<Foo> v2;
  v2.emplace_back(1, 2);
}
```

## 使用 Emplace 方法进行 Move-Only 操作

目前我们看到了 **emplace()** 方法对性能的提升，除此外它们也能使不可能的代码变成可能，例如在容器中存储 **std::unique_ptr**。

考虑这个片段：

```cpp
std::vector<std::unique_ptr<Foo>> v1;
```

你如何将值插入到这个 `std::vector` 中呢？一种方法是在 **push_back()** 的参数中直接构造：

```cpp
v1.push_back(std::unique_ptr<Foo>(new Foo(1, 2)));
```

这个代码可以工作，但是比较笨重。也可以通过这样的方式：

```cpp
Foo *f2 = new Foo(1, 2);
v1.push_back(std::unique_ptr<Foo>(f2));
```

这段代码可以编译，但在插入之前它使原始指针的所有权不清楚。

更糟糕的是，vector 现在拥有该对象，但 f2 仍然有效，以后可能会被意外删除。

其他解决方法甚至无法编译，因为 `std::unique_ptr` 不能复制：

```cpp
std::unique_ptr<Foo> f(new Foo(1, 2));
v1.push_back(f);             // Does not compile!
v1.push_back(new Foo(1, 2)); // Does not compile!
```

使用 **emplace()** 方法可以直观的在构造对象时插入，而非构造对象的场景可以使用 **push_back()** 配合 `std::move()` 进行插入：

```cpp
v1.emplace_back(new Foo(1, 2));

std::unique_ptr<Foo> f(new Foo(1, 2));
v1.push_back(std::move(f));
```

通过结合标准迭代器，可以在任意位置上进行插入：

```cpp
v1.emplace(v1.begin(), new Foo(1, 2));
```

也就是说，实际上我们并不希望看到使用 `std::make_unique` 来构造 `unique_ptr` 对象。

**译者疑惑**：

- 构造函数不强调指针是个 unique_ptr，这种信息的省略真的好吗？

## 总结

> We’ve used vector as an example in this Tip, but emplace methods are also available for maps, lists and other STL containers. When combined with unique_ptr, emplace allows for good encapsulation and makes the ownership semantics of heap-allocated objects clear in ways that weren’t possible before. Hopefully this has given you a feel for the power of the new emplace family of container methods, and a desire to use them where appropriate in your own code.

## 附录

```cpp
#include <vector>
#include <string>
#include <iostream>

class Foo {
 public:
  Foo(int x_, int y_) {
    std::cout << "Foo(x, y)" << std::endl;
    x = x_;
    y = y_;
  }

  Foo(const Foo& f) {
    std::cout << "Foo(const Foo& f)" << std::endl;
    x = f.x;
    y = f.y;
  }

  Foo(Foo&& f) {
    std::cout << "Foo(Foo&& f)" << std::endl;
    x = f.x;
    y = f.y;
  }

 public:
  int x;
  int y;
};

void test1() {
  std::cout << "=============== test1 ===============" << std::endl;
  std::vector<Foo> v;
  Foo f(1, 2);
  v.push_back(f);
}

void test2() {
  std::cout << "=============== test2 ===============" << std::endl;
  std::vector<Foo> v;
  v.push_back(Foo(1, 2));
}

void test3() {
  std::cout << "=============== test3 ===============" << std::endl;
  std::vector<Foo> v;
  v.emplace_back(1, 2);
}

int main(int argc, char **argv) {  
  test1();
  test2();
  test3();
}
```

编译后的输出为：

```sh
=============== test1 ===============
Foo(x, y)
Foo(const Foo& f)
=============== test2 ===============
Foo(x, y)
Foo(Foo&& f)
=============== test3 ===============
Foo(x, y)
```
