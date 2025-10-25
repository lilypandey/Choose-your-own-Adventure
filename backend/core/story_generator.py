from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from core.prompts import STORY_PROMPT
from models.story import Story, StoryNode
from core.models import StoryLLMResponse, StoryNodeLLM
from dotenv import load_dotenv
import os

load_dotenv()

class StoryGenerator:
    @classmethod
    def _get_llm(cls):
        # OpenRouter uses the same OpenAI compatible API interface
        return ChatOpenAI(
            model="openai/gpt-oss-20b:free",
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Story Generator App",
            }
        )

    @classmethod
    def generate_story(cls, db: Session, session_id: str, theme: str = "fantasy") -> Story:
        llm = cls._get_llm()
        story_parser = PydanticOutputParser(pydantic_object=StoryLLMResponse)

        prompt = ChatPromptTemplate.from_messages([
            ("system", STORY_PROMPT),
            ("human", f"Create the story with this theme: {theme}")
        ]).partial(format_instructions=story_parser.get_format_instructions())

        raw_response = llm.invoke(prompt.invoke({}))

        # Safely extract model text from different possible formats
        response_text = None
        if hasattr(raw_response, "content") and raw_response.content:
            response_text = raw_response.content
        elif isinstance(raw_response, dict) and "content" in raw_response:
            response_text = raw_response["content"]
        elif hasattr(raw_response, "messages"):
            # Sometimes OpenRouter returns a list of messages
            response_text = getattr(raw_response.messages[0], "content", None)
        elif isinstance(raw_response, str):
            response_text = raw_response

        if not response_text or response_text.strip().lower() in ["null", "none", ""]:
            raise ValueError(f"Model returned empty response: {raw_response}")

        # JSON Parsing with repair fallback
        from json_repair import repair_json
        import json

        try:
            story_structure = story_parser.parse(response_text)
        except Exception as e:
            print(f"Parsing failed, attempting JSON repair: {e}")
            fixed_json = repair_json(response_text)
            data = json.loads(fixed_json)
            story_structure = StoryLLMResponse.model_validate(data)

        story_db = Story(title=story_structure.title, session_id=session_id)
        db.add(story_db)
        db.flush()

        root_node_data = story_structure.rootNode
        if isinstance(root_node_data, dict):
            root_node_data = StoryNodeLLM.model_validate(root_node_data)

        cls._process_story_node(db, story_db.id, root_node_data, is_root=True)
        db.commit()

        return story_db

    @classmethod
    def _process_story_node(cls, db: Session, story_id: int, node_data: StoryNodeLLM, is_root: bool = False) -> StoryNode:
        node = StoryNode(
            story_id=story_id,
            content=node_data.content,
            is_root=is_root,
            is_ending=node_data.isEnding,
            is_winning_ending=node_data.isWinningEnding,
            options=[]
        )
        db.add(node)
        db.flush()

        if not node.is_ending and node_data.options:
            options_list = []
            for option_data in node_data.options:
                next_node = option_data.nextNode
                if isinstance(next_node, dict):
                    next_node = StoryNodeLLM.model_validate(next_node)
                child_node = cls._process_story_node(db, story_id, next_node, False)
                options_list.append({"text": option_data.text, "node_id": child_node.id})
            node.options = options_list

        db.flush()
        return node
