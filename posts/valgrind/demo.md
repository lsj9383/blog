# 示例代码

[TOC]

## 概述

为了构造测试场景的测试代码。

## 进程 Exec 的 massif

**结论：**

- exec 是不会输出堆报告的，因为整个进程空间都被替换掉了。
- 如果使用 `--trace-children=yes` 仍然会输出进程的堆报告。

```c
// exec-process-massif.c

#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

void g(void)
{
   malloc(4000);
}

void f(void)
{
   malloc(2000);
   g();
}

int main(void)
{
   int i;
   int* a[10];

   for (i = 0; i < 10; i++) {
      a[i] = malloc(1000);
   }

   f();

   g();

   for (i = 0; i < 10; i++) {
      free(a[i]);
   }

   char *args[] = {"ls", "-l", NULL};
   execvp("ls", args);
   printf("This line will not be executed\n");

   return 0;
}
```

执行如下命令：

```sh
# 编译
$ gcc -g exec-process-massif.c -o exec-process-massif

# 输出堆报告（没有）
$ valgrind --tool=massif --time-unit=B ./exec-process-massif

# 输出堆报告（有）
$ valgrind --tool=massif --time-unit=B --trace-children=yes ./exec-process-massif
```


## 多进程 Fork 的 massif

**结论：**

- valgrind massif 会自动跟踪 Fork 出的子进程的堆使用情况（因为是整个进程空间的拷贝）。
- 进程被 kill 掉也会输出堆报告，但是 **kill -9 不行**，无法输出 massif 报告。

```c
// multi-process-massif.c

#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

void g(void)
{
   malloc(4000);
}

void f(void)
{
   malloc(2000);
   g();
}

void parent_process() {}

void child_process() {
    for (int i = 0; i < 10; i++) {
      malloc(1000);
   }
}

int main(void)
{
   int i;
   int* a[10];

   for (i = 0; i < 10; i++) {
      a[i] = malloc(1000);
   }

   f();

   g();

   for (i = 0; i < 10; i++) {
      free(a[i]);
   }

   pid_t pid = fork();
   if (pid < 0) {
        printf("Fork failed.\n");
        return 1;
    } else if (pid == 0) {
        // 子进程代码
        printf("Child process: pid=%d\n", getpid());
        sleep(1);
        child_process();
        printf("Child process: Done\n");
    } else {
        // 父进程代码
        printf("Parent process: pid=%d\n", getpid());
        printf("Parent process: child pid=%d\n", pid);
        parent_process();
        printf("Parent process: Done\n");
    }

   return 0;
}
```

执行如下命令：

```sh
# 编译
$ gcc -g multi-process-massif.c -o multi-process-massif

# 输出堆报告
$ valgrind --tool=massif --time-unit=B ./multi-process-massif
```
