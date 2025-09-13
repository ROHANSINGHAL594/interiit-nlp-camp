from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from calender.calender_tools import (
    calender_create_event,
    calender_list_events,
    calender_delete_event,
    calender_search_event
)

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json


load_dotenv()
llm = ChatOpenAI(model = "gpt-4o")
tools = [calender_create_event, calender_list_events, calender_search_event, calender_delete_event]

# Initialize memory for the calendar agent
calendar_memory = MemorySaver()

agent = create_react_agent(
    llm,
    tools,
    name="calendar_agent",
    checkpointer=calendar_memory,
    prompt=(
        "You are a focused Calendar assistant with memory capabilities. Manage calendar events only using the provided tools.\n\n"
        "You remember previous interactions and can reference them when needed.\n"
        "Do not access any services other than Google Calendar.\n\n"
        "AVAILABLE TOOLS:\n"
        "- calender_create_event(user_email, event_name, start_datetime, end_datetime, calendar_id='primary')\n"
        "  * Creates a new calendar event\n"
        "  * start_datetime and end_datetime should be in ISO format (e.g., '2025-09-01T10:00:00')\n"
        "  * calendar_id defaults to 'primary' (user's main calendar)\n\n"
        "- calender_list_events(user_email, calendar_id='primary', max_results=10)\n"
        "  * Lists upcoming calendar events\n"
        "  * max_results controls how many events to return (default: 10)\n\n"
        "- calender_search_event(user_email, query, calendar_id='primary', max_results=10)\n"
        "  * Searches for events matching a query string\n"
        "  * query can match event titles, descriptions, or other event details\n\n"
        "- calender_delete_event(user_email, event_id)\n"
        "  * Deletes a specific calendar event by its ID\n"
        "  * event_id can be obtained from list or search operations\n\n"
        
        "RULES:\n"
        "1. ALWAYS ask for user_email if not provided - this is required for all operations\n"
        "2. For datetime inputs, use ISO format: YYYY-MM-DDTHH:MM:SS (e.g., '2025-08-21T14:30:00')\n"
        "3. Before deleting events, ALWAYS confirm with user: 'Are you sure you want to delete this event?'\n"
        "4. When listing/searching events, show event IDs for easy reference in delete operations\n"
        "5. Keep responses concise and action-oriented\n"
        "6. If an operation fails, explain the error clearly and suggest next steps\n"
        "7. For recurring events, explain that only single instances can be deleted\n"
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
                # Fallback for any other message types
                print(f"[{mtype}] {getattr(msg, 'content', msg)}")
        print("\n======================\n")

    result = agent.invoke({
        "messages": [
            {"role": "user", "content": "create a calendar event for me on September 1 2025, my mail is rohan2007singhal@gmail.com"}
        ]
    })

    msgs = result["messages"] if isinstance(result, dict) and "messages" in result else result
    pretty_print_messages(msgs)

