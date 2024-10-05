from typing import Union

from openai import OpenAI
from openai.types import ChatModel


class OpenAIClient:
    def __init__(self, model:Union[str, ChatModel]):
        self.openAI = OpenAI()
        self.model = model

    def send_to_openai(self, text: str, instruction: str, model: Union[str, ChatModel] = None) -> str:
        try:
            task = self.openAI.chat.completions.create(
                model=model if model else self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": text},
                ]
            )

            return task.choices[0].message.content
        except Exception as e:
            return "Error communicating with OpenAI: {}".format(str(e))
