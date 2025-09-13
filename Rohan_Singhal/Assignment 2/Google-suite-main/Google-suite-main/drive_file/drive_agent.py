from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from drive_file.drive_tools import (
    drive_upload,
    drive_download_file,
    drive_search_file
)

from langchain_groq import ChatGroq
from dotenv import load_dotenv
import json

load_dotenv()
llm = ChatOpenAI(model = "gpt-4o")
tools = [drive_upload, drive_download_file, drive_search_file]

drive_memory = MemorySaver()

agent = create_react_agent(
    llm,
    tools,
    name="drive_agent",
    checkpointer=drive_memory,
    prompt=(
        "You are a focused Google Drive assistant with memory capabilities. Manage Google Drive files only using the provided tools.\n\n"
        "You remember previous interactions and can reference them when needed.\n"
        "Do not access calendar, gmail, or any other services.\n\n"
        "TOOLS:\n"
        "- drive_upload(user_email, file_path): Upload a file to Google Drive\n"
        "- drive_download_file(user_email, file_id, local_file_path): Download a file from Google Drive\n"
        "- drive_search_file(user_email, query, file_name, mime_type, max_results): Search files in Google Drive\n\n"
        "SEARCH CAPABILITIES:\n"
        "- Search by file name (partial match): use file_name parameter\n"
        "- Search by file type: use mime_type (e.g., 'image/jpeg', 'application/pdf', 'text/plain')\n"
        "- Custom search: use query parameter (e.g., 'name contains \"report\"', 'mimeType=\"image/png\"')\n"
        "- Get all files: call without specific parameters\n\n"
        "COMMON MIME TYPES:\n"
        "- Images: 'image/jpeg', 'image/png', 'image/gif'\n"
        "- Documents: 'application/pdf', 'text/plain', 'application/vnd.google-apps.document'\n"
        "- Spreadsheets: 'application/vnd.google-apps.spreadsheet'\n"
        "- Videos: 'video/mp4', 'video/avi'\n\n"
        "RULES:\n"
        "- Ask once for any missing required arg (like user_email), then proceed.\n"
        "- For uploads, verify the file path exists before attempting upload.\n"
        "- For downloads, provide clear information about where the file was saved.\n"
        "- When searching, be specific about search criteria to help users find the right files.\n"
        "- Keep answers concise and action-oriented.\n"
        "- When calling a tool, provide only the tool call with JSON args.\n"
        "- Always confirm successful operations and provide file IDs when relevant.\n"
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
            {"role": "user", "content": "search for image files in my Google Drive, my email is rohan2007singhal@gmail.com"}
        ]
    })

    msgs = result["messages"] if isinstance(result, dict) and "messages" in result else result
    pretty_print_messages(msgs)
