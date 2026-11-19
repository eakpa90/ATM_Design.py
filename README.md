# ATM_Design.py — Algorithmic Thinking & Defensive ATM Simulation

A structured field exercise in **algorithmic thinking**, **defensive system design**, and **modular Python implementation** built around a classic problem: *"Withdraw money from an ATM."*

Rather than jumping straight into code, this project separates the **Problem** (the goal), the **Algorithm** (the ordered steps, loops, branches, and failure handlers), and the **Program** (the executable Python implementation and automated tests).

---

## Problem → Algorithm → Program

* **Problem (The Goal):** *"Withdraw money from an ATM."* Describes what needs to be achieved without specifying how it happens.
* **Algorithm (The Procedure):** A deterministic sequence of steps, decision checks, retry loops, and rollback rules that solves the problem safely—including when hardware, networks, or users behave unexpectedly.
* **Program (The Implementation):** Modular Python classes (`Card`, `Account`, `HardwareInterface`, `BankServer`, `ATMController`) paired with an interactive terminal app (`atm_cli.py`) and automated unit tests (`test_atm.py`).

---

## Project Structure

```text
ATM_Design.py/
├── README.md                  # Project overview, design rationale, CLI usage, and testing guide
├── .gitignore                 # Ignores Python cache, virtual environments, and pytest artifacts
├── docs/
│   ├── flowchart.md           # Visual flowchart of happy path, loops, and failure exits
│   └── pseudocode.md          # Failure-aware pseudo-code specification
├── src/
│   ├── __init__.py            # Marks src as a Python package
│   ├── atm_controller.py      # Core domain models, hardware/bank interfaces, and state logic
│   └── atm_cli.py             # Interactive command-line interface (CLI) simulation
└── tests/
    ├── __init__.py            # Marks tests as a Python package
    └── test_atm.py            # Automated pytest suite verifying core flows and failure paths