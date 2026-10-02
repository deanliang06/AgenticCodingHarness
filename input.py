from tkinter import *
from Agent import Agent

def send_message(message: str):
    """
    Called when the user submits a message.

    Replace this with your harness logic:
        harness.send(message)
    """
    agent.on_user_msg(message)
    add_agent_message(agent.last_output.msg)


def on_message_submit():
    """
    Reads the current text box, clears it,
    displays the message, then calls send_message().
    """
    message = get_current_message()

    if not message.strip():
        return

    # Show user message in conversation area
    conversation.config(state=NORMAL)
    conversation.insert(END, f"You:\n{message}\n\n")
    conversation.config(state=DISABLED)
    conversation.see(END)

    # Clear input
    clear_message_box()

    # Pass message to your harness
    send_message(message)


def get_current_message() -> str:
    """
    Returns the current contents of the input box.
    """
    return message_box.get("1.0", END).rstrip("\n")


def clear_message_box():
    """
    Clears the user's input box.
    """
    message_box.delete("1.0", END)


def set_status(text: str):
    """
    Lets your harness update the status indicator.

    Example:
        set_status("Running command...")
        set_status("Waiting for input")
    """
    status_label.config(text=text)


def add_agent_message(message: str):
    """
    Call this when your harness/model produces a response.
    """
    conversation.config(state=NORMAL)
    conversation.insert(END, f"Agent:\n{message}\n\n")
    conversation.config(state=DISABLED)
    conversation.see(END)


def handle_ctrl_enter(event):
    """
    Ctrl+Enter submits the message.
    Normal Enter still creates a newline.
    """
    on_message_submit()
    return "break"


# =========================
# GUI
# =========================

if __name__ == "__main__":
    agent = Agent()
    root = Tk()
    root.title("Harness Gadget")
    root.geometry("760x650")
    root.minsize(600, 500)

    root.configure(bg="#181818")

    # ---------- Header ----------
    header = Frame(root, bg="#202020", height=55)
    header.pack(fill=X)

    title_label = Label(
        header,
        text="Harness Gadget",
        font=("Segoe UI", 16, "bold"),
        fg="white",
        bg="#202020"
    )
    title_label.pack(side=LEFT, padx=20, pady=15)

    status_label = Label(
        header,
        text="Ready",
        font=("Segoe UI", 10),
        fg="#a0a0a0",
        bg="#202020"
    )
    status_label.pack(side=RIGHT, padx=20)

    # ---------- Conversation ----------
    conversation_frame = Frame(root, bg="#181818")
    conversation_frame.pack(fill=BOTH, expand=True, padx=18, pady=(18, 10))

    conversation = Text(
        conversation_frame,
        wrap=WORD,
        font=("Segoe UI", 11),
        bg="#202020",
        fg="#f0f0f0",
        insertbackground="white",
        relief=FLAT,
        padx=15,
        pady=15,
        state=DISABLED
    )

    scrollbar = Scrollbar(
        conversation_frame,
        command=conversation.yview
    )

    conversation.configure(yscrollcommand=scrollbar.set)

    conversation.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.pack(side=RIGHT, fill=Y)

    # ---------- Input area ----------
    input_frame = Frame(root, bg="#181818")
    input_frame.pack(fill=X, padx=18, pady=(0, 18))

    message_box = Text(
        input_frame,
        height=5,
        wrap=WORD,
        font=("Segoe UI", 11),
        bg="#2a2a2a",
        fg="white",
        insertbackground="white",
        relief=FLAT,
        padx=12,
        pady=10
    )

    message_box.pack(
        side=LEFT,
        fill=BOTH,
        expand=True
    )

    message_box.bind("<Control-Return>", handle_ctrl_enter)

    send_button = Button(
        input_frame,
        text="Send",
        command=on_message_submit,
        font=("Segoe UI", 10, "bold"),
        width=10,
        bg="#4a7cff",
        fg="white",
        activebackground="#638fff",
        activeforeground="white",
        relief=FLAT,
        cursor="hand2"
    )

    send_button.pack(
        side=RIGHT,
        padx=(10, 0),
        fill=Y
    )

    # Put keyboard focus directly in input box
    message_box.focus_set()

    root.mainloop()