import logging
from cltl.combot.infra.container import InfraContainer
from cltl.combot.infra.di_container import singleton
from cltl.simulated_user.api import SimulatedUser
from cltl.simulated_user.llama_cpp import SimulatedUserImpl
from cltl.simulated_user.service import SimulatedUserService

logger = logging.getLogger(__name__)

class SimulatedUserContainer(InfraContainer):
    @property
    @singleton
    def simulated_user(self) -> SimulatedUser:
        logger.info("Starting Simulated User through llama_cpp")
        return SimulatedUserImpl.from_config(self.config_manager)

    @property
    @singleton
    def simulated_user_service(self) -> SimulatedUserService:
        return SimulatedUserService.from_config(self.simulated_user, self.event_bus,
                                                        self.resource_manager, self.config_manager)

    def start(self):
        logger.info("Start Simulated User")
        super().start()
        self.simulated_user_service.start()

    def stop(self):
        try:
            logger.info("Stop Simulated User")
            self.simulated_user_service.stop()
        finally:
            super().stop()

