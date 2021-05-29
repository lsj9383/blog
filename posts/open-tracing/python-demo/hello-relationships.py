# references: https://github.com/yurishkuro/opentracing-tutorial/tree/master/python/lesson01

import sys
import time
import logging
import opentracing
import jaeger_client


def init_tracer(service):
    logging.getLogger('').handlers = []
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    config = jaeger_client.Config(
        config={
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'logging': True,
        },
        service_name=service,
    )

    # this call also sets opentracing.tracer
    return config.initialize_tracer()


def say_hello(tracer, hello_to):
    with tracer.start_span('say-hello') as span:
        span.set_tag('hello-to', hello_to)
        hello_str = format_string(tracer, span, hello_to)
        print_hello(tracer, span, hello_str)


def format_string(tracer, root_span, hello_to):
    with tracer.start_span('format', child_of=root_span) as span:
        hello_str = 'Hello, %s!' % hello_to
        span.log_kv({'event': 'string-format', 'value': hello_str})
        return hello_str


def print_hello(tracer, root_span, hello_str):
    with tracer.start_span('println', child_of=root_span) as span:
        print(hello_str)
        span.log_kv({'event': 'println'})


def main():
    assert len(sys.argv) == 2
    hello_to = sys.argv[1]

    tracer = init_tracer('hello-world')
    say_hello(tracer, hello_to)

    # Jaeger Tracer is primarily designed for long-running server processes, 
    # so it has an internal buffer of spans that is flushed by a background thread. 
    # Since our program exits immediately, 
    # it may not have time to flush the spans to Jaeger backend.
    time.sleep(2)
    tracer.close()


if __name__ == '__main__':
    main()
