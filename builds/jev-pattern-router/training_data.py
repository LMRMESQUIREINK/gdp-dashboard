"""
Labeled examples for TrainedJudge, in this project's own RUTHLESS TRADING
GOLD domain — routing a natural-language query to one of
/builds/trading-jarvis/jarvis_orchestrator.py's real tool categories
(signal_pipeline: check_signal/check_fundamentals; prop_firm: the three
prop_firm_* tools; swamp_decompose: the Swamp Intelligence decomposition
tool; other: nothing here fits). Three questions per example, matching
the "ask everything at once" pattern from the source analysis: category
(Choice), destructive (Noul — would this, if auto-executed, do something
irreversible?), priority (Score, 0=routine, 1=elevated, 2=urgent).

TRAIN is what TrainedJudge is fit on. TEST is held out — never shown to
the classifier — used only in test_judge.py's accuracy/confidence check,
matching the source tutorial's own discipline of freezing the test set
before measuring anything.
"""
from __future__ import annotations

TRAIN: list[dict] = [
    # signal_pipeline
    {"text": "Check AAPL for a buy or sell signal today", "category": "signal_pipeline", "destructive": "no", "priority": 1},
    {"text": "What's the current RSI reading on TSLA?", "category": "signal_pipeline", "destructive": "no", "priority": 0},
    {"text": "Is NVDA showing a breakout signal right now?", "category": "signal_pipeline", "destructive": "no", "priority": 1},
    {"text": "Pull the latest fundamentals for MSFT", "category": "signal_pipeline", "destructive": "no", "priority": 0},
    {"text": "Run the EMA crossover check on SPY", "category": "signal_pipeline", "destructive": "no", "priority": 0},
    {"text": "Does GOOGL have a bullish signal this week?", "category": "signal_pipeline", "destructive": "no", "priority": 0},
    {"text": "Give me the fundamentals snapshot for AMZN", "category": "signal_pipeline", "destructive": "no", "priority": 0},
    {"text": "Check for a sell signal on QQQ immediately, I need to know now", "category": "signal_pipeline", "destructive": "no", "priority": 2},

    # prop_firm
    {"text": "Check sizing for 2 ES contracts on a 50K TPT account", "category": "prop_firm", "destructive": "no", "priority": 0},
    {"text": "What's my trailing drawdown floor right now on the 100K account?", "category": "prop_firm", "destructive": "no", "priority": 1},
    {"text": "What's my pass probability for the TPT eval with 8 days left?", "category": "prop_firm", "destructive": "no", "priority": 0},
    {"text": "Compare sizing strategies for 1 vs 3 contracts on my funded account", "category": "prop_firm", "destructive": "no", "priority": 0},
    {"text": "How much room do I have left on my daily loss limit today?", "category": "prop_firm", "destructive": "no", "priority": 1},
    {"text": "Give me a session report for my 75K evaluation account", "category": "prop_firm", "destructive": "no", "priority": 0},
    {"text": "I'm close to my trailing drawdown, how many contracts can I safely hold right now?", "category": "prop_firm", "destructive": "no", "priority": 2},
    {"text": "Run a Monte Carlo pass probability check for my 150K account", "category": "prop_firm", "destructive": "no", "priority": 0},

    # swamp_decompose
    {"text": "Decompose this objective: grow the account by 5% this month", "category": "swamp_decompose", "destructive": "no", "priority": 0},
    {"text": "Break down the task tree for expanding into options trading", "category": "swamp_decompose", "destructive": "no", "priority": 0},
    {"text": "Run swamp decomposition on 'build a diversified futures strategy'", "category": "swamp_decompose", "destructive": "no", "priority": 0},
    {"text": "What are the event packets for this new trading objective?", "category": "swamp_decompose", "destructive": "no", "priority": 0},
    {"text": "Decompose my goal of reaching funded status by year end", "category": "swamp_decompose", "destructive": "no", "priority": 0},
    {"text": "Build me a task tree for diversifying across three new symbols", "category": "swamp_decompose", "destructive": "no", "priority": 0},

    # other / out of scope
    {"text": "What's the weather like today", "category": "other", "destructive": "no", "priority": 0},
    {"text": "Tell me a joke about trading", "category": "other", "destructive": "no", "priority": 0},
    {"text": "How do I set up my email client", "category": "other", "destructive": "no", "priority": 0},
    {"text": "What time is it in Tokyo right now", "category": "other", "destructive": "no", "priority": 0},
    {"text": "Recommend a good book about markets", "category": "other", "destructive": "no", "priority": 0},

    # destructive examples (irreversible actions, spread across categories so the
    # destructive question learns the pattern, not just one category)
    {"text": "Delete all my saved positions and reset the account", "category": "prop_firm", "destructive": "yes", "priority": 2},
    {"text": "Force-close every open position right now without confirmation", "category": "prop_firm", "destructive": "yes", "priority": 2},
    {"text": "Wipe the positions store and start fresh", "category": "prop_firm", "destructive": "yes", "priority": 1},
    {"text": "Cancel all pending orders and liquidate everything immediately", "category": "signal_pipeline", "destructive": "yes", "priority": 2},
    {"text": "Clear out the entire trade history, I don't need any of it", "category": "other", "destructive": "yes", "priority": 1},
    {"text": "Erase all stored account data permanently", "category": "prop_firm", "destructive": "yes", "priority": 1},
    {"text": "Remove every open order without asking me first", "category": "signal_pipeline", "destructive": "yes", "priority": 2},
    {"text": "Reset everything and discard all my trade history for good", "category": "other", "destructive": "yes", "priority": 1},
]

TEST: list[dict] = [
    {"text": "Check SPY for a current trading signal", "category": "signal_pipeline", "destructive": "no", "priority": 0},
    {"text": "How urgent is my drawdown situation on the 50K account?", "category": "prop_firm", "destructive": "no", "priority": 1},
    {"text": "Decompose the objective of scaling to a 150K funded account", "category": "swamp_decompose", "destructive": "no", "priority": 0},
    {"text": "What's a good recipe for pasta", "category": "other", "destructive": "no", "priority": 0},
    {"text": "Delete every position on file right now, no confirmation needed", "category": "prop_firm", "destructive": "yes", "priority": 2},
    {"text": "Check my fundamentals on AAPL please", "category": "signal_pipeline", "destructive": "no", "priority": 0},
    {"text": "What's my current pass probability with 5 days left in the eval?", "category": "prop_firm", "destructive": "no", "priority": 0},
    # Deliberately ambiguous, same spirit as the source tutorial's M10
    # ("I want to change my plan, and I also need a copy of last month's
    # invoice") — mixes signal-pipeline and prop-firm framing on purpose.
    {"text": "Check the signal on my 50K account's ES position and tell me if I'm near my drawdown limit", "category": "prop_firm", "destructive": "no", "priority": 1},
]
