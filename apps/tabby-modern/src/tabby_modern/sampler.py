"""
tabby-modern sampler — ExllamaV3SamplerBuilder.
Extracted from tabbyAPI backends/exllamav3/sampler.py (ore: retained).
Refined: no tabbyAPI request type coupling — accepts a duck-type params object.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from exllamav3.generator.sampler import CustomSampler


@dataclass
class SamplerBuilder:
    """
    Constructs an exllamav3 CustomSampler from request parameters.
    Pass params with: temperature, top_k, top_p, min_p,
    repetition_penalty, frequency_penalty, presence_penalty.
    """

    _stack: list[Any] = field(default_factory=list)

    def penalties(
        self, rep_p: float, freq_p: float, pres_p: float,
        penalty_range: int = 0, rep_decay: int = 0
    ) -> "SamplerBuilder":
        from exllamav3.generator.sampler import SS_RepP, SS_PresFreqP
        self._stack += [
            SS_RepP(rep_p, penalty_range, rep_decay),
            SS_PresFreqP(pres_p, freq_p, penalty_range, rep_decay),
        ]
        return self

    def temperature(self, temp: float) -> "SamplerBuilder":
        from exllamav3.generator.sampler import SS_Temperature
        self._stack.append(SS_Temperature(temp))
        return self

    def top_k(self, top_k: int) -> "SamplerBuilder":
        if top_k > 0:
            from exllamav3.generator.sampler import SS_TopK
            self._stack.append(SS_TopK(top_k))
        return self

    def top_p(self, top_p: float) -> "SamplerBuilder":
        if top_p < 1.0:
            from exllamav3.generator.sampler import SS_TopP
            self._stack.append(SS_TopP(top_p))
        return self

    def min_p(self, min_p: float) -> "SamplerBuilder":
        if min_p > 0.0:
            from exllamav3.generator.sampler import SS_MinP
            self._stack.append(SS_MinP(min_p))
        return self

    def build(self, greedy: bool = False) -> "CustomSampler":
        from exllamav3.generator.sampler import CustomSampler, SS_Argmax, SS_Sample
        if greedy or not self._stack:
            return CustomSampler([SS_Argmax()])
        self._stack.append(SS_Sample())
        return CustomSampler(self._stack)


def build_sampler_from_request(params: Any) -> "CustomSampler":
    """
    Build a CustomSampler from a request params object.
    Duck-typed: works with CompletionRequest, ChatCompletionRequest, or any
    object with temperature / top_k / top_p / min_p / repetition_penalty attrs.
    """
    temp = getattr(params, "temperature", 1.0)
    greedy = temp == 0.0

    builder = SamplerBuilder()

    rep_p = getattr(params, "repetition_penalty", 1.0)
    freq_p = getattr(params, "frequency_penalty", 0.0)
    pres_p = getattr(params, "presence_penalty", 0.0)
    if rep_p != 1.0 or freq_p != 0.0 or pres_p != 0.0:
        builder.penalties(rep_p, freq_p, pres_p)

    if not greedy:
        builder.temperature(temp)
        builder.top_k(getattr(params, "top_k", 0))
        builder.top_p(getattr(params, "top_p", 1.0))
        builder.min_p(getattr(params, "min_p", 0.0))

    return builder.build(greedy=greedy)
