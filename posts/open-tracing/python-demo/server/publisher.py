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
tracer = init_tracer('publisher')

@app.route("/publish")
def publish():
    print("========= Headers =========")
    for k, v in request.headers:
        print(k, ":", v)

    span_ctx = tracer.extract(opentracing.propagation.Format.HTTP_HEADERS, request.headers)
    span_tags = {opentracing.ext.tags.SPAN_KIND: opentracing.ext.tags.SPAN_KIND_RPC_SERVER}
    with tracer.start_span('publish', child_of=span_ctx, tags=span_tags):
        hello_str = request.args.get('helloStr')
        print(hello_str)
        return 'published'

if __name__ == "__main__":
    app.run(port=8082)