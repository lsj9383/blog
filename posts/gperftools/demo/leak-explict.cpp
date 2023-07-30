#include <stdlib.h>
#include <gperftools/heap-checker.h>

#include <iostream>

void test() {
  char* ch = new char('A');
}

int main() {
  const int array_count = 4;
  int* p = new int[array_count];

  HeapLeakChecker heap_checker("test_foo");
  test();
  if (!heap_checker.NoLeaks()) {
    std::cout << "heap memory leak" << std::endl;
  } else {
    std::cout << "no wrong" << std::endl;
  }

  return 0;
}
