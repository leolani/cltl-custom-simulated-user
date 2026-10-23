import logging
from cltl.combot.event.emissor import TextSignalEvent
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.time_util import timestamp_now
from cltl.combot.infra.topic_worker import TopicWorker
from cltl.combot.infra.event.util import extract_scenario_id
from emissor.representation.scenario import TextSignal
from cltl.simulated_user.api import SimulatedUser

logger = logging.getLogger(__name__)


class SimulatedUserService:
    """
    Service used to integrate the component into applications.
    """
    @classmethod
    def from_config(cls, simulated_user: SimulatedUser, event_bus: EventBus, resource_manager: ResourceManager,
                    config_manager: ConfigurationManager):
        config = config_manager.get_config("cltl.simulated_user")
        return cls(config.get("topic_in"), config.get("topic_out"), simulated_user,
                   event_bus, resource_manager)

    def __init__(self, input_topic: str, output_topic: str, simulated_user: SimulatedUser,
                 event_bus: EventBus, resource_manager: ResourceManager):
        self._simulated_user = simulated_user
        self._event_bus = event_bus
        self._resource_manager = resource_manager
        self._input_topic = input_topic
        self._output_topic = output_topic
        self._topic_worker = None

    def start(self, timeout=30):
        self._topic_worker = TopicWorker([self._input_topic], self._event_bus, provides=[self._output_topic],
                                         resource_manager=self._resource_manager, processor=self._process,  buffer_size=64,
                                         name=self.__class__.__name__)
        self._topic_worker.start().wait()

    def stop(self):
        if not self._topic_worker:
            return

        self._topic_worker.stop()
        self._topic_worker.await_stop()
        self._topic_worker = None

    def _process(self, event: Event[TextSignalEvent]):
        response = self._simulated_user.respond(event.payload.signal.text)
        if not response:
            return

        scenario_id = extract_scenario_id(event)
        signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, response)
        self._event_bus.publish(self._output_topic,
                                Event.for_scenario_payload(scenario_id, TextSignalEvent.for_speaker(signal),
                                                           source=event))
