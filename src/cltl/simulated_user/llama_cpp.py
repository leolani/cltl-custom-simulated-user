"""A simulated user that interacts with an agent,
such as the DayInterviewer, with the knowledge of an
example day.
"""
from openai import OpenAI
from cltl.simulated_user.api import SimulatedUser

_DEFAULT_HOST = "http://localhost:8080"
_DEFAULT_MODEL ="Qwen/Qwen2.5-7B-Instruct-GGUF:Q4_K_M"
_DEFAULT_NAME = "Stranger"
_DEFAULT_TEMPERATURE = 0.3
NR_OF_HISTORY_TURNS = 12

class SimulatedUserImpl(SimulatedUser):
    @classmethod
    def from_config(cls, config_manager):
        config = config_manager.get_config("cltl.simulated_user")

        return cls(model=config.get("model") if "model" in config else _DEFAULT_MODEL,
                   host=config.get("host") if "host" in config else _DEFAULT_HOST,
                   temperature=config.get_float("temperature") if "temperature" in config else _DEFAULT_TEMPERATURE,
                   api_key=config.get("api_key") if "api_key" in config else None,
                   name=config.get("human") if "human" in config else _DEFAULT_NAME,
                   instruct=config.get("instruction") if "instruction" in config else None
                   )

    def __init__(self, model: str = _DEFAULT_MODEL,
                 host: str = _DEFAULT_HOST,
                 temperature : float = _DEFAULT_TEMPERATURE,
                 api_key: str = None,
                 name:str = _DEFAULT_NAME,
                 instruct: str = None):
        """
        Parameters
        ----------
        model : str
            Name of the model. llama-server serves a single model and ignores this,
            it is used to label the detections.
        host : str
            Address of the llama-server, e.g. "http://localhost:9009".
        api_key : str
            API key, only needed if llama-server was started with --api-key.
        name: str
            Name of the simulated user
        """
        self._client = OpenAI(base_url=f"{host.rstrip('/')}/v1", api_key=api_key or "no-key")
        self._model = model
        self.name = name
        self._temperature = temperature
        self._instruct_basics = f"""
            You are {self.name}. You are a human and you have a conversation with a conversational agent. 
            You are a human user, not an assistant: keep your answers short.
            You can also ask questions to the agent.
            """
        self.instruction = instruct
        self.history = []

    def respond(self, agent_utterance):
        """The answer of the LLM to an utterance of the agent, with the knowledge of the day."""
        instructions = [self._instruct_basics]
        if self.instruction:
            instructions.append(self.instruction)
        messages = ([{"role": "user", "content": "\n".join(instructions)}]
                    + self.history[-NR_OF_HISTORY_TURNS:] + [{"role": "user", "content": agent_utterance}])
        response = self._client.chat.completions.create(model=self._model, messages=messages, temperature=self._temperature,
                                                       max_tokens=150)
        answer = response.choices[0].message.content.strip()
        self.history += [{"role": "assistant", "content": agent_utterance}, {"role": "user", "content": answer}]
        return answer



