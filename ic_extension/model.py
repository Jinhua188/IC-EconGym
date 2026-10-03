"""A reproducible 13-sector, one-government economic experiment environment.

All monetary flows are fixed-2020-price values in RMB 10,000 per quarter.
The 13 sectors are endogenous representative agents. The other 42 domestic
sectors, imports, and final users remain explicit boundary flows.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import math
import numpy as np
import yaml

DATA = Path(__file__).resolve().parent / "data"
N = 13


def clip(x, lo=0.0, hi=1.0):
    return np.clip(x, lo, hi)


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30.0, 30.0)))


@dataclass
class SectorAction:
    production_plan: float
    inventory_target: float = 0.0
    price_change: float = 0.0
    capex_share: float = 0.0
    rd_share: float = 0.0
    ai_share: float = 0.0
    coordination: float = 0.0
    diversification: float = 0.0


@dataclass
class GovernmentAction:
    ai: np.ndarray
    capacity: np.ndarray
    rd: np.ndarray
    qualification: np.ndarray
    inventory: np.ndarray
    edge_repair: np.ndarray

    @classmethod
    def zeros(cls):
        return cls(*(np.zeros(N, dtype=float) for _ in range(6)))


class SectorAgent:
    """Role interface. A policy only chooses actions from the agent observation."""

    def __init__(self, index: int, label: str, kind: str, allowed_actions: list[str]):
        self.index, self.label, self.kind = index, label, kind
        self.allowed_actions = allowed_actions

    def observation(self, env: "ICEnvironment") -> dict:
        j = self.index
        upstream = np.flatnonzero(env.a_total[:N, j] > 1e-12).tolist()
        downstream = np.flatnonzero(env.a_total[j, :N] > 1e-12).tolist()
        return {
            "sector_id": j + 1, "sector_type": self.kind,
            "allowed_actions": self.allowed_actions,
            "output": float(env.output[j]), "base_output": float(env.q0[j]),
            "capacity": float(env.capacity[j]), "inventory": float(env.finished[j]),
            "backlog": float(env.backlog[j]), "price": float(env.price[j]),
            "ai": float(env.ai[j]), "ai_effective": float(env.ai_effective[j]),
            "technology": float(env.tech[j]), "absorption": float(env.absorb[j]),
            "upstream_ids": [k + 1 for k in upstream],
            "upstream_prices": env.price[upstream].tolist(),
            "upstream_health": env.health[upstream, j].tolist(),
            "downstream_ids": [k + 1 for k in downstream],
            "observed_demand": float(env.last_demand[j]),
            "government_budget_remaining": float(env.budget_remaining),
        }


class GovernmentAgent:
    def observation(self, env: "ICEnvironment") -> dict:
        return {
            "period": env.t,
            "output": env.output.tolist(), "value_added": env.value_added.tolist(),
            "base_output": env.q0.tolist(), "backward_linkage": env.backward_linkage.tolist(),
            "price": env.price.tolist(), "shortage": env.shortage.tolist(),
            "backlog": env.backlog.tolist(), "technology": env.tech.tolist(),
            "ai_effective": env.ai_effective.tolist(),
            "edge_health": env.health.tolist(),
            "fiscal_cost": float(env.fiscal_cost),
            "budget_remaining": float(env.budget_remaining),
        }


class RuleSectorPolicy:
    """A bounded baseline policy; rates are scenario assumptions, not estimates."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.rng = np.random.default_rng(int(cfg.get("seed", 20261001)) + 71)
        self.period = 0
        self.common_error = 0.0

    def begin_period(self):
        self.common_error = float(self.rng.normal())
        self.period += 1

    def act(self, obs: dict) -> SectorAction:
        base = obs["base_output"]
        demand_ratio = obs["observed_demand"] / max(base, 1e-12)
        modules = set(self.cfg.get("modules", []))
        if "forecast" in modules:
            common = float(self.cfg.get("common_forecast_share", 0.0))
            gain = 1.0 - float(self.cfg.get("ai_forecast_gain", 0.0)) * min(obs["ai_effective"], 1.0)
            error = float(self.cfg.get("forecast_error_sd", 0.0)) * gain * (
                common * self.common_error + math.sqrt(max(0.0, 1.0 - common ** 2)) * self.rng.normal())
            demand_ratio *= max(0.0, 1.0 + error)
        plan = base * clip(0.7 + 0.3 * demand_ratio, 0.3, 1.8)
        action = SectorAction(production_plan=float(plan))
        if "investment" in modules:
            action.capex_share = float(clip(0.02 * max(demand_ratio - 1.0, 0), 0, 0.05))
        if "innovation" in modules:
            action.rd_share = float(self.cfg.get("rd_rate", 0.005))
        if "ai" in modules:
            action.ai_share = float(self.cfg.get("ai_rate", 0.002))
        if "coordination" in modules:
            action.coordination = float(self.cfg.get("coordination_effort", 0.1))
        if "diversification" in modules:
            action.diversification = float(self.cfg.get("diversification_effort", 0.1))
        for name in ("price_change", "capex_share", "rd_share", "ai_share", "coordination", "diversification"):
            if name not in obs["allowed_actions"]:
                setattr(action, name, 0.0)
        return action


class RuleGovernmentPolicy:
    def __init__(self, cfg: dict):
        self.cfg = cfg

    def act(self, obs: dict) -> GovernmentAction:
        out = GovernmentAction.zeros()
        policy = self.cfg.get("policy", {})
        if not policy.get("enabled", False):
            return out
        if int(obs["period"]) < int(policy.get("start_period", 0)):
            return out
        budget = obs["budget_remaining"]
        if budget <= 0:
            return out
        channels = policy.get("channels", {"capacity": 1.0})
        if policy.get("adaptive", False):
            shortage_rate = np.mean(np.asarray(obs["shortage"]) / np.maximum(obs["base_output"], 1.0))
            health_gap = max(0.0, 1.0 - float(np.mean(obs["edge_health"])))
            ai_gap = max(0.0, 1.0 - float(np.mean(obs["ai_effective"])))
            channels = {"ai": 0.1 + ai_gap, "capacity": 0.1 + shortage_rate,
                        "rd": 0.1 + max(0.0, 1.0 - float(np.mean(obs["technology"]))),
                        "qualification": 0.1 + health_gap,
                        "inventory": 0.1 + shortage_rate,
                        "edge_repair": 0.1 + health_gap}
        explicit = policy.get("sector_weights")
        if explicit is not None:
            weights = np.asarray(explicit, dtype=float)
        else:
            rule = policy.get("targeting_rule", "uniform")
            if rule == "uniform":
                weights = np.ones(N)
            elif rule == "output_scale":
                weights = np.asarray(obs["base_output"], dtype=float)
            elif rule == "ai_gap":
                weights = np.maximum(1.0 - np.asarray(obs["ai_effective"]), 0.01)
            elif rule == "backward_linkage":
                weights = np.asarray(obs["backward_linkage"], dtype=float)
            elif rule == "linkage_stress_proxy":
                weights = np.asarray(obs["backward_linkage"], dtype=float) * (
                    0.1 + np.asarray(obs["shortage"]) / np.maximum(obs["base_output"], 1.0))
            else:
                raise ValueError(f"Unknown policy.targeting_rule: {rule}")
        if len(weights) != N or np.any(weights < 0) or weights.sum() <= 0:
            raise ValueError("policy.sector_weights must contain 13 nonnegative values and a positive sum")
        weights /= weights.sum()
        spend = min(budget, float(policy.get("spend_fraction", 1.0)) * budget)
        channel_total = sum(max(0.0, float(v)) for v in channels.values())
        if channel_total <= 0:
            return out
        for name, fraction in channels.items():
            if not hasattr(out, name):
                raise ValueError(f"Unknown government action channel: {name}")
            setattr(out, name, spend * max(0.0, float(fraction)) / channel_total * weights)
        return out


class ICEnvironment:
    """13-sector dynamic economy with explicit IO accounting and intervention hooks."""

    SECTOR_TYPES = ["materials", "materials", "materials", "equipment", "equipment",
                    "electronic_input", "equipment", "manufacturing", "application",
                    "application", "application", "application", "application"]

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.seed = int(cfg.get("seed", 20261001))
        self.rng = np.random.default_rng(self.seed)
        mode = cfg.get("import_case", "proportional")
        if mode not in {"proportional", "intermediate_first", "final_first"}:
            raise ValueError("import_case must be proportional, intermediate_first, or final_first")
        with np.load(DATA / f"io_use_{mode}.npz") as dat:
            self.zd = dat["z_domestic"].copy()
            self.zm = dat["z_import"].copy()
            self.yd = dat["y_domestic"].copy()
            self.ym = dat["y_import"].copy()
            self.x = dat["x"].copy()
            self.va_annual = dat["value_added"].copy()
            self.imports = dat["imports"].copy()
        with (DATA / "sector_labels.csv").open(encoding="utf-8-sig", newline="") as file:
            self.labels = [r["io_label"] for r in csv.DictReader(file)][:N]
        roles = yaml.safe_load((DATA / "sector_roles.yaml").read_text(encoding="utf-8"))
        if len(roles["sectors"]) != N:
            raise ValueError("sector_roles.yaml must contain exactly 13 roles")
        for i, role in enumerate(roles["sectors"]):
            if role["sector_id"] != i + 1:
                raise ValueError("sector_roles.yaml must be ordered by sector_id 1..13")
        self.roles = roles["sectors"]
        self.agents = [SectorAgent(i, self.labels[i], self.roles[i]["type"],
                                   self.roles[i]["allowed_actions"]) for i in range(N)]
        self.government = GovernmentAgent()
        self.q0 = self.x[:N] / 4.0
        self.a_domestic = self.zd[:, :N] / self.x[None, :N]
        self.a_import = self.zm[:, :N] / self.x[None, :N]
        self.a_total = self.a_domestic + self.a_import
        full_a = self.zd / self.x[None, :]
        full_leontief = np.linalg.solve(np.eye(len(self.x)) - full_a, np.eye(len(self.x)))
        self.backward_linkage = full_leontief.sum(axis=0)[:N]
        self.backward_linkage /= self.backward_linkage.mean()
        self.a_va = self.va_annual[:N] / self.x[:N]
        self.base_outside_sales = self.zd[:N, N:].sum(axis=1) / 4.0
        self.base_final = self.yd[:N].sum(axis=1) / 4.0
        self.base_internal = self.zd[:N, :N] / 4.0
        self.base_external_inputs = self.zd[N:, :N] / 4.0
        self.base_import_inputs = self.zm[:, :N] / 4.0
        self._audit_base()
        self.reset()

    def _audit_base(self):
        row = self.base_internal.sum(axis=1) + self.base_outside_sales + self.base_final
        col = self.zd[:, :N].sum(axis=0) + self.zm[:, :N].sum(axis=0) + self.va_annual[:N]
        if not np.allclose(row, self.q0, rtol=1e-10, atol=1e-4):
            raise ValueError("Domestic IO row does not balance for 13 sectors")
        if not np.allclose(col, self.x[:N], rtol=1e-10, atol=1e-4):
            raise ValueError("IO columns do not balance for 13 sectors")

    def reset(self):
        self.t = 0
        self.output = self.q0.copy()
        self.capacity = self.q0.copy()
        self.finished = np.zeros(N)
        self.backlog = np.zeros(N)
        self.price = np.ones(N)
        self.last_price = np.ones(N)
        self.ai = np.zeros(N)
        self.tech = np.ones(N)
        self.absorb = np.asarray(self.cfg.get("absorption", [r["absorption"] for r in self.roles]), dtype=float)
        self.friction = np.asarray(self.cfg.get("friction", [r["friction"] for r in self.roles]), dtype=float)
        self.ai_effective = np.zeros(N)
        self.pressure = np.zeros((N, N))
        self.health = np.ones((N, N))
        self.qualification = np.ones((N, N))
        self.extra_lag = np.zeros((N, N), dtype=int)
        self.material_domestic = np.zeros((55, N))
        self.material_import = np.zeros((55, N))
        self.pending = {0: self.base_internal.copy()}
        self.capacity_projects = {}
        self.value_added = self.a_va * self.q0
        self.shortage = np.zeros(N)
        self.last_demand = self.q0.copy()
        self.last_deliveries = self.q0.copy()
        self.wip = self.q0.copy()
        self.fiscal_cost = 0.0
        self.fiscal_spent_period = 0.0
        self.repair_credit = np.zeros(N)
        self.budget_remaining = float(self.cfg.get("budget_share", 0.0)) * self.q0.sum()
        self.supplier_hhi = 1.0 / 3.0
        self.congestion_loss = 0.0
        self.congestion_cumulative = 0.0
        self.history = []
        return self.observations()

    def observations(self):
        return {"sectors": [a.observation(self) for a in self.agents],
                "government": self.government.observation(self)}

    def _shock(self):
        shock = self.cfg.get("shock", {})
        active = int(shock.get("start", -1)) <= self.t < int(shock.get("end", -1))
        capacity = np.ones(N)
        external = np.ones((55, N))
        if active:
            i = int(shock.get("sector", 8)) - 1
            if not 0 <= i < N:
                raise ValueError("shock.sector must be 1..13")
            capacity[i] -= float(shock.get("capacity_loss", 0.0))
            if shock.get("external_input_loss", 0.0):
                external[:, i] -= float(shock["external_input_loss"])
        return clip(capacity), clip(external), active

    @staticmethod
    def _resource_allocation(benefit: np.ndarray, cost: np.ndarray, budget: float):
        """KKT solution for sum(benefit*x - cost*x²/2), sum(x)<=budget, 0<=x<=1."""
        if budget <= 0:
            return np.zeros_like(benefit)
        lo, hi = 0.0, float(np.max(benefit))
        for _ in range(48):
            lam = (lo + hi) / 2.0
            x = clip((benefit - lam) / cost)
            if x.sum() > budget:
                lo = lam
            else:
                hi = lam
        return clip((benefit - hi) / cost)

    def _government(self, action: GovernmentAction):
        fields = ("ai", "capacity", "rd", "qualification", "inventory", "edge_repair")
        requested = sum(float(np.maximum(getattr(action, name), 0).sum()) for name in fields)
        factor = min(1.0, self.budget_remaining / requested) if requested > 0 else 0.0
        paid = {}
        for name in fields:
            arr = np.asarray(getattr(action, name), dtype=float)
            if arr.shape != (N,) or not np.all(np.isfinite(arr)) or np.any(arr < 0):
                raise ValueError(f"Government action {name} must be 13 finite nonnegative amounts")
            paid[name] = arr * factor
        spent = sum(v.sum() for v in paid.values())
        self.budget_remaining -= spent
        self.fiscal_cost += spent
        self.fiscal_spent_period = float(spent)
        output_scale = np.maximum(self.q0, 1.0)
        self.ai += 0.1 * paid["ai"] / output_scale
        self.tech += 0.05 * paid["rd"] / output_scale
        self.qualification = clip(self.qualification + 0.2 * paid["qualification"][None, :] / output_scale[None, :])
        self.repair_credit += paid["edge_repair"]
        lag = int(self.cfg.get("capacity_lag", 4))
        if np.any(paid["capacity"] > 0):
            self.capacity_projects[self.t + lag] = self.capacity_projects.get(self.t + lag, np.zeros(N)) + 0.1 * paid["capacity"]
        return paid

    def _nash_reward_fraction(self, sector: int, budget: float, shortage_rate: float) -> float:
        """Stylized conditional Nash contract over the available sector budget."""
        contract = self.cfg.get("contract", {})
        if budget <= 0:
            return 0.0
        quality = float(contract.get("platform_quality", 0.5))
        audit = float(contract.get("audit", 0.5))
        penalty = float(contract.get("penalty", 0.1))
        weight = float(contract.get("sector_bargaining_weight", 0.5))
        # Payoffs are normalized by the sector's baseline quarterly output.
        budget_rate = budget / max(self.q0[sector], 1.0)
        benefit = quality * (0.1 + shortage_rate)
        fractions = np.linspace(0.0, 1.0, 101)
        sector_surplus = np.maximum(benefit + fractions * budget_rate + audit * penalty - 0.05, 0.0)
        platform_surplus = np.maximum(benefit + (1.0 - fractions) * budget_rate - 0.02 * audit, 0.0)
        product = np.power(sector_surplus, weight) * np.power(platform_surplus, 1.0 - weight)
        return float(fractions[int(np.argmax(product))])

    def step(self, sector_actions: list[SectorAction], government_action: GovernmentAction):
        if len(sector_actions) != N:
            raise ValueError("Exactly 13 sector actions are required")
        for agent, action in zip(self.agents, sector_actions):
            for name in ("production_plan", "inventory_target", "price_change", "capex_share",
                         "rd_share", "ai_share", "coordination", "diversification"):
                value = float(getattr(action, name))
                if not math.isfinite(value):
                    raise ValueError(f"Nonfinite {name} action for sector {agent.index + 1}")
                if name != "price_change" and value < 0:
                    raise ValueError(f"Negative {name} action for sector {agent.index + 1}")
                if name in ("capex_share", "rd_share", "ai_share", "coordination", "diversification") and value > 1:
                    raise ValueError(f"{name} exceeds one for sector {agent.index + 1}")
                if name not in ("production_plan", "inventory_target") and name not in agent.allowed_actions and abs(value) > 1e-12:
                    raise ValueError(f"Disallowed {name} action for sector {agent.index + 1}")
        modules = set(self.cfg.get("modules", []))
        self.capacity += self.capacity_projects.pop(self.t, np.zeros(N))
        cap_shock, external_shock, shock_active = self._shock()
        paid = self._government(government_action)
        planned = np.asarray([a.production_plan for a in sector_actions], dtype=float)
        if not np.all(np.isfinite(planned)) or np.any(planned < 0):
            raise ValueError("production_plan must be finite and nonnegative")
        planned = np.minimum(planned, 2.0 * self.q0)
        target = int(self.cfg.get("demand_sector", 12)) - 1
        growth = float(self.cfg.get("demand_growth", 0.0))
        demand_boost = (1.0 + growth) ** self.t - 1.0
        demand_shock = self.cfg.get("demand_shock", {})
        if int(demand_shock.get("start", -1)) <= self.t < int(demand_shock.get("end", -1)):
            demand_boost += float(demand_shock.get("increase", 0.0))
        final = self.base_final.copy()
        if 0 <= target < N:
            final[target] *= 1.0 + demand_boost
        # Explicit source-specific material accounts; the remaining 42 sectors and imports
        # are not reassigned to the 13 observed agents.
        arrivals = self.pending.pop(self.t, np.zeros((N, N)))
        self.material_domestic[:N] += arrivals
        max_external = float(self.cfg.get("external_supply_elasticity", 1.25))
        for source in range(N, 55):
            need = self.a_domestic[source] * planned
            self.material_domestic[source] += np.minimum(need, self.base_external_inputs[source - N] * max_external) * external_shock[source]
        for source in range(55):
            need = self.a_import[source] * planned
            # Import and domestic goods are separately tracked; this is not an assumed
            # source substitution rule.
            self.material_import[source] += np.minimum(need, self.base_import_inputs[source] * max_external) * external_shock[source]
        if "inventory" in modules and paid["inventory"].sum() > 0:
            # Reserve purchases come only from the explicit other-42 domestic
            # supply boundary. They are recorded as extra external purchases.
            for j in range(N):
                share = self.a_domestic[N:, j]
                if share.sum() > 0:
                    self.material_domestic[N:, j] += paid["inventory"][j] * share / share.sum()
        desired_internal = self.a_domestic[:N] * planned[None, :]
        target_quarters = np.asarray([a.inventory_target for a in sector_actions], dtype=float)
        if np.any(target_quarters > 0):
            gap = np.maximum(target_quarters[None, :] * self.base_internal - self.material_domestic[:N], 0.0)
            desired_internal += float(self.cfg.get("inventory_adjustment", 0.25)) * gap
        desired_sales = desired_internal.sum(axis=1) + self.base_outside_sales + final + self.backlog
        effective_ai = clip(self.ai * self.absorb * self.cfg.get("time_fit", 0.9) / (1.0 + self.friction), 0.0, 3.0)
        self.ai_effective = effective_ai
        capacity_eff = self.capacity * cap_shock
        if "ai" in modules:
            capacity_eff *= 1.0 + float(self.cfg.get("ai_productivity", 0.1)) * effective_ai
        if "innovation" in modules:
            capacity_eff *= 1.0 + float(self.cfg.get("technology_productivity", 0.1)) * np.maximum(self.tech - 1.0, 0.0)
        if "manufacturing" in modules:
            capacity_eff[7] *= float(self.cfg.get("manufacturing_yield", 1.0))
        if "packaging" in modules:
            capacity_eff[7] *= float(self.cfg.get("packaging_limit", 1.0))
        if "equipment" in modules:
            capacity_eff[7] *= float(self.cfg.get("equipment_availability", 1.0))
        input_limit = np.full(N, np.inf)
        for j in range(N):
            limits = []
            for coeff, stock in ((self.a_domestic[:, j], self.material_domestic[:, j]),
                                 (self.a_import[:, j], self.material_import[:, j])):
                positive = coeff > 1e-12
                if positive.any():
                    limits.append(float(np.min(stock[positive] / coeff[positive])))
            if limits:
                input_limit[j] = min(limits)
        q = np.minimum.reduce([planned + self.backlog, desired_sales, capacity_eff, input_limit])
        q = np.maximum(q, 0.0)
        self.material_domestic = np.maximum(self.material_domestic - self.a_domestic * q[None, :], 0.0)
        self.material_import = np.maximum(self.material_import - self.a_import * q[None, :], 0.0)
        # Preserve essential intermediate commitments before allocating the
        # residual to other-42 buyers and final users. This avoids artificial
        # self-starvation from a demand shock in an IO sector with self-inputs.
        sale_request = desired_internal.sum(axis=1) + self.base_outside_sales + final + self.backlog
        available_finished = q + self.finished
        internal_request = desired_internal.sum(axis=1)
        internal_ratio = np.minimum(1.0, available_finished / np.maximum(internal_request, 1e-12))
        shipped_internal = desired_internal * internal_ratio[:, None]
        residual = np.maximum(available_finished - shipped_internal.sum(axis=1), 0.0)
        other_request = self.base_outside_sales + final + self.backlog
        other_ratio = np.minimum(1.0, residual / np.maximum(other_request, 1e-12))
        sold_final = final * other_ratio
        sold_outside = self.base_outside_sales * other_ratio
        served_backlog = self.backlog * other_ratio
        self.congestion_loss = 0.0
        if "supplier_choice" in modules:
            # Three stylized capacity channels within each source sector. These
            # are not observed firms and do not change the IO product identity.
            capacity_shares = np.array([0.45, 0.40, 0.35])
            quality = np.array([1.0, 0.90, 0.80])
            precision = float(self.cfg.get("search_precision", 1.0))
            hhis = []
            for i in range(N):
                requests = shipped_internal[i].copy()
                if requests.sum() <= 0:
                    continue
                scores = precision * quality - np.array([0.0, 0.03, 0.05])
                probs = np.exp(scores - scores.max())
                probs /= probs.sum()
                slot_demand = probs * requests.sum()
                slot_capacity = self.base_internal[i].sum() * capacity_shares * float(self.cfg.get("supplier_channel_capacity", 1.0))
                served = np.divide(np.minimum(slot_demand, slot_capacity),
                                   np.maximum(slot_demand, 1e-12))
                fraction = float(np.dot(probs, served))
                shipped_internal[i] *= fraction
                self.congestion_loss += float(requests.sum() * (1.0 - fraction))
                hhis.append(float(np.sum(probs ** 2)))
            if hhis:
                self.supplier_hhi = float(np.mean(hhis))
        self.congestion_cumulative += self.congestion_loss
        delivered = shipped_internal.sum(axis=1) + sold_final + sold_outside + served_backlog
        self.finished = np.maximum(available_finished - delivered, 0.0)
        self.shortage = np.maximum(sale_request - delivered, 0.0)
        self.shortage[self.shortage < 1e-9 * self.q0] = 0.0
        retained = float(self.cfg.get("backlog_retention", 0.25))
        self.backlog = np.minimum(retained * self.shortage,
                                  float(self.cfg.get("max_backlog_quarters", 2.0)) * self.q0)
        # Shipping is one quarter behind ordering; extra certification lag is
        # applied to subsequent shipments rather than weakening physical units.
        for i in range(N):
            for j in range(N):
                if shipped_internal[i, j] <= 0:
                    continue
                delay = 1 + int(self.extra_lag[i, j])
                deliver_t = self.t + delay
                if deliver_t not in self.pending:
                    self.pending[deliver_t] = np.zeros((N, N))
                self.pending[deliver_t][i, j] += shipped_internal[i, j] * self.health[i, j] * self.qualification[i, j]
        # Edge dynamics: positive AI-load/absorption mismatch, shock and unmet
        # orders raise pressure; verified repair and coordination reduce it.
        if "edge" in modules:
            coordination = np.asarray([a.coordination for a in sector_actions])
            mismatch = np.maximum(effective_ai[:, None] - self.absorb[None, :], 0.0)
            edge_gap = np.maximum(desired_internal - arrivals, 0.0) / np.maximum(desired_internal, 1.0)
            self.pressure = np.maximum(0.0, 0.70 * self.pressure + 0.1 * mismatch +
                                       0.05 * edge_gap - 0.05 * coordination[None, :] -
                                       0.5 * self.repair_credit[None, :] / np.maximum(self.q0[None, :], 1.0))
            self.health = clip(1.0 - 0.05 * self.pressure,
                               float(self.cfg.get("edge_health_floor", 0.85)), 1.0)
        self.repair_credit[:] = 0.0
        if "qualification" in modules:
            self.qualification = clip(self.qualification + 0.01 * np.asarray([a.diversification for a in sector_actions])[None, :])
        # Price, investment and innovation rules are off unless a task enables them.
        if "price" in modules:
            imbalance = np.divide(sale_request, np.maximum(available_finished, 1.0)) - 1.0
            self.price *= np.exp(clip(0.05 * imbalance, -0.05, 0.05))
            if "market_power" in modules:
                self.price *= 1.0 + float(self.cfg.get("hhi_markup", 0.01)) * max(0.0, self.supplier_hhi - 1.0 / 3.0)
            price_actions = np.asarray([a.price_change for a in sector_actions])
            self.price *= np.exp(np.clip(price_actions, -0.1, 0.1))
        costs = (self.a_total[:N].T @ self.price) * q + (self.a_total[N:].sum(axis=0) * q)
        labor_other_cost = self.a_va * q * float(self.cfg.get("labor_share_of_va", 0.8))
        if "ai" in modules:
            labor_other_cost *= np.maximum(0.0, 1.0 - float(self.cfg.get("ai_cost_reduction", 0.1)) * effective_ai)
        profit = self.price * delivered - costs - labor_other_cost - 0.1 * self.finished - 0.2 * self.shortage
        self.value_added = self.a_va * q
        self.wip = 0.5 * self.wip + 0.5 * q
        private_investment = np.zeros(N)
        private_rd = np.zeros(N)
        private_ai = np.zeros(N)
        if "investment" in modules:
            capex = np.asarray([a.capex_share for a in sector_actions]) * self.q0
            private_investment = capex
            lag = int(self.cfg.get("capacity_lag", 4))
            self.capacity_projects[self.t + lag] = self.capacity_projects.get(self.t + lag, np.zeros(N)) + float(self.cfg.get("capital_efficiency", 0.1)) * capex
        if "innovation" in modules:
            rd = np.asarray([a.rd_share for a in sector_actions]) * self.q0
            private_rd = rd
            rd_gain = 1.0 + float(self.cfg.get("innovation_ai_gain", 0.5)) * effective_ai
            self.tech = (1.0 - float(self.cfg.get("tech_depreciation", 0.001))) * self.tech + float(self.cfg.get("rd_efficiency", 0.01)) * rd_gain * rd / np.maximum(self.q0, 1)
        if "ai" in modules:
            ai_spend = np.asarray([a.ai_share for a in sector_actions]) * self.q0
            private_ai = ai_spend
            self.ai = clip(self.ai + float(self.cfg.get("ai_conversion", 0.1)) * ai_spend / np.maximum(self.q0, 1), 0.0, 3.0)
        if "coordination" in modules:
            shortage_rate = self.shortage / np.maximum(sale_request, 1)
            incentives = paid["qualification"] / np.maximum(self.q0, 1)
            if "contract" in modules:
                fractions = np.array([self._nash_reward_fraction(j, paid["qualification"][j], shortage_rate[j])
                                      for j in range(N)])
                audit = float(self.cfg.get("contract", {}).get("audit", 0.5))
                penalty = float(self.cfg.get("contract", {}).get("penalty", 0.1))
                incentives = incentives * fractions + audit * penalty
            coordination_prob = sigmoid(2.0 * incentives + 0.5 * shortage_rate - 0.5)
            if self.cfg.get("stochastic_coordination", False):
                coordinated = self.rng.random(N) < coordination_prob
            else:
                coordinated = coordination_prob
            coordination_rate = float(np.mean(coordinated))
            self.coordination_allocation = [self._resource_allocation(
                np.array([1.0, 0.8, 0.7, 0.6, 0.9]) * float(c),
                np.ones(5), float(self.cfg.get("coordination_budget", 1.0))) for c in coordinated]
            for j, effort in enumerate(self.coordination_allocation):
                self.pressure[:, j] = np.maximum(0.0, self.pressure[:, j] - 0.02 * effort[2] - 0.03 * effort[4])
                self.qualification[:, j] = clip(self.qualification[:, j] + 0.01 * effort[3])
            self.health = clip(1.0 - 0.05 * self.pressure,
                               float(self.cfg.get("edge_health_floor", 0.85)), 1.0)
        else:
            self.coordination_allocation = [np.zeros(5) for _ in range(N)]
            coordination_rate = 0.0
        self.output = q
        cashflow = profit - private_investment - private_rd - private_ai
        self.last_demand = sale_request
        self.last_deliveries = delivered
        weights = self.cfg.get("welfare_weights", {})
        service = float(1.0 - self.shortage.sum() / max(sale_request.sum(), 1.0))
        technology_gain = float(np.dot(self.tech - 1.0, self.a_va * self.q0))
        price_volatility = float(np.sum(np.abs(self.price - self.last_price) * self.q0))
        welfare = float(self.value_added.sum() * float(weights.get("value_added", 1.0)) +
                        technology_gain * float(weights.get("technology", 0.0)) +
                        service * self.value_added.sum() * float(weights.get("resilience", 0.0)) -
                        self.shortage.sum() * float(weights.get("shortage", 0.2)) -
                        price_volatility * float(weights.get("price_volatility", 0.0)) -
                        self.fiscal_spent_period * float(weights.get("fiscal_cost", 1.0)) -
                        self.supplier_hhi * self.value_added.sum() * float(weights.get("concentration", 0.0)))
        self.last_price = self.price.copy()
        record = {"period": self.t, "output": float(q.sum()), "base_output": float(self.q0.sum()),
                  "final_demand": float(final.sum()), "final_delivered": float(sold_final.sum()),
                  "final_shortage": float(np.maximum(final - sold_final, 0.0).sum()),
                  "final_fill_rate": float(sold_final.sum() / max(final.sum(), 1e-12)),
                  "outside_demand": float(self.base_outside_sales.sum()),
                  "outside_delivered": float(sold_outside.sum()),
                  "internal_orders": float(desired_internal.sum()),
                  "internal_delivered": float(shipped_internal.sum()),
                  "value_added": float(self.value_added.sum()), "shortage": float(self.shortage.sum()),
                  "backlog": float(self.backlog.sum()), "price_index": float(np.average(self.price, weights=self.q0)),
                  "edge_health_mean": float(np.mean(self.health)), "ai_effective_mean": float(np.mean(self.ai_effective)),
                  "supplier_hhi": float(self.supplier_hhi), "congestion_loss": float(self.congestion_loss),
                  "congestion_cumulative": float(self.congestion_cumulative),
                  "service_rate": service, "technology_gain": technology_gain,
                  "technology_mean": float(np.mean(self.tech)),
                  "coordination_rate": coordination_rate,
                  "qualification_mean": float(np.mean(self.qualification)),
                  "government_inventory_spend": float(paid["inventory"].sum()),
                  "government_qualification_spend": float(paid["qualification"].sum()),
                  "government_edge_repair_spend": float(paid["edge_repair"].sum()),
                  "profit_total": float(profit.sum()),
                  "private_investment": float(private_investment.sum()),
                  "private_rd": float(private_rd.sum()), "private_ai": float(private_ai.sum()),
                  "fiscal_cost_cumulative": float(self.fiscal_cost), "welfare": welfare,
                  "shock_active": int(shock_active)}
        self.history.append(record)
        self.t += 1
        return self.observations(), {"sectors": cashflow.tolist(), "government": welfare}, False, record
