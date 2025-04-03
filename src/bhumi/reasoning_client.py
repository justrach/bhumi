"""
Enhanced client for working with reasoning-capable LLMs.

This module provides specialized tools for working with LLMs that support
chain-of-thought reasoning, allowing for better control over the reasoning
process and improved response handling. It also supports tool calls
within the reasoning process.
"""

from typing import List, Dict, Any, Union, Optional, Tuple, AsyncIterator
import re
import json
import asyncio
from dataclasses import dataclass, field
from enum import Enum

from .base_client import BaseLLMClient, LLMConfig, ReasoningResponse

class ReasoningFormat(Enum):
    """Supported formats for reasoning extraction"""
    TAGS = "tags"  # <think>...</think>
    JSON = "json"  # {"reasoning": "...", "response": "..."}
    MARKDOWN = "markdown"  # ```reasoning\n...\n```\n...
    AUTO = "auto"  # Try all formats

@dataclass
class ReasoningConfig:
    """Configuration for reasoning-specific parameters"""
    # Format to use for reasoning
    format: ReasoningFormat = ReasoningFormat.AUTO

    # Prompt template to encourage reasoning
    prompt_template: str = "Think step by step to solve this problem. First analyze the question carefully, then work through it methodically."

    # Whether to include reasoning in system prompt
    use_system_prompt: bool = True

    # Whether to extract reasoning even if not explicitly formatted
    extract_implicit: bool = True

    # Additional format-specific instructions
    format_instructions: Dict[ReasoningFormat, str] = field(default_factory=lambda: {
        ReasoningFormat.TAGS: "First, think through your reasoning step by step inside <think>...</think> tags. Then provide your final answer.",
        ReasoningFormat.JSON: "Respond with a JSON object that has two fields: 'reasoning' containing your step-by-step thought process, and 'response' containing your final answer.",
        ReasoningFormat.MARKDOWN: "First, provide your reasoning in a code block with the language 'reasoning'. Then provide your final answer.",
    })

    # Custom regex patterns for extracting reasoning
    custom_patterns: List[Tuple[str, str]] = field(default_factory=list)


class EnhancedReasoningResponse(ReasoningResponse):
    """Enhanced response class for reasoning models with additional capabilities"""

    def __init__(self, reasoning: str, output: str, raw: dict, format_used: ReasoningFormat = None, tool_calls: List[Dict[str, Any]] = None):
        super().__init__(_reasoning=reasoning, _output=output, _raw=raw)
        self.format_used = format_used
        self.tool_calls = tool_calls or []

    @property
    def reasoning(self) -> str:
        """Alias for think() for more intuitive API"""
        return self._reasoning

    @property
    def output(self) -> str:
        """Alias for __str__() for more intuitive API"""
        return self._output

    @property
    def has_tool_calls(self) -> bool:
        """Check if the response contains tool calls"""
        return len(self.tool_calls) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            "reasoning": self._reasoning,
            "output": self._output
        }

        if self.has_tool_calls:
            result["tool_calls"] = self.tool_calls

        return result

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())

    def to_markdown(self) -> str:
        """Format as markdown with reasoning in a code block"""
        markdown = f"```reasoning\n{self._reasoning}\n```\n\n"

        if self.has_tool_calls:
            markdown += "**Tool Calls:**\n\n"
            for i, tool_call in enumerate(self.tool_calls):
                function = tool_call.get("function", {})
                markdown += f"- Tool {i+1}: `{function.get('name', 'unknown')}` with args `{function.get('arguments', '{}')}` \n"
            markdown += "\n"

        markdown += self._output
        return markdown

    def to_html(self) -> str:
        """Format as HTML with reasoning in a details section"""
        reasoning_html = self._reasoning.replace("\n", "<br>")

        tool_calls_html = ""
        if self.has_tool_calls:
            tool_calls_html = "<div class=\"tool-calls\">\n"
            tool_calls_html += "<h4>Tool Calls:</h4>\n<ul>\n"
            for tool_call in self.tool_calls:
                function = tool_call.get("function", {})
                tool_calls_html += f"<li>{function.get('name', 'unknown')} with args {function.get('arguments', '{}')} </li>\n"
            tool_calls_html += "</ul>\n</div>\n"

        return f"""
        <details>
            <summary>Reasoning Process</summary>
            <div class="reasoning">{reasoning_html}</div>
        </details>
        {tool_calls_html}
        <div class="response">{self._output}</div>
        """


class ReasoningClient(BaseLLMClient):
    """
    Enhanced client for working with reasoning-capable LLMs.

    This client extends BaseLLMClient with specialized capabilities for
    handling models that can perform chain-of-thought reasoning.
    """

    def __init__(
        self,
        config: LLMConfig,
        reasoning_config: Optional[ReasoningConfig] = None,
        **kwargs
    ):
        """
        Initialize the reasoning client.

        Args:
            config: Base LLM configuration
            reasoning_config: Reasoning-specific configuration
            **kwargs: Additional arguments passed to BaseLLMClient
        """
        super().__init__(config, **kwargs)
        self.reasoning_config = reasoning_config or ReasoningConfig()

    async def completion_with_reasoning(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> Union[EnhancedReasoningResponse, AsyncIterator[str]]:
        """
        Get a completion with explicit reasoning.

        This method enhances the prompt to encourage the model to show its reasoning
        process, then extracts and structures that reasoning in the response.

        Args:
            messages: List of message dictionaries
            stream: Whether to stream the response
            **kwargs: Additional arguments passed to completion

        Returns:
            EnhancedReasoningResponse or AsyncIterator for streaming
        """
        # Don't modify the original messages
        messages = messages.copy()

        # Add reasoning instructions based on the configured format
        enhanced_messages = self._enhance_messages_for_reasoning(messages)

        # Get completion from the base client
        response = await super().completion(enhanced_messages, stream=stream, **kwargs)

        # For streaming, just return the stream
        if stream:
            return response

        # For non-streaming, extract and structure the reasoning
        return self._extract_reasoning(response)

    def _enhance_messages_for_reasoning(
        self,
        messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Enhance messages to encourage reasoning.

        Args:
            messages: Original message list

        Returns:
            Enhanced message list
        """
        enhanced_messages = messages.copy()
        format_type = self.reasoning_config.format

        # If using system prompt and there's a system message, enhance it
        if self.reasoning_config.use_system_prompt:
            if enhanced_messages and enhanced_messages[0].get("role") == "system":
                # Append to existing system message
                enhanced_messages[0]["content"] += f"\n\n{self.reasoning_config.prompt_template}"

                # Add format-specific instructions if not AUTO
                if format_type != ReasoningFormat.AUTO:
                    format_instructions = self.reasoning_config.format_instructions.get(format_type, "")
                    if format_instructions:
                        enhanced_messages[0]["content"] += f"\n\n{format_instructions}"
            else:
                # Create a new system message
                system_content = self.reasoning_config.prompt_template

                # Add format-specific instructions if not AUTO
                if format_type != ReasoningFormat.AUTO:
                    format_instructions = self.reasoning_config.format_instructions.get(format_type, "")
                    if format_instructions:
                        system_content += f"\n\n{format_instructions}"

                # Insert at the beginning
                enhanced_messages.insert(0, {
                    "role": "system",
                    "content": system_content
                })

        return enhanced_messages

    def _extract_reasoning(self, response: Any) -> EnhancedReasoningResponse:
        """
        Extract reasoning from the response.

        Args:
            response: Response from the base client

        Returns:
            EnhancedReasoningResponse with structured reasoning
        """
        # If it's already a ReasoningResponse, convert to EnhancedReasoningResponse
        if isinstance(response, ReasoningResponse):
            return EnhancedReasoningResponse(
                reasoning=response._reasoning,
                output=response._output,
                raw=response._raw
            )

        # Extract tool calls if present
        tool_calls = []
        if isinstance(response, dict):
            # Check for tool calls in the response
            if "tool_calls" in response:
                tool_calls = response["tool_calls"]
            elif "raw_response" in response and "choices" in response["raw_response"]:
                message = response["raw_response"]["choices"][0].get("message", {})
                if "tool_calls" in message:
                    tool_calls = message["tool_calls"]

        # Get the content from the response
        if isinstance(response, dict):
            if "text" in response:
                content = response["text"]
            elif "choices" in response.get("raw_response", {}):
                content = response["raw_response"]["choices"][0]["message"].get("content", "")
            else:
                content = ""
        else:
            content = str(response)

        # Extract reasoning based on format
        format_type = self.reasoning_config.format
        reasoning, output, format_used = "", content, None

        if format_type == ReasoningFormat.AUTO or format_type == ReasoningFormat.TAGS:
            # Try tags format
            think_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
            if think_match:
                reasoning = think_match.group(1).strip()
                output = content[content.find("</think>") + 8:].strip()
                format_used = ReasoningFormat.TAGS

        if (format_type == ReasoningFormat.AUTO or format_type == ReasoningFormat.JSON) and not reasoning:
            # Try JSON format
            try:
                data = json.loads(content)
                if "reasoning" in data and "response" in data:
                    reasoning = data["reasoning"]
                    output = data["response"]
                    format_used = ReasoningFormat.JSON
            except json.JSONDecodeError:
                pass

        if (format_type == ReasoningFormat.AUTO or format_type == ReasoningFormat.MARKDOWN) and not reasoning:
            # Try markdown format
            markdown_match = re.search(r'```reasoning\n(.*?)\n```', content, re.DOTALL)
            if markdown_match:
                reasoning = markdown_match.group(1).strip()
                output = content[content.find("```\n") + 4:].strip()
                format_used = ReasoningFormat.MARKDOWN

        # Try custom patterns
        if not reasoning and self.reasoning_config.custom_patterns:
            for pattern, output_pattern in self.reasoning_config.custom_patterns:
                reasoning_match = re.search(pattern, content, re.DOTALL)
                if reasoning_match:
                    reasoning = reasoning_match.group(1).strip()

                    # If output pattern is provided, use it to extract output
                    if output_pattern:
                        output_match = re.search(output_pattern, content, re.DOTALL)
                        if output_match:
                            output = output_match.group(1).strip()

                    break

        # Try to extract implicit reasoning if enabled
        if not reasoning and self.reasoning_config.extract_implicit:
            # Look for common reasoning patterns
            patterns = [
                r'(?:Let me think|Let\'s think|Thinking through this|Step by step|First,)(.*?)(?:Therefore|In conclusion|To summarize|So,|Finally,)',
                r'(?:Analysis|Reasoning|Thought process):(.*?)(?:Answer|Response|Conclusion):',
            ]

            for pattern in patterns:
                reasoning_match = re.search(pattern, content, re.DOTALL)
                if reasoning_match:
                    reasoning = reasoning_match.group(1).strip()
                    break

            # If we found implicit reasoning, try to extract the output
            if reasoning:
                output_patterns = [
                    r'(?:Therefore|In conclusion|To summarize|So,|Finally,)(.*?)$',
                    r'(?:Answer|Response|Conclusion):(.*?)$'
                ]

                for pattern in output_patterns:
                    output_match = re.search(pattern, content, re.DOTALL)
                    if output_match:
                        output = output_match.group(1).strip()
                        break

        # If we still don't have reasoning, use the whole content as output
        if not reasoning:
            reasoning = ""
            output = content

        # Create raw response dict
        if isinstance(response, dict) and "raw_response" in response:
            raw = response["raw_response"]
        else:
            raw = {"content": content}

        return EnhancedReasoningResponse(
            reasoning=reasoning,
            output=output,
            raw=raw,
            format_used=format_used,
            tool_calls=tool_calls
        )
