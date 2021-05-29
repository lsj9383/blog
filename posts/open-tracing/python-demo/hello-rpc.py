# references: https://github.com/yurishkuro/opentracing-tutorial/tree/master/python/lesson01

import sys
import time
import logging
import requests
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
        span.set_baggage_item('greeting', "test")
        span.set_tag('hello-to', hello_to)
        hello_str = format_string(tracer, span, hello_to)
        print_hello(tracer, span, hello_str)


def format_string(tracer, root_span, hello_to):
    with tracer.start_span('format', child_of=root_span) as span:
        hello_str = http_get(tracer, span, 8081, 'format', 'helloTo', hello_to)
        span.log_kv({'event': 'string-format', 'value': hello_str})
        return hello_str


def print_hello(tracer, root_span, hello_str):
    with tracer.start_span('println', child_of=root_span) as span:
        http_get(tracer, span, 8082, 'publish', 'helloStr', hello_str)
        span.log_kv({'event': 'println'})


def http_get(tracer, span, port, path, param, value):
    url = 'http://localhost:%s/%s' % (port, path)

    span.set_tag(opentracing.ext.tags.HTTP_METHOD, 'GET')
    span.set_tag(opentracing.ext.tags.HTTP_URL, url)
    span.set_tag(opentracing.ext.tags.SPAN_KIND, opentracing.ext.tags.SPAN_KIND_RPC_CLIENT)
    headers = {}
    tracer.inject(span, opentracing.propagation.Format.HTTP_HEADERS, headers)

    r = requests.get(url, params={param: value}, headers=headers)
    assert r.status_code == 200
    return r.text


def main():
    assert len(sys.argv) == 2
    hello_to = sys.argv[1]

    tracer = init_tracer('hello-world')

    try:
        say_hello(tracer, hello_to)
    except:
        pass

    # Jaeger Tracer is primarily designed for long-running server processes, 
    # so it has an internal buffer of spans that is flushed by a background thread. 
    # Since our program exits immediately, 
    # it may not have time to flush the spans to Jaeger backend.
    time.sleep(2)
    tracer.close()


if __name__ == '__main__':
    main()
