from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class LLMRequest:
    task: str
    prompt: str
    temperature: float = 0.1
    max_tokens: int = 700


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str
    fallback_used: bool = False


class LLMProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        pass


class DeterministicLLMProvider(LLMProvider):
    provider_name = "deterministic"
    model_name = "rules-v1"

    def generate(self, request: LLMRequest) -> LLMResponse:
        selected_mitigation = "approval-gated rollback"
        if request.task == "postmortem" and "Selected mitigation:\n" in request.prompt:
            selected_mitigation = (
                request.prompt.split("Selected mitigation:\n", 1)[1].splitlines()[0].strip()
                or selected_mitigation
            )
        responses = {
            "root_cause": (
                "Metrics, logs, deployment timing, commit notes, and runbook guidance "
                "point to the v1.42.0 payment retry fanout change increasing overlapping "
                "checkout work and saturating the database connection pool. External "
                "provider degradation remains less likely because provider latency evidence "
                "is normal."
            ),
            "mitigation": (
                "Rollback is the safest first mitigation because it is reversible, aligns "
                "with the deployment window, and directly removes the retry fanout change "
                "correlated with DB pool saturation and checkout timeouts."
            ),
            "postmortem": (
                "Checkout latency and payment failures increased after the v1.42.0 "
                "checkout-api deployment. The strongest evidence points to retry fanout "
                "creating overlapping database work and saturating the connection pool. "
                f"The current human-selected response is {selected_mitigation}, with follow-up "
                "tests and alert correlation for retry pressure."
            ),
        }
        text = responses.get(
            request.task,
            "Deterministic fallback could not map this task to a specialized response.",
        )
        return LLMResponse(
            text=text,
            provider=self.provider_name,
            model=self.model_name,
            fallback_used=False,
        )


class OllamaLLMProvider(LLMProvider):
    provider_name = "ollama"

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model_name: str = "llama3.1",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def generate(self, request: LLMRequest) -> LLMResponse:
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": request.prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens,
                },
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return LLMResponse(
            text=str(payload.get("response", "")).strip(),
            provider=self.provider_name,
            model=self.model_name,
            fallback_used=False,
        )


class ResilientLLMProvider(LLMProvider):
    def __init__(self, primary: LLMProvider, fallback: LLMProvider) -> None:
        self.primary = primary
        self.fallback = fallback
        self.provider_name = primary.provider_name
        self.model_name = primary.model_name

    def generate(self, request: LLMRequest) -> LLMResponse:
        try:
            response = self.primary.generate(request)
            if response.text:
                return response
        except Exception:
            pass
        fallback_response = self.fallback.generate(request)
        return LLMResponse(
            text=fallback_response.text,
            provider=fallback_response.provider,
            model=fallback_response.model,
            fallback_used=True,
        )


def build_llm_provider() -> LLMProvider:
    provider = os.getenv("LLM_PROVIDER", "deterministic").lower()
    fallback = DeterministicLLMProvider()
    if provider == "ollama":
        return ResilientLLMProvider(
            primary=OllamaLLMProvider(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
                model_name=os.getenv("OLLAMA_MODEL", "llama3.1"),
                timeout_seconds=float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "20")),
            ),
            fallback=fallback,
        )
    return fallback
