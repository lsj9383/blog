#include <stdlib.h>
#include <gperftools/heap-checker.h>

#include <iostream>

void test1() {
  char* ch = new char('A');
}

void test2() {
  char* ch = new char('B');
}

int main() {
  const int array_count = 4;
  int* p = new int[array_count];

  HeapLeakChecker heap_checker("test_foo");
  test1();

  {
    HeapLeakChecker::Disabler disabler;
    test2();
  }

  if (!heap_checker.NoLeaks()) {
    std::cout << "heap memory leak" << std::endl;
  } else {
    std::cout << "no wrong" << std::endl;
  }


  return 0;
}
