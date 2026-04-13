"""
vita_brain.py
Rule-based AI response engine for VITA.
No external API key required. Responds intelligently based on
energy level, task context, wellbeing data, and user message keywords.
"""

import random
from datetime import datetime


# ── Energy-level response templates ─────────────────────────────────────────

ENERGY_INSIGHTS = {
    "high": [
        "Your energy is at peak capacity right now. This is the best window to engage with your most demanding tasks — the ones that require deep focus, creative output, or complex decision-making. Front-load your hardest work before this window closes.",
        "Peak state detected. Prioritise tasks that require full cognitive bandwidth. Difficult conversations, deep work sessions, and complex problem-solving all belong here. Guard this window — it is finite.",
        "High energy is a limited resource. Use it on tasks that only you can do, and that require your full mental presence. Routine admin and low-stakes communication can wait for your lower-energy periods later in the day.",
    ],
    "medium": [
        "You are in a steady, functional state. This is ideal for collaborative work, moderately complex tasks, and anything that benefits from a calm, deliberate approach. Avoid burning this energy on trivial tasks.",
        "Steady-state energy is well-suited for meetings, structured work, and tasks that require consistency rather than intensity. Save your high-energy windows for tomorrow if you spent them already.",
        "At medium capacity, you can sustain reliable output without burning reserves. Mix focused work with lighter tasks. Avoid context-switching too often — it costs more energy than it appears.",
    ],
    "low": [
        "Low energy means your body and mind are asking for less friction. Stick to familiar, low-decision tasks: replying to messages, organising, reviewing notes. Protect yourself from high-stakes decisions right now.",
        "In a low-energy state, your best move is to reduce cognitive load. Short, contained tasks are your ally. Avoid starting anything complex that you cannot finish — incomplete loops drain more energy than rest.",
        "Low battery mode engaged. Hydrate, eat if you have not recently, and sequence only simple tasks. Your energy will recover faster if you do not push against it.",
    ],
    "depleted": [
        "You are running on reserves. The most productive thing you can do right now is rest. Even 20 minutes of genuine rest returns more value than 2 hours of depleted effort.",
        "Depletion is a signal, not a failure. Your system needs to recover before it can output anything meaningful. If possible, step away from all task pressure entirely for at least one cycle.",
        "At this energy level, forcing output creates compounding debt. Reschedule non-critical tasks, communicate your availability honestly, and treat recovery as your highest-priority item.",
    ],
}

WELLBEING_TIPS = [
    "Drink water before caffeine. Dehydration is the most common cause of afternoon cognitive decline, and most people never trace it back to morning hydration habits.",
    "A five-minute walk taken before a difficult task resets the prefrontal cortex more effectively than staring at a screen during a mental block.",
    "Eating at regular intervals stabilises blood glucose, which directly controls focus duration and mood stability. Skipping meals is not efficiency — it is borrowing energy from later.",
    "Short rest periods between tasks are not laziness. They are how your brain consolidates learning and prepares for the next focus cycle. Build them into your schedule deliberately.",
    "Posture affects breathing, which affects oxygen delivery to the brain. Sit upright, relax your shoulders, and take three slow breaths before resuming focused work.",
    "The 20-20-20 rule exists because screen fatigue is cumulative and invisible until it becomes debilitating. Every 20 minutes, look at something 20 feet away for 20 seconds.",
    "Movement does not require a workout. Standing, stretching, or walking to another room for two minutes every hour is enough to reduce the physiological cost of prolonged sitting.",
    "Sleep is the single most impactful recovery tool available. One night of poor sleep reduces cognitive performance by approximately 30 percent. Protect your sleep window above all else.",
]

GREETINGS = [
    "VITA online. I am your energy-aware life assistant. Tell me what is on your mind.",
    "System ready. What would you like to work through today?",
    "Connected. I have your task and energy context loaded. How can I help you prioritise?",
]


# ── Keyword-intent detection ─────────────────────────────────────────────────

def detect_intent(message: str) -> str:
    msg = message.lower()

    if any(w in msg for w in ["tired", "exhausted", "drained", "no energy", "burnt out", "burnout"]):
        return "low_energy"

    if any(w in msg for w in ["overwhelmed", "too much", "stress", "anxious", "panic", "behind"]):
        return "overwhelmed"

    if any(w in msg for w in ["what should i do", "what to do", "where to start", "prioritise", "prioritize", "next task", "first task"]):
        return "prioritise"

    if any(w in msg for w in ["water", "hydrat", "drink"]):
        return "hydration"

    if any(w in msg for w in ["eat", "food", "hungry", "meal", "lunch", "breakfast", "dinner"]):
        return "food"

    if any(w in msg for w in ["move", "walk", "exercise", "stretch", "sit", "sedentary"]):
        return "movement"

    if any(w in msg for w in ["sleep", "rest", "nap", "break", "pause", "tired"]):
        return "rest"

    if any(w in msg for w in ["focus", "distract", "concentrate", "deep work", "flow"]):
        return "focus"

    if any(w in msg for w in ["hello", "hi", "hey", "start", "begin", "good morning", "morning"]):
        return "greeting"

    if any(w in msg for w in ["help", "how", "what", "why", "explain"]):
        return "general_help"

    return "general"


# ── Context-aware response generator ────────────────────────────────────────

def generate_response(message: str, context: dict) -> str:
    """
    Generate an intelligent response based on the user message and their
    current energy, tasks, and wellbeing data.

    context keys:
        energy       : str  -- 'high' | 'medium' | 'low' | 'depleted' | None
        tasks        : list -- [{name, energy, done, category}, ...]
        water        : int  -- glasses drunk today
        move_min     : int  -- minutes of movement
        rest_min     : int  -- minutes of rest
        last_meal    : str  -- ISO timestamp or None
    """
    intent      = detect_intent(message)
    energy      = context.get("energy") or "medium"
    tasks       = context.get("tasks", [])
    water       = context.get("water", 0)
    move_min    = context.get("move_min", 0)

    pending_tasks   = [t for t in tasks if not t.get("done")]
    completed_tasks = [t for t in tasks if t.get("done")]

    # ── Intent-specific responses ────────────────────────────────────────────

    if intent == "greeting":
        base = random.choice(GREETINGS)
        if energy:
            base += f" Your current energy state is logged as {energy}."
        return base

    if intent == "low_energy":
        if energy in ("depleted", "low"):
            return (
                "Your body is telling you something important. At low or depleted energy, "
                "attempting high-output work creates compounding fatigue without proportional returns. "
                "The most strategic move is to rest first, then re-engage with only your lowest-energy tasks. "
                "Recovery is not wasted time — it is infrastructure."
            )
        return (
            "Feeling tired despite your logged energy level can indicate dehydration, skipped meals, "
            "or accumulated cognitive load. Drink water, step away from your screen for five minutes, "
            "and check when you last ate. Small physical resets have outsized cognitive returns."
        )

    if intent == "overwhelmed":
        task_count = len(pending_tasks)
        return (
            f"You have {task_count} pending task{'s' if task_count != 1 else ''} in your queue. "
            "When everything feels urgent, nothing actually gets done well. "
            "Identify the single task that, if completed, would reduce your mental load the most. "
            "Do only that task next. The rest can wait — the feeling of overwhelm rarely reflects reality."
        )

    if intent == "prioritise":
        if not pending_tasks:
            return (
                "Your task queue is currently empty. Add your tasks and set your energy level, "
                "and VITA will sort them by what your mind and body can actually handle right now."
            )
        # Find best energy match
        energy_rank = {"high": 3, "medium": 2, "low": 1, "depleted": 0}
        user_rank   = energy_rank.get(energy, 2)
        best = sorted(pending_tasks, key=lambda t: abs(energy_rank.get(t.get("energy","medium"), 2) - user_rank))
        top = best[0]
        return (
            f"Based on your current {energy} energy state, your best next task is '{top['name']}' "
            f"({top.get('energy','medium')} energy required). "
            "It most closely matches what you have available to give right now. "
            "Complete it fully before moving on — partial progress on many tasks is less effective than finishing one."
        )

    if intent == "hydration":
        if water < 3:
            return (
                f"You have logged {water} glass{'es' if water != 1 else ''} of water today, which is below the minimum threshold. "
                "Mild dehydration at just 1-2 percent of body weight measurably reduces attention span and working memory. "
                "Drink a full glass of water now, before continuing any task."
            )
        if water >= 8:
            return (
                "Your hydration is on track. Maintaining this through the afternoon is important — "
                "most people hydrate well in the morning and forget as the day progresses. "
                "Keep a water source visible at your workspace."
            )
        return (
            f"You are at {water} of 8 glasses. You are making progress. "
            "A useful habit is pairing water intake with regular breaks — every time you step away from your desk, drink a glass."
        )

    if intent == "food":
        return (
            "Regular food intake is one of the most underrated productivity variables. "
            "Skipping meals or eating inconsistently causes blood sugar volatility, which shows up as poor focus, "
            "irritability, and decision fatigue. Aim for a meal or substantive snack every 3-4 hours. "
            "Log your last meal in the Wellbeing section so VITA can track your patterns."
        )

    if intent == "movement":
        if move_min < 10:
            return (
                f"You have logged {move_min} minutes of movement so far. "
                "Even a 5-minute walk has been shown to improve creative thinking and reduce cortisol. "
                "Stand up now, move to a different space, and return. It takes less than five minutes and the cognitive return is immediate."
            )
        return (
            f"You have {move_min} minutes of movement logged. "
            "Sustained activity throughout the day is more valuable than a single workout block. "
            "Keep taking short movement breaks every 45-60 minutes."
        )

    if intent == "rest":
        return (
            "Rest is not the absence of productivity — it is a prerequisite for it. "
            "Your brain consolidates information, clears metabolic waste, and resets attention resources during rest periods. "
            "A 10-20 minute break taken intentionally returns more than an hour of fatigued effort. "
            "Log a rest block in the Wellbeing section to track your recovery patterns."
        )

    if intent == "focus":
        return (
            f"At {energy} energy, your optimal focus session length is approximately "
            + ("90 minutes with a 20-minute break." if energy == "high" else
               "45-60 minutes with a 10-minute break." if energy == "medium" else
               "25-30 minutes with a 10-minute break.")
            + " Remove all non-essential tabs, silence notifications, and commit to a single task before starting. "
            "Multitasking reduces output quality by up to 40 percent."
        )

    if intent == "general_help":
        return (
            "VITA helps you manage your day based on your actual energy state, not arbitrary deadlines. "
            "Set your energy level on the home screen, add your tasks with their energy requirements, "
            "and VITA will sort your queue to match what you have available. "
            "Use the Wellbeing section to track water, food, movement, and rest. "
            "Ask me anything about your tasks, priorities, or how to approach your day."
        )

    # ── Default: context-aware general response ──────────────────────────────
    if pending_tasks:
        task_names = ", ".join(t["name"] for t in pending_tasks[:3])
        return (
            f"You currently have {len(pending_tasks)} pending task{'s' if len(pending_tasks) != 1 else ''}: {task_names}{'...' if len(pending_tasks) > 3 else ''}. "
            f"With your current {energy} energy level, I recommend focusing on tasks that match your capacity rather than the ones that feel most urgent. "
            "What specifically would you like help thinking through?"
        )

    return (
        "I am here to help you plan your day around your energy, not your anxiety. "
        "Add some tasks, set your energy level, and I can help you sequence your day intelligently. "
        "Or just tell me what is on your mind."
    )


def get_wellness_tip() -> str:
    return random.choice(WELLBEING_TIPS)


def get_energy_insight(energy_level: str) -> str:
    tips = ENERGY_INSIGHTS.get(energy_level, ENERGY_INSIGHTS["medium"])
    return random.choice(tips)
