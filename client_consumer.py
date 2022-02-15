from sys import argv
from requests import get

from opentelemetry import trace
from opentelemetry.propagate import extract
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from azure.servicebus import ServiceBusClient, ServiceBusMessage
#import requests
#from requests.api import head

trace.set_tracer_provider(
TracerProvider(
        resource=Resource.create({SERVICE_NAME: "my-helloworld-service"})
    )
)

jaeger_exporter = JaegerExporter(
    # configure agent
    agent_host_name='localhost',
    agent_port=6831,
    # optional: configure also collector
    # collector_endpoint='http://localhost:14268/api/traces?format=jaeger.thrift',
    # username=xxxx, # optional
    # password=xxxx, # optional
    # max_tag_value_length=None # optional
)

tracer = trace.get_tracer_provider().get_tracer(__name__)

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)


#Service_BUS
CONNECTION_STR = "Endpoint="
QUEUE_NAME = "event"

def send_single_message(sender, id):
    # create a Service Bus message
    message = ServiceBusMessage(
        "Single Message2",
        correlation_id = id
        )
    headers = {}
    # send the message to the queue
    sender.send_messages(message)
    print("Sent a single message")

assert len(argv) == 2

servicebus_client = ServiceBusClient.from_connection_string(conn_str=CONNECTION_STR, logging_enable=True)
with servicebus_client:
    receiver = servicebus_client.get_queue_receiver(queue_name=QUEUE_NAME, max_wait_time=5)
    for msg in receiver:
        print("Received: " + str(msg))
        TRACE={'traceparent': str(msg.correlation_id)}
        print
print(TRACE)

with tracer.start_as_current_span(
    "Consumer",
    context=extract(TRACE),
    kind=trace.SpanKind.SERVER
    #attributes="bus.name", "tracing.servicebus.windows.net"
):
    print("ok")
