from sys import argv
from requests import get

from opentelemetry import trace
from opentelemetry.propagate import inject
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
CONNECTION_STR = "Endpoint=sb://"
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

with tracer.start_as_current_span("client"):
    with tracer.start_as_current_span("client-server"):
        headers = {}
        print(headers)
        inject(headers)
        print(headers)
        requested = get(
            "http://localhost:8082/server_request",
            params={"param": argv[1]},
            headers=headers,
        )
        assert requested.status_code == 200
        print(headers)
        print("sucess")
    with tracer.start_as_current_span('Service-BUS'):
        span = trace.get_current_span()
        headers = {}
        print(headers)
        inject(headers)
        print("BUS")
        print(headers)
        id = headers["traceparent"]
        print("oid " + id)
        span.set_attribute("bus.name", "tracing.servicebus.windows.net")
        span.add_event("event message",{"event_attributes": 1, "TESTE":2})
        servicebus_client = ServiceBusClient.from_connection_string(conn_str=CONNECTION_STR, logging_enable=True)
        with servicebus_client:
            sender = servicebus_client.get_queue_sender(queue_name=QUEUE_NAME)
            with sender:
                send_single_message(sender,id)
