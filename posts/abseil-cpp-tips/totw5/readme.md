# Disappearing Act

Quicklink: [Abseil：C++ Tips of the Week](../readme.md)

有些时候，为了正确使用 C++ 库，你需要同时理解库和语言。那么下面的代码有什么问题？

```cpp
// DON’T DO THIS
std::string s1, s2;
...
const char* p1 = (s1 + s2).c_str();             // Avoid!
const char* p2 = absl::StrCat(s1, s2).c_str();  // Avoid!
```

无论是 **s1 + s2** 和 **absl::StrCat(s1, s2)** 创建临时对象，并且 `c_str()` 返回一个指针指向一个临时变量的字符串内存，因此 p1 和 p2 指向的内存生命周期，将和临时变量生命周期一致。

那么这样的临时变量生命周期是多长呢？根据 C++17 标准，临时对象的销毁在在评估完整表达式的最后一步：

> Temporary objects are destroyed as the last step in evaluating the full-expression that (lexically) contains the point where they were created.

在上面的每个例子中，赋值运算符右侧的表达式一完成，临时值就被销毁，返回值从 c_str() 变成了一个悬空指针。

## 选项一：在完整表达式结束之前完成使用临时对象

```cpp
// Safe (albeit a silly example):
size_t len1 = strlen((s1 + s2).c_str());
size_t len2 = strlen(absl::StrCat(s1, s2).c_str());
```

## 选项二：存储临时对象

```cpp
// Safe (and more efficient than you might think):
std::string tmp_1 = s1 + s2;
std::string tmp_2 = absl::StrCat(s1, s2);
// tmp_1.c_str() and tmp_2.c_str() are safe.
```

## 选项三：存储临时对象的引用

## 选项四：设计你的函数并使他们不返回对象
