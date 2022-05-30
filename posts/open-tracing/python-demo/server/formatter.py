import logging
from flask import Flask
from flask import request
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
 
app = Flask(__name__)
tracer = init_tracer('formatter')

@app.route("/format")
def format():
    print("========= Headers =========")
    for k, v in request.headers:
        print(k, ":", v)

    span_ctx = tracer.extract(opentracing.propagation.Format.HTTP_HEADERS, request.headers)
    span_tags = {opentracing.ext.tags.SPAN_KIND: opentracing.ext.tags.SPAN_KIND_RPC_SERVER}
    with tracer.start_span('format', child_of=span_ctx, tags=span_tags):
        hello_to = request.args.get('helloTo')
        return 'Hello, %s!' % hello_to
 
if __name__ == "__main__":
    app.run(port=8081)
