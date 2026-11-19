# ATM Withdrawal Flowchart

This document maps the withdrawal algorithm visually. In flowchart notation:

* **Rectangles `[ ... ]`** represent system actions, state updates, or hardware/server calls.
* **Parallelograms `( [Input/Output] ... )`** represent user prompts, inputs, or screen outputs.
* **Diamonds `[Decision: ... ]`** represent conditional branching points.

---

## Visual Flow

```text
[ START ]
   │
   ▼
( [Input] Insert / Tap Card ) ──► [Decision: Card Readable & Valid?]
                                        ├── NO  ──► [Eject Card & Display Error] ──► [ END ]
                                        └── YES
                                              │
                                              ▼
                                    [Initialize: attempts = 0]
                                              │
                                              ▼
                                    ( [Input] Request PIN )
                                              │
                                              ▼
                             ┌───► [Decision: PIN Correct?]
                             │           ├── YES ──► [Proceed to Menu] ──┐
                             │           └── NO                          │
                             │                 │                         │
                             │                 ▼                         │
                             │        [Increment attempts + 1]           │
                             │                 │                         │
                             │                 ▼                         │
                             │     [Decision: attempts == 3?]            │
                             │           ├── YES ──► [Retain Card & Lock] ──► [ END ]
                             │           └── NO  ──┘ (Warn & Loop back)  │
                             └───────────────────────────────────────────┘
                                                                         │
                                                                         ▼
                                                          ( [Input] Select Withdrawal & Amount )
                                                                         │
                                                                         ▼
                                                          [Decision: Amount Valid & Within Limits?]
                                                                         ├── NO  ──► [Display Error] ──► (Loop to Amount Entry)
                                                                         └── YES
                                                                               │
                                                                               ▼
                                                            [Server Call: Check Balance & Hold Funds]
                                                                         │
                                                                         ▼
                                                          [Decision: Server Response Status]
                                                                         ├── INSUFFICIENT FUNDS ──► [Prompt Retry/Cancel]
                                                                         ├── NETWORK TIMEOUT    ──► [Abort & Safe Exit] ──► [ END ]
                                                                         └── APPROVED
                                                                               │
                                                                               ▼
                                                            [Hardware Action: Dispense Cash Bills]
                                                                         │
                                                                         ▼
                                                          [Decision: Mechanical Jam Detected?]
                                                                         ├── YES ──► [Trigger Maintenance & Refund Ledger] ──► [ END ]
                                                                         └── NO
                                                                               │
                                                                               ▼
                                                             [Update Ledger & Print/Digital Receipt]
                                                                         │
                                                                         ▼
                                                                [Eject Card & Open Shutter]
                                                                         │
                                                                         ▼
                                                       [Timer: User Takes Card / Takes Cash?]
                                                                         ├── TIMEOUT (No action) ──► [Retract Card & Cash to Safe Bin]
                                                                         └── SUCCESSFUL REMOVAL ──┘
                                                                               │
                                                                               ▼
                                                                   [Clear Session Memory]
                                                                               │
                                                                               ▼
                                                                           [ END ]