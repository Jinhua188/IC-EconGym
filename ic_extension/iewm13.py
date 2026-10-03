"""IEWM-style runtime and observable policy adapters for the 13-sector model.

This adapts the executable interface in the supplied IEWM document. It uses
ICEnvironment as the sole settlement engine; the enterprise BOM and synthetic
candidate edges are deliberately not substituted for the 2020 IO accounts.
"""
from __future__ import annotations

from copy import deepcopy

import numpy as np

from .model import (GovernmentAction, ICEnvironment, RuleGovernmentPolicy,
                    RuleSectorPolicy, SectorAction)


class SectorPolicy:
    """All alternatives receive the same sector observation and action type."""

    def __init__(self, cfg: dict, name: str = "rule"):
        if name not in {"rule", "demand_tracking", "buffered_smoothing"}:
            raise ValueError(f"Unknown sector policy: {name}")
        self.name = name
        self.rule = RuleSectorPolicy(cfg)

    def begin_period(self):
        self.rule.begin_period()

    def act(self, observation: dict) -> SectorAction:
        action = self.rule.act(observation)
        if self.name == "demand_tracking":
            base = observation["base_output"]
            demand = observation["observed_demand"]
            action.production_plan = float(np.clip(demand, 0.3 * base, 2.0 * base))
        if self.name == "buffered_smoothing":
            base = observation["base_output"]
            demand_ratio = observation["observed_demand"] / max(base, 1e-12)
            action.production_plan = float(base * np.clip(0.5 + 0.5 * demand_ratio, 0.3, 2.0))
            action.inventory_target = 0.25
        return action


class GovernmentPolicy:
    """Targeting rules share channels, total budget and start period."""

    def __init__(self, cfg: dict, name: str = "configured"):
        if name not in {"configured", "uniform", "linkage", "stress", "none"}:
            raise ValueError(f"Unknown government policy: {name}")
        self.name = name
        local = deepcopy(cfg)
        local["policy"] = deepcopy(cfg.get("policy", {}))
        if name == "none":
            local["policy"]["enabled"] = False
        elif name != "configured":
            local["policy"].pop("sector_weights", None)
            local["policy"]["targeting_rule"] = {
                "uniform": "uniform",
                "linkage": "backward_linkage",
                "stress": "linkage_stress_proxy",
            }[name]
        self.rule = RuleGovernmentPolicy(local)

    def act(self, observation: dict) -> GovernmentAction:
        return self.rule.act(observation)


class World13:
    """Minimal typed reset/run_agents/step/evaluate interface.

    The environment keeps its existing IO accounting and transition logic.
    This runtime does not implement learning, endogenous rule evolution, or
    online empirical alignment.
    """

    def __init__(self, cfg: dict, sector_policy: str = "rule",
                 government_policy: str = "configured"):
        self.cfg = deepcopy(cfg)
        self.sector_policy_name = sector_policy
        self.government_policy_name = government_policy
        self.reset()

    def reset(self, seed: int | None = None) -> dict:
        if seed is not None:
            self.cfg["seed"] = int(seed)
        self.environment = ICEnvironment(self.cfg)
        self.sectors = SectorPolicy(self.cfg, self.sector_policy_name)
        self.government = GovernmentPolicy(self.cfg, self.government_policy_name)
        self.trajectory: list[dict] = []
        return self.environment.observations()

    def run_agents(self, observation: dict | None = None) -> dict:
        observation = observation or self.environment.observations()
        self.sectors.begin_period()
        return {
            "sectors": [self.sectors.act(o) for o in observation["sectors"]],
            "government": self.government.act(observation["government"]),
        }

    def step(self, actions: dict) -> tuple[dict, dict, bool, dict]:
        next_observation, rewards, done, record = self.environment.step(
            actions["sectors"], actions["government"])
        self.trajectory.append(record)
        return next_observation, rewards, done, record

    def evaluate(self) -> dict:
        if not self.trajectory:
            raise ValueError("Run at least one step before evaluation")
        rows = self.trajectory
        return {
            "periods": len(rows),
            "cumulative_value_added": sum(r["value_added"] for r in rows),
            "cumulative_shortage": sum(r["shortage"] for r in rows),
            "cumulative_final_demand": sum(r["final_demand"] for r in rows),
            "cumulative_final_delivered": sum(r["final_delivered"] for r in rows),
            "cumulative_final_shortage": sum(r["final_shortage"] for r in rows),
            "final_fill_rate": sum(r["final_delivered"] for r in rows) / max(sum(r["final_demand"] for r in rows), 1e-12),
            "cumulative_welfare": sum(r["welfare"] for r in rows),
            "mean_service_rate": float(np.mean([r["service_rate"] for r in rows])),
            "terminal_output": rows[-1]["output"],
            "terminal_backlog": rows[-1]["backlog"],
            "fiscal_spend": rows[-1]["fiscal_cost_cumulative"],
            "private_spend": sum(r["private_investment"] + r["private_rd"] + r["private_ai"] for r in rows),
            "terminal_ai_effective_mean": rows[-1]["ai_effective_mean"],
            "terminal_technology_mean": rows[-1]["technology_mean"],
            "terminal_edge_health_mean": rows[-1]["edge_health_mean"],
        }


def make(cfg: dict, *, sector_policy: str = "rule",
         government_policy: str = "configured") -> World13:
    return World13(cfg, sector_policy=sector_policy,
                   government_policy=government_policy)
