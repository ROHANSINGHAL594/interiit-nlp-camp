

import json
from langgraph_supervisor import create_supervisor
from langchain.chat_models import init_chat_model
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from gmail_file.gmail_agent import agent as gmail_agent
from calender.calender_agent import agent as calendar_agent
from drive_file.drive_agent import agent as drive_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
import uuid
load_dotenv()

memory = MemorySaver()

supervisor = create_supervisor(
    model=ChatOpenAI(model = "gpt-4o"),
    agents=[gmail_agent, calendar_agent, drive_agent],
    prompt=(
        "You are a supervisor managing three agents:\n"
        "- a calendar agent, which helps user create, delete and list the events\n"
        "- a gmail agent , which help send a mail , list the mail and delete a mail \n"
        "- a drive agent, which helps user upload, delete and list the files\n"
        "You have memory of previous conversations and can refer back to them.\n"
        "When a user asks about something from earlier in the conversation, use that context.\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself."
    ),
    add_handoff_back_messages=True,
    output_mode="full_history",
).compile(name="supervisor_agent", checkpointer=memory)
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
###### BELOW CODE IS AI GENERATED IF ERROR FOUND FIX YOURSELF
    def run_demo():
 
        thread_id = str(uuid.uuid4())
        
        print(f"🧠 Starting conversation with memory (Thread ID: {thread_id})")
        print("💡 The agent will remember our conversation history!")
        
        # Configuration for the conversation thread
        config = {"configurable": {"thread_id": thread_id}}
        
        # Example of a multi-turn conversation that demonstrates memory
        conversations = [
            "search for ftf_assignment6 file if available download it and then send a mail to vivekc24@iitk.ac.in that i love him from top to bottom and i want to meet him tomorrow 1 pm in front of ccd , then schedule a meeting with vivek on september 1, 4 pm ,2025,   pritotize sending email first then calender then image download my mail is rohan2007singhal@gmail.com",
            "What was the email address I just mentioned?",
            "Can you remind me what meeting I scheduled?"
        ]
        
        for i, user_input in enumerate(conversations, 1):
            print(f"\n{'='*50}")
            print(f"CONVERSATION TURN {i}")
            print(f"{'='*50}")
            print(f"User: {user_input}")
            print()
            
            result = supervisor.invoke({
                "messages": [
                    {"role": "user", "content": user_input}
                ]
            }, config=config)

            msgs = result["messages"] if isinstance(result, dict) and "messages" in result else result
            pretty_print_messages(msgs)
            
            # Small pause between conversations for readability
            if i < len(conversations):
                print("(Conversation continues with memory...)\n")
        
        print("\n🎯 Memory Demo Complete!")
        print("The agent remembered information from previous messages in the conversation.")

    def interactive_chat():
        """Run interactive CLI chat with the supervisor agent"""
        # Generate a unique thread ID for this chat session
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        print("🤖 Welcome to the Interactive Supervisor Agent!")
        print("=" * 50)
        print("💬 You can chat with me about Gmail, Calendar, and Drive tasks")
        print("🧠 I have memory and will remember our conversation")
        print("🔄 Type 'exit', 'quit', or 'bye' to end the chat")
        print("📋 Type 'help' for available commands")
        print(f"🆔 Session ID: {thread_id[:8]}...")
        print("=" * 50)
        
        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
                    print("\n👋 Goodbye! Thanks for chatting!")
                    break
                
                # Handle help command
                if user_input.lower() in ['help', 'h']:
                    print("\n📋 Available Commands:")
                    print("🔹 Gmail: Send emails, list emails, create drafts, search emails")
                    print("🔹 Calendar: Create events, list events, search events, delete events")
                    print("🔹 Drive: Upload files, download files, search files")
                    print("🔹 Memory: I remember our conversation history")
                    print("🔹 Examples:")
                    print("   • 'Send an email to john@example.com about meeting tomorrow'")
                    print("   • 'Schedule a meeting with Sarah on Monday at 2 PM'")
                    print("   • 'Search for presentation files in my drive'")
                    print("   • 'What was the last email I sent?'")
                    continue
                
                # Skip empty inputs
                if not user_input:
                    print("⚠️ Please enter a message or type 'help' for commands.")
                    continue
                
                print("\n🤔 Processing your request...")
                
                # Send message to supervisor agent
                result = supervisor.invoke({
                    "messages": [
                        {"role": "user", "content": user_input}
                    ]
                }, config=config)
                
                # Extract and display the response
                msgs = result["messages"] if isinstance(result, dict) and "messages" in result else result
                
                # Find the last assistant message
                last_assistant_msg = None
                for msg in reversed(msgs):
                    mtype = getattr(msg, "type", None) or msg.__class__.__name__.lower()
                    if mtype == "ai":
                        last_assistant_msg = msg.content
                        break
                
                if last_assistant_msg:
                    print(f"\n🤖 Assistant: {last_assistant_msg}")
                else:
                    print("\n🤖 Assistant: Task completed!")
                
                # Optional: Show full transcript on demand
                show_full = input("\n📋 Show full transcript? (y/N): ").strip().lower()
                if show_full in ['y', 'yes']:
                    pretty_print_messages(msgs)
                
            except KeyboardInterrupt:
                print("\n\n⚠️ Chat interrupted. Type 'exit' to quit properly.")
                continue
            except Exception as e:
                print(f"\n❌ An error occurred: {e}")
                print("Please try again or type 'exit' to quit.")
                continue

    # Main menu for choosing between demo and interactive chat
    print("🚀 Supervisor Agent - Choose Mode")
    print("=" * 40)
    print("1. 🎭 Run Demo (Predefined conversations)")
    print("2. 💬 Interactive Chat (CLI)")
    print("3. 🚪 Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                run_demo()
                break
            elif choice == "2":
                interactive_chat()
                break
            elif choice == "3":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break