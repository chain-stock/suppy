from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from suppy import Edge, Simulator
from suppy.supplychain import SupplyChain
from suppy.leadtime import LeadTime
from suppy.node import Node, Orders, Sales, Stock
from suppy.pipeline import Pipeline, Receipt
from suppy.strategy.control.single_echelon.rsq import se_RsQ
from suppy.strategy.release.fractional import Fractional


@pytest.mark.parametrize("run_args", ((1, 3), (3,)))
@patch("suppy.simulator.Simulator.simulate_period")
def test_simulator_run(sim_period_mock, run_args):
    """Test the different calls to run"""
    sc = SupplyChain()
    sim = Simulator(sc, MagicMock(), MagicMock())
    sim.run(*run_args)
    sim_period_mock.assert_has_calls(
        [
            call(period=1, loop=0),
            call(period=2, loop=0),
            call(period=3, loop=0),
        ]
    )


def test_simulator_output():
    """Test the Simulatort.output property"""
    sc = SupplyChain(
        nodes=[Node("A"), Node("B")],
        edges=[Edge("B", "A", 1)],
    )
    sim = Simulator(sc, MagicMock(), MagicMock())

    assert list(sim.output) == []

    sim.run(1)

    output = list(sim.output)
    assert len(output) == 1
    assert isinstance(output[0], Path)

    sim.stream = StringIO()
    sim.run(1)

    output = list(sim.output)
    assert len(output) == 1
    assert isinstance(output[0], Path)


def test_simulate_period():
    """Test if simulate period has the expected behavior."""
    sc = SupplyChain(
        nodes=[
            Node(
                "A",
                data=dict(
                    order_quantity=30,
                    reorder_level=25,
                    review_time=1,
                    safety_stock=1,
                ),
                llc=0,
                sales=Sales({1: [10], 2: [10], 3: [10]}),
                lead_time=LeadTime(default=1),
                stock=Stock({"A": 15, "C": 5}),
            ),
            Node(
                "B",
                data=dict(
                    order_quantity=25,
                    reorder_level=40,
                    review_time=1,
                ),
                llc=0,
                sales=Sales({1: [15], 2: [15], 3: [15]}),
                lead_time=LeadTime(default=2),
                pipeline=Pipeline([Receipt(sku_code="D", eta=1, quantity=75)]),
                backorders=5,
            ),
            Node(
                "C",
                data=dict(
                    order_quantity=150,
                    reorder_level=20,
                    review_time=1,
                ),
                llc=1,
                lead_time=LeadTime({1: 3, 2: 7}, default=3),
                stock=Stock({"C": 200}),
            ),
            Node(
                "D",
                data=dict(
                    order_quantity=200,
                    reorder_level=20,
                    review_time=2,
                ),
                llc=1,
                lead_time=LeadTime(default=4),
                orders=Orders({"B": 15}),
                stock=Stock({"D": 40}),
                pipeline=Pipeline([Receipt(sku_code="D", eta=2, quantity=200)]),
            ),
        ],
        edges=[
            Edge(source="C", destination="A", number=2),
            Edge(source="D", destination="A", number=1),
            Edge(source="D", destination="B", number=3),
        ],
    )

    sim = Simulator(
        control_strategy=se_RsQ(sc), release_strategy=Fractional(), supply_chain=sc
    )
    sim.run(1)

    assert sc.nodes["A"].pipeline == [
        Receipt(sku_code="C", eta=1, quantity=60),
        Receipt(sku_code="D", eta=1, quantity=7),
    ]
    assert sc.nodes["A"].stock == {"A": 5, "C": 5, "D": 0}


def test_simulator_invalid_strategies():
    """Test if an error is raised when the provided strategies
    don't implement the correct interface"""
    sc = SupplyChain()
    with pytest.raises(TypeError, match=r"control_strategy \(type\) is not compatible"):
        Simulator(sc, control_strategy=int, release_strategy=Fractional())  # type: ignore
    with pytest.raises(TypeError, match=r"release_strategy \(type\) is not compatible"):
        Simulator(sc, control_strategy=se_RsQ(sc), release_strategy=int)  # type: ignore


def test_simulator_validate_llc():
    """Test if an error is raised if any node does not have a valid llc set"""
    sc = SupplyChain(nodes=[Node("A")])
    sc.nodes["B"] = Node("B")
    sim = Simulator(sc, MagicMock(), MagicMock())
    with pytest.raises(ValueError, match=r"Node\(B\) has an invalid llc: -1"):
        sim.run(1)


def test_simulator_loop():
    """Test if the loop functionality correctly carries over the state from one loop to the next."""
    sc = SupplyChain(
        nodes=[
            Node(
                "B",
                sales=Sales({1: [10]}),
                stock=Stock({"B": 35}),
                data={
                    "review_time": 1,
                    "reorder_level": 1,
                    "order_quantity": 1,
                },
            ),
            Node(
                "A",
                stock=Stock({"A": 0}),
                orders=Orders({"B": 50}),
                pipeline=Pipeline([Receipt(sku_code="A", eta=10, quantity=200)]),
                data={
                    "review_time": 1,
                    "reorder_level": 1,
                    "order_quantity": 1,
                },
            )
        ]
    )
    sim = Simulator(
        control_strategy=se_RsQ(sc), release_strategy=Fractional(), supply_chain=sc
    )
    sim.run(1, loops=3)

    assert sc.nodes["B"].stock["B"] == 5
    assert sc.nodes["A"].orders == Orders({"B": 50})
    assert sc.nodes["A"].pipeline == Pipeline([Receipt(sku_code="A", eta=7, quantity=200)])
