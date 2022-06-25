# Raw String Literals

Quicklink:

- [目录](../readme.md)
- [原文链接](https://abseil.io/tips/64)

由于转义的问题，你可能很难在 C++ 代码中理解正则表达式。将文本版的 JSON 或者 Protobuf 数据嵌入到单元测试中对引号和换行的处理也可能会让你感到恼火。

当你必须使用转义时，代码的可读性将会急剧下降：

> When you have to use significant escaping (or worse, multi-layer escaping), code clarity drops precipitously.

幸运的是 C++11 中可以消除这种转义需求：原始字符串 (raw string literals)。

## 原始字符串格式

原始字符串语法如下：

```cpp
R"tag(whatever you want to say)tag"
```

`tag` 是一个最多 16 个字符的序列（tag 可以为空，且这是常见的做法）。tag 可以包含任何字符，除括号、反斜杠和空格之外。

普通字符串方式：

```cpp
const char concert_17_raw[] =
    "id: 17\n"
    "artist: \"Beyonce\"\n"
    "date: \"Wed Oct 10 12:39:54 EDT 2012\"\n"
    "price_usd: 200\n";
```

使用原始字符串后：

```cpp
const char concert_17_raw[] = R"(
    id: 17
    artist: "Beyonce"
    date: "Wed Oct 10 12:39:54 EDT 2012"
    price_usd: 200)";
```

## 特别案例

```cpp
std::string my_string = R"foo(This contains quoted parens "()")foo";
```

## 结论

原始字符串不会成为你日常使用的工具，但有时善用原始字符串可以提升代码的可读性。

当你下次尝试弄清楚是需要 `\\` 或者是 `\\\\` 时，尝试使用原始字符串。即使正则表达式仍然难以理解，但一定比有转义时更简单，读者也会感谢你：

```cpp
R"regexp((?:"(?:\\"|[^"])*"|'(?:\\'|[^'])*'))regexp";
```

代替：

```cpp
"(?:\"(?:\\\\\"|[^\"])*\"|'(?:\\\\'|[^'])*')"
```
