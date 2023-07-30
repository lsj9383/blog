#include <stdlib.h>
#include <unistd.h>
#include <gperftools/heap-checker.h>

#include <iostream>

void test() {
  char* ch = new char('A');
}

int main() {
    int* p1 = new int[1];
    int* p2 = new int[2];

  for (int i; i < 5; ++i) {
    std::cout << "start: " << i << "/5" << std::endl;
    test();
    sleep(1);

    if (HeapLeakChecker::NoGlobalLeaks()) {
      std::cout << "no leaks" << std::endl;
    } else {
      std::cout << "leaks" << std::endl;
    }
  }

  delete[] p1;

  return 0;
}