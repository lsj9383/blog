# string_view

Quicklink: [Abseil：C++ Tips of the Week](../readme.md)

## string_view 是什么，为什么你需要使用它

当创建一个参数是常量字符串的函数时，有三种常见的选择：

```cpp
// C Convention
void TakesCharStar(const char* s);
void TakesCharStar(const char* s, size_t length);  // better, 译者注：原文没有该方式

// Old Standard C++ convention
void TakesString(const std::string& s);

// string_view C++ conventions
void TakesStringView(absl::string_view s);    // Abseil
void TakesStringView(std::string_view s);     // C++17
```

当调用者已经拥有字符串时，前两者的效果最好，但若发生以下转换：

- std::string 转换为 const char*
- const char* 转换为 std::string

若要实现这些转换，代码会怎么做呢？

对于 std::string 转换为 const char*，调用者需要使用 c_str() 函数，高效但是不便（我对这个不便的理解是可读性差，代码长）：

```cpp
void AlreadyHasString(const std::string& s) {
  TakesCharStar(s.c_str());
}
```

对于 const char* 转换为 std::string，调用者不用做任何事情，但是会创建一个临时的 std::string 变量，复制字符串内容，效率较低：

```cpp
void AlreadyHasCharStar(const char* s) {
  TakesString(s);  // 将会创建副本
}
```

## 该如何处理？

Google 的首选方式是使用 string_view，目前这已经成为了 C++17 的预置类型。

string_view 对象可以视作为已存在字符缓冲区的视图。具体而言，string_view 仅由指针和长度组成，同时 string_view 作为视图，是不能修改的（值对象）。

复制 string_view 是一个浅复制，即复制指针和长度，而不会有任何字符串数据被复制。

同时，string_view 具有两个隐式转换，即：

- 隐式转换 1：可以从 const char* 转换为 string_view（对 const char* 的 strlen() 会自动调用）。
- 隐式转换 2：可以从 const std::string& 转换为 string_view。

```cpp
void AlreadyHasString(const std::string& s) {
  TakesStringView(s);       // 没有显式转换；方便的！
}

void AlreadyHasCharStar(const char* s) {
  TakesStringView(s);       // 没有副本；高效的！
}
```

因为 string_view 并不拥有数据，因此 string_view 所指向的字符串必须拥有比 string_view 更长的生命周期。也因此，不能用 string_view 进行数据存储，我们在使用时需要有足够的证据来表明 string_view 使用期间的内存有效。

若后续需要对数据进行修改了，则需要调用 `std::string(my_string_vew)`，这会对字符串进行拷贝，生成一个独立的 std::string。

## 其他注意事项

- string_view 的复制足够轻量，因此在传递 string_view 时不需要用 `const&`，而是应该像 int 等类型一样传值。
- 将 string_view 通过 const 修饰，仅影响 string_view 本身是否被修改，其下的底层字符串，无论是否通过 const 修饰 string_view，都是不能被修改的。
- 对于函数参数，尽量不要用 const 修饰 string_view，除非你的团队要求你这样使用。
- string_view 不一定是 NULL 终止符的字符串，因此这样使用并不安全：

  ```cpp
  printf("%s\n", sv.data()); // DON’T DO THIS
  ```

  更好的方式是：

  ```cpp
  absl::PrintF("%s\n", sv);
  ```

- string_view 输出方式类似 string 或 const char*：

  ```cpp
  std::cout << "Took '" << s << "'";
  ```

- string_view has a constexpr constructor and a trivial destructor; keep this in mind when using in static and global variables or constants.