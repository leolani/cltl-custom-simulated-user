# cltl-custom-simulated-user

A Leolani component that lets an LLM play the human side of a conversation.
It replaces the audio and chat UI input: every utterance of the agent is
answered by a language model that pretends to be a person, and that answer is
fed back to the agent as if a user had typed it.

This makes it possible to run long conversations with an agent (for example
the DayInterviewer) without anybody at the keyboard, to test it or to collect
interaction data.

- **`cltl.simulated_user`** listens for agent utterances on the event bus,
  asks an LLM (served by `llama-server` through its OpenAI-compatible API) for
  a short first-person reply in the role of a named human, and publishes that
  reply as a user utterance.

It attaches to a running Leolani deployment through the message bus, as one
tenant. Nothing in the platform needs to know it exists.

## How it fits together

```
        ┌──────────────────────────┐
        │  agent (e.g. eliza,      │
        │  DayInterviewer, ...)    │
        └───────┬──────────▲───────┘
                │          │
 cltl.topic.text_out    cltl.topic.text_in
  (agent utterance)     (user utterance)
                │          │
                ▼          │
 ┌─────────────────────────┴─────────┐        ┌──────────────┐
 │ SimulatedUserService              │        │ llama-server │
 │   SimulatedUserImpl.respond(text) │ ─────► │ /v1/chat/... │
 └───────────────────────────────────┘        └──────────────┘
```

`SimulatedUserImpl` keeps the last 12 turns of the conversation as context
and answers in at most 150 tokens. The reply is published as a
`TextSignalEvent` for the speaker, with `source=event`, so tenant and scenario
ids carry over from the agent's utterance.

The simulated user only answers; it never starts the conversation. The first
utterance has to come from the agent, e.g. its greeting when the deployment's
`cltl-context` opens a scenario.

All topic names are configurable, see [Configuration](#configuration).

## Configuration

`config/default.config` holds the standalone defaults; `config/custom.config`
overrides them for a real deployment. The relevant sections:

```ini
[cltl.event]
implementation: kombu             # internal = in-process bus, for local testing

[cltl.event.kombu]
server: $CLTL_AMQP_URL            # broker of the deployment
exchange: cltl.combot
compression: bzip2
tenant: $CLTL_TENANT              # empty = listen to all tenants

[cltl.simulated_user]
model: Qwen/Qwen2.5-7B-Instruct-GGUF:Q4_K_M  # only a label, llama-server serves one model
host: http://localhost:8080       # address of llama-server
temperature: 0.3
# api_key: ...                    # only if llama-server runs with --api-key
topic_in: cltl.topic.text_out     # what the agent says
topic_out: cltl.topic.text_in     # where the simulated user's answers go
human: Jan                        # name of the simulated user (default: Stranger)
# instruction: ...                # who the simulated user is, added to the system prompt
```

`$VAR` values are expanded when read. An unset variable is passed on as the
literal string (with only a warning), so a missing `CLTL_TENANT` makes the
component bind a queue for a tenant literally named `$CLTL_TENANT`.

## Running

Requires Python ≥ 3.11.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start an LLM backend on the `host` from the configuration, e.g.:

```bash
llama-server -hf Qwen/Qwen2.5-7B-Instruct-GGUF:Q4_K_M --port 8080
```

### As a tenant in a Leolani deployment

Make sure the deployment's broker is running and reachable (e.g. the
`servers/broker` and `servers/eliza` stacks of a cltl-apps checkout), and that
the agent for the tenant is up. Then, with the virtual environment active:

```bash
CLTL_AMQP_URL=amqp://eliza:eliza123@127.0.0.1:5672/ CLTL_TENANT=tenant-a \
    python src/main.py
```

- `CLTL_AMQP_URL` is the broker of the deployment, as seen from outside its
  Docker network.
- `CLTL_TENANT` is the tenant the simulated user talks for. It then only
  receives the agent utterances of `tenant-a` and its answers only reach that
  tenant's agent. Left empty, it would answer every tenant on the exchange.

Both are read from `config/custom.config`, which sets
`[cltl.event] implementation: kombu`. `main.py` serves a `/health` endpoint on
port 8010. Opening and closing scenarios is not its job; that is done by the
deployment's own `cltl-context`.

Do not chat with the same tenant from the chat UI at the same time: the agent
would get two users, and the simulated user would also answer the replies
meant for you.

### Standalone

Without `config/custom.config`, `config/default.config` uses the in-process
event bus (`[cltl.event] implementation: internal`). The component then starts
but has nobody to talk to; this is only useful to check that it starts.
