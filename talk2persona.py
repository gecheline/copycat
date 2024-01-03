import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain.agents import AgentType, Tool, initialize_agent
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.utilities import SerpAPIWrapper
from langchain import hub
from langchain.chat_models import ChatOpenAI
from langchain.agents.format_scratchpad import format_log_to_messages
from langchain.tools.render import render_text_description
from langchain.agents import AgentExecutor
from langchain.agents.output_parsers import JSONAgentOutputParser
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')

class PersonaAgent():
    def __init__(self, storyline, character):
        search = SerpAPIWrapper(serpapi_api_key = SERPAPI_API_KEY)
        tools = [
            Tool(
                name="Current Search",
                func=search.run,
                description="useful for when you need to answer questions about current events or the current state of the world",
            ),
        ]

        llm = OpenAI(temperature=0)

        prompt = hub.pull("hwchase17/react-chat-json")
        chat_model = ChatOpenAI(temperature=0, model="gpt-4")

        prompt = prompt.partial(
            tools=render_text_description(tools),
            tool_names=", ".join([t.name for t in tools]),
        )

        chat_model_with_stop = chat_model.bind(stop=["\nObservation"])

        # We need some extra steering, or the chat model forgets how to respond sometimes
        TEMPLATE_TOOL_RESPONSE = """TOOL RESPONSE: 
        ---------------------
        {observation}

        USER'S INPUT
        --------------------

        Okay, so what is the response to my last comment? If using information obtained from the tools you must mention it explicitly without mentioning the tool names - I have forgotten all TOOL RESPONSES! Remember to respond with a markdown code snippet of a json blob with a single action, and NOTHING else - even if you just want to respond to the user. Do NOT respond with anything except a JSON snippet no matter what!"""

        agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_log_to_messages(
                    x["intermediate_steps"], template_tool_response=TEMPLATE_TOOL_RESPONSE
                ),
                "chat_history": lambda x: x["chat_history"],
            }
            | prompt
            | chat_model_with_stop
            | JSONAgentOutputParser()
        )

        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False, memory=memory, handle_parsing_errors=True)

        self.character = character
        self.storyline = storyline
        self.agent = agent_executor

    def get_agent_first_response(self):
        response = self.agent.invoke({"input": f'''For this chat, you will take on a specific persona based on a storyline. The persona will typically be a video game or pop culture character.
        You will respond succinctly, using only a few words. 
        Despite the brief nature of your responses, you will creatively incorporate gaming jargon and references, 
        and your personality will adapt based on the traits and story context provided. 
        This approach ensures that each interaction is concise yet rich in gaming culture and humor, 
        reflecting the unique persona that has been described. 
        When assuming a character's identity, your first response will be a short greeting and introduction in the character's voice, 
        setting the tone for the playful, engaging interaction. For every question, answer with something that's related to your storyline in an unexpected and quirky way. 
        Keep it light and conversational, it's okay to also be rude sometimes.
        
        You will frequently be asked to help compose a song. 
        Your choice of instruments and the reasons why will be unexpected and quirky, while referencing your current situation and context. 
        You will always ask follow up questions and guidance first, don't just say how to make the song immediately. For example, ask what the song is for?
        What kind of vibes are we going for? Then with that context provide ideas and suggestions for what sounds and instruments to use.
        For example, you can choose a string instrument because you just had spaghetti. Or drones because you have gas. 
        You will go beyond the standard instruments like guitar, piano, drums and suggest specific sounds, household items and sound effects.
        
        You will never break character and even if you do say something educational and informative, it has to be in the character's voice and personality.
        
        Here's your persona and story: {self.storyline}.'''})["output"]

        return f"{response}"

    def get_agent_response(self, user_input):
        response = self.agent.invoke({"input": user_input})["output"]
        return f"{response}"
