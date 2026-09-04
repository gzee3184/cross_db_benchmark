"""Machine-agnostic unified Large Language Model client.

Connects to any OpenAI-compatible server (vLLM, SGLang, NIM, or OpenAI).
"""

import os
from typing import Any, Dict, List, Optional
from openai import OpenAI


class LLMClient:
    """Unified client for inference across open-weight and proprietary models."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ):
        """Initialize the client.

        Args:
            base_url: Server URL. Defaults to LM_BASE_URL or http://localhost:30000/v1.
            api_key: Authorization key. Defaults to LM_API_KEY or 'EMPTY'.
            model: Model identifier. Defaults to LM_MODEL or 'default'.
            timeout: Network request timeout in seconds.
        """
        self.base_url = base_url or os.environ.get(
            "LM_BASE_URL", "http://localhost:30000/v1"
        )
        self.api_key = api_key or os.environ.get("LM_API_KEY", "EMPTY")
        self.model = model or os.environ.get("LM_MODEL", "default")
        self.timeout = timeout

        self._client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> str:
        """Generate text from a prompt.

        Args:
            prompt: User message text.
            system_prompt: Optional system instructions.
            temperature: Sampling temperature.
            max_tokens: Maximum completion tokens.

        Returns:
            The model completion string.
        """
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        return content.strip()

    def generate_tool_call(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Optional[Dict[str, Any]]:
        """Request structured tool calls from the model.

        Args:
            prompt: User message text.
            tools: List of tool definitions conforming to OpenAI format.
            system_prompt: Optional system instructions.
            temperature: Sampling temperature.

        Returns:
            The parsed tool call arguments dictionary, or None if no call made.
        """
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=temperature,
        )
        message = response.choices[0].message
        if message.tool_calls:
            call = message.tool_calls[0]
            import json
            try:
                return json.loads(call.function.arguments)
            except Exception:
                return None
        return None
