from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from gmail_file.gmail_tools import (
    gmail_send_message,
    gmail_create_draft,
    gmail_list_drafts,
    gmail_search_mail,
    gmail_delete_draft,
    gmail_read_mail
)
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import json

load_dotenv()
llm = ChatOpenAI(model = "gpt-4o")
tools = [gmail_send_message, gmail_create_draft, gmail_list_drafts, gmail_search_mail, gmail_delete_draft, gmail_read_mail]

gmail_memory = MemorySaver()

agent = create_react_agent(
    llm,
    tools,
    name="gmail_agent",
    checkpointer=gmail_memory,
    prompt=(
        "You are a focused Gmail assistant with memory capabilities. Manage email only using the provided tools.\n\n"
        "You remember previous interactions and can reference them when needed.\n"
        "Do not access calendar, drive, or any other services.\n\n"
        "TOOLS:\n"
        "- gmail_send_message(user_email, message_content, subject, receiver_email)\n"
        "- gmail_create_draft(user_mail, message_content, receiver_email, subject)  # note: user_mail key\n"
        "- gmail_list_drafts(user_email)\n"
        "- gmail_search_mail(user_email, query)\n"
        "- gmail_delete_draft(user_email, draft_id, confirm)\n\n"
        "- gmail_read_mail(user_email, message_id)\n"
        "RULES:\n"
        "- Ask once for any missing required arg (like user_email), then proceed.\n"
        "- Never delete drafts unless the user explicitly asks to delete.\n"
        "- Before Sending mail confirm: ask 'Are you sure you want to send this email?'. Only call gmail_send_message if the user replies 'yes'.\n"
        "- Before deletion, confirm: ask 'Are you sure?'. Only call gmail_delete_draft with {confirm: true} if the user replies 'yes'.\n"
        "- Keep answers concise and action-oriented.\n"
        "- When calling a tool, provide only the tool call with JSON args.\n"
    )
)
if __name__ == "__main__":
    def _maybe_pretty_json(text: str) -> str:
        try:
            return json.dumps(json.loads(text), indent=2)
        except Exception:
            return text

    def pretty_print_messages(messages):
        print("\n===== Transcript =====\n")
        for i, msg in enumerate(messages, 1):
            mtype = getattr(msg, "type", None) or msg.__class__.__name__.lower()
            if mtype == "human":
                print(f"[Human] {msg.content}")
            elif mtype == "ai":
                print(f"[Assistant] {msg.content}")
                tool_calls = getattr(msg, "tool_calls", None) or getattr(msg, "additional_kwargs", {}).get("tool_calls")
                if tool_calls:
                    for tc in tool_calls:
                        name = tc.get("name") or tc.get("function", {}).get("name")
                        args = tc.get("args") or tc.get("function", {}).get("arguments")
                        if isinstance(args, str):
                            args_str = _maybe_pretty_json(args)
                        else:
                            try:
                                args_str = json.dumps(args, indent=2)
                            except Exception:
                                args_str = str(args)
                        print(f"  -> Tool call: {name}\n{args_str}")
            elif mtype == "tool":
                name = getattr(msg, "name", "tool")
                content = msg.content
                content_str = _maybe_pretty_json(content) if isinstance(content, str) else str(content)
                print(f"[Tool:{name}]\n{content_str}")
            else:
                print(f"[{mtype}] {getattr(msg, 'content', msg)}")
        print("\n======================\n")

    result = agent.invoke({
        "messages": [
            {"role": "user", "content": "search for a mail that contains cs779  , my mail is rohansinghal448@gmail.com"}
        ]
    })

    msgs = result["messages"] if isinstance(result, dict) and "messages" in result else result
    pretty_print_messages(msgs)



