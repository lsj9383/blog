# Enumerating with Class

Quicklink:

- [目录](../readme.md)
- [原文链接](https://abseil.io/tips/86)

## 无范围枚举

枚举的概念对于 C++ 程序员来说是非常熟悉的，但是在 C++11 前，枚举主要有两个缺点：

- 枚举和枚举类在相同的范围（命名空间）中。
- 可以隐式转换为整数类型值。

因此，在 C++98 中：

```cpp
enum CursorDirection { kLeft, kRight, kUp, kDown };
CursorDirection d = kLeft; // OK: enumerator in scope
int i = kRight;            // OK: enumerator converts to int
```

同时进行如下定义会错误：

```cpp
// error: redeclarations of kLeft and kRight
enum PoliticalOrientation { kLeft, kCenter, kRight };
```

C++11 修改了无范围枚举的行为：为枚举添加了命名空间，命名空间即枚举类。但为了保持兼容性，仍然将枚举导出到了枚举类的命名空间。

因此 C++11 代码可以写成：

```cpp
CursorDirection d = CursorDirection::kLeft;  // OK in C++11
int i = CursorDirection::kRight;             // OK: still converts to int
```

但是 **PoliticalOrientation** 还是会编译失败，因为枚举仍然会导出到枚举类的命名空间中。

## 作用域枚举

C++11 为了解决这两个问题，引入了新的概念：作用域枚举。

为了引入作用域枚举，这里添加了新的关键词：`enum class`，同时有以下特性：

- 枚举仅在枚举类的命名空间中。
- 不能隐式转为整数。

```cpp
enum class CursorDirection { kLeft, kRight, kUp, kDown };
CursorDirection d = kLeft;                    // error: kLeft not in this scope
CursorDirection d2 = CursorDirection::kLeft;  // OK
int i = CursorDirection::kRight;              // error: no conversion
```

同时，具有相同枚举的枚举类可以编译成功：

```cpp
// OK: kLeft and kRight are local to each scoped enum
enum class PoliticalOrientation { kLeft, kCenter, kRight };
```

## 底层枚举类型

C++11 还引入了为枚举指定底层类型的能力。

以前枚举的底层整数类型是通过检查枚举的大小来确定的，但现在我们可以明确了:

```cpp
// Use "int" as the underlying type for CursorDirection
enum class CursorDirection : int { kLeft, kRight, kUp, kDown };
```

因为这个枚举值很少，因此如果我们希望在存储 `CursorDirection` 避免浪费内存，我们可以指定 `char` 类型作为底层类型：

```cpp
// Use "char" as the underlying type for CursorDirection
enum class CursorDirection : char { kLeft, kRight, kUp, kDown };
```

如果枚举超过了底层类型的数据范围，编译器会报错。

## 结论

尽量在新代码中使用 `enum class`，这将有助于减少命名空间污染，并且能有助于避免隐式转换的错误：

```cpp
enum class Parting { kSoLong, kFarewell, kAufWiedersehen, kAdieu };
```
