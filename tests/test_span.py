from time import sleep

from api_tracer.console import setup_console
from api_tracer.span import span


@span
def foo(hello="world", delay=1):
    print(hello)
    sleep(delay)

@span
def bar(spam="eggs", delay=1):
    print(spam)
    sleep(delay)

@span
def baz(apple="orange", delay=1):
    print(apple)
    sleep(delay)


if __name__ == "__main__":
    setup_console("test")
    foo(hello="foo", delay=1)
    bar(spam="bar", delay=2)
    baz(apple="baz", delay=3)
