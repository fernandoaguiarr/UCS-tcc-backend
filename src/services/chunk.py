from typing import Union

import tiktoken
from openai.types import ChatModel


def count_tokens(text: str, model: Union[str, ChatModel]) -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def create_chunks(text: str, max_chunk_size: int, model: Union[str, ChatModel]):
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)

    chunks = [tokens[i:i + max_chunk_size] for i in range(0, len(tokens), max_chunk_size)]
    return [encoding.decode(chunk) for chunk in chunks]
