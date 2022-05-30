# Disappearing Act

Quicklink: [Abseil：C++ Tips of the Week](../readme.md)

## 选项一：在完整表达式结束之前完成使用临时对象

```cpp
// Safe (albeit a silly example):
size_t len1 = strlen((s1 + s2).c_str());
size_t len2 = strlen(absl::StrCat(s1, s2).c_str());
```

## 选项二：存储临时对象

## 选项三：存储临时对象的引用

## 选项四：设计你的函数并使他们不返回对象
