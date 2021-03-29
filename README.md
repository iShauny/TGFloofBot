# TGFloofBot
Floofbot Telegram Bot

# Running

## Dependencies

Requires Python 3.9+ and Poetry:

```
python -m pip install poetry
```

To create a virtual environment and install dependencies:

```
python -m poetry install
```

To activate the virtual environment (`exit` to exit):

```
python -m poetry shell
```

## Configuration

Copy the sample configuration file `config.yaml.sample` to `config.yaml` and fill out the fields.

(A token can be obtained by messaging @BotFather on Telegram)

Include `debug: true` if you want to have extended debug log output.

## Starting the bot

First, make sure the environment has been activated:

```
python -m poetry shell
```

Then, run the script:

```
python entrypoint.py
```

# Development

## Example command

This can be placed in tgfloofbot/plugins/extra/commands.py

```python
class EchoCommandArgs(pydantic.BaseModel):
    text: str = pydantic.Field(..., description="Text to echo")


@loader.command(help="Repeats what the user says")
def echo(
    client: TGFloofbotClient,
    update: Update,
    context: CallbackContext,
    args: EchoCommandArgs,
) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id, text=args.text)
```

## Linting and formatting

First, make sure the lint dependencies are installed:

```
poetry install -E lint
```

Then, you can run the code formatter:

```
black tgfloofbot
```

And/or the type checker:

```
mypy tgfloofbot
```
