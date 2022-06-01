# Prefer Factory Functions to Initializer Methods

Quicklink: [Abseil：C++ Tips of the Week](../readme.md)

在不使用 C++ 异常机制的环境中（Google 的 C++ 编程通常很少使用异常机制，可以参考 [Exceptions](https://google.github.io/styleguide/cppguide.html#Exceptions)），C++ 构造函数必须成功，因为他们没有办法向外暴露任何失败。

当然，你可以在构造函数失败时，调用 **abort()**，但是这种方式会让整个进程停掉，这种形式在代码中通常无法接受。

如果你的构造函数逻辑无法避免失败的可能，一种通用的方式是添加一个初始化方法（即 `init method`），该初始化方法负责所有的初始化工作，如果存在失败会通过返回值返回失败信息。

这种形式要求开发者：

- 构造函数生成对象
- 调用初始化方法
- 初始化失败立即销毁对象

然而这样的形式仅仅是假设开发者会这样使用，开发者很有可能并不遵循这样的使用方式。因此开发者很可能在初始化方法调用前，或者初始化方法调用失败后，去调用其他的方法。

因此这种方式要求你维护一个对象状态，通常是三种：

- 已初始化
- 未初始化
- 初始化失败（很多时候，可以和未初始化归并未相同的状态）

这样的设计要求遵循很多原则：对象的每个方法都必须指明可以调用的状态，用户也需要了解并遵守这些规则。

因为如果不遵循这样的原则进行实现，客户端人员更加倾向于编写任何可以工作的代码，而不管你打算支持什么。当这种情况发生时，可维护性就会急剧下降（参考 [Hyrum's Law](https://www.hyrumslaw.com/)）。

幸运的是，对于这样的场景存在简单替代方案：提供一个工厂函数，它创建和初始化对象实例，并返回他们的`指针`或 `absl::optional`，使用 null 标识失败。

这里有一个使用 **std::unique_ptr<>** 的示例：

```cpp
// foo.h
class Foo {
 public:
  // Factory method: creates and returns a Foo.
  // May return null on failure.
  static std::unique_ptr<Foo> Create();

  // Foo is not copyable.
  Foo(const Foo&) = delete;
  Foo& operator=(const Foo&) = delete;

 private:
  // Clients can't invoke the constructor directly.
  Foo();
};

// foo.c
std::unique_ptr<Foo> Foo::Create() {
  // Note that since Foo's constructor is private, we have to use new.
  return absl::WrapUnique(new Foo());
}
```

`Foo::Create()` 作为类方法，是可以承担 Init 方法的职责的。

如果对象有额外的 Init 方法，也可以通过如下形式：

```cpp
// foo.h
class Foo {
 public:
  static std::unique_ptr<Foo> Create();

  // Foo is not copyable.
  Foo(const Foo&) = delete;
  Foo& operator=(const Foo&) = delete;

 private:
  Foo();
  bool Init();
};

// foo.c
std::unique_ptr<Foo> Foo::Create() {
  auto p = absl::WrapUnique(new Foo());
  if (!p->Init()) {
    return nullptr;
  }

  return p;
}
```

这种方式的主要缺点是，只能返回在堆空间的对象，而不适用于在栈空间工作的对象。

## 附录、C++ 异常

Google 的 C++ 代码规范中，并不建议使用异常，可以参考 [Exceptions](https://google.github.io/styleguide/cppguide.html#Exceptions)。

Google 不使用异常，并非是从哲学或者道德层面来判断的，而仅仅是为了自身的方便。因为现有的 Google 代码都没有使用异常，如果引入异常机制，会导致现有代码存在问题，而迁移成本又太大。

> Our advice against using exceptions is not predicated on philosophical or moral grounds, but practical ones. Because we'd like to use our open-source projects at Google and it's difficult to do so if those projects use exceptions, we need to advise against exceptions in Google open-source projects as well. Things would probably be different if we had to do it all over again from scratch.

## 附录、海伦定律

海伦定律请参考 [Hyrum's Law](https://www.hyrumslaw.com/)。

> With a sufficient number of users of an API, it does not matter what you promise in the contract: all observable behaviors of your system will be depended on by somebody.

简单来说，当系统的用户足够多时，其任何可观察到的行为都会影响某些使用系统的用户。

因此我们需要小心暴露系统可观察的行为，降低和减小影响。
