from satya import Model, Field, List
from typing import Optional

class Message(Model):
    role: str
    content: str
    refusal: Optional[str] = Field(required=False)

class TokenDetails(Model):
    cached_tokens: int
    audio_tokens: int

class CompletionTokenDetails(Model):
    reasoning_tokens: int
    audio_tokens: int
    accepted_prediction_tokens: int
    rejected_prediction_tokens: int

class Usage(Model):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_tokens_details: TokenDetails
    completion_tokens_details: CompletionTokenDetails

class Choice(Model):
    index: int
    message: Message
    logprobs: Optional[dict] = Field(required=False)
    finish_reason: str

class OpenAIResponse(Model):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Usage
    service_tier: str
    system_fingerprint: Optional[str] = Field(required=False)

class DeltaMessage(Model):
    role: Optional[str] = Field(required=False)
    content: Optional[str] = Field(required=False)
    refusal: Optional[str] = Field(required=False)

class StreamChoice(Model):
    index: int
    delta: DeltaMessage
    logprobs: Optional[dict] = Field(required=False)
    finish_reason: Optional[str] = Field(required=False)

class OpenAIStreamChunk(Model):
    id: str
    object: str
    created: int
    model: str
    service_tier: str
    system_fingerprint: Optional[str] = Field(required=False)
    choices: List[StreamChoice]