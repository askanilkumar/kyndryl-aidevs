"""LAB 1a - Memory is just a list we send again every time.

RUN:   python lab1a_list_memory.py
THEN:  (1) change MAX_KEEP from 10 to 4 and run again. Which messages does the bot forget?
       (2) run the script twice. Is anything remembered between runs? Why not?
"""
MAX_KEEP = 10          # how many messages the bot is allowed to see

history = []           # <- this Python list IS the memory


def bot_reply(messages):
    """A stand-in 'model'. It can only use what is inside `messages`."""
    text = " ".join(m["content"].lower() for m in messages if m["role"] == "user")
    last = messages[-1]["content"].lower()
    if "what is my name" in last:
        for m in reversed(messages):
            if m["role"] == "user" and "my name is" in m["content"].lower():
                return "Your name is " + m["content"].lower().split("my name is")[1].strip(" .").title()
        return "Sorry, I don't know your name."
    return f"(I can see {len(messages)} messages)"


def say(text):
    history.append({"role": "user", "content": text})
    visible = history[-MAX_KEEP:]                    # the window: only the last N go to the model
    reply = bot_reply(visible)
    history.append({"role": "assistant", "content": reply})
    print(f"you: {text}\nbot: {reply}\n")


say("Hi, my name is Anil")
say("What is my name?")
for i in range(6):
    say(f"Tell me about plan number {i}")
say("What is my name?")            # still remembered? depends on MAX_KEEP

print(f"The list now holds {len(history)} messages. It lives only in this process.")
history.clear()                    # <- this is what a restart does
say("What is my name?")

from agentlib.habits import footer   # noqa: E402
footer()
