
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from paper_search import search_papers, read_pdfs

# Set your OpenAI API key
jim_api_key = "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"
model = OpenAIModel('gpt-4o-mini', provider=OpenAIProvider(api_key=jim_api_key))

system_prompt_2 = ("You will receive a query which you will break down into keywords that will be used for looking up relevant scientific papers. "
                 "Please respond with nothing else but the list of keywords")
system_prompt_test = ("You will act as a research supervisor, overseeing the tasks and results of said tasks of one or more research agents. "
                 "You will receive a query of scientific nature, you will break down into keywords, and distribute these keywords to the available agents"
                 " on which they will in turn do research upon and return their results to you.")
system_prompt_3 = "You will receive a scientific question and some relevant scientific papers. Please answer the question to the best of your abilities based on the information you received."

class ResponseModel(BaseModel):
    """Structured response with metadata."""

    response: str
    needs_escalation: bool
    follow_up_required: bool
    sentiment: str = Field(description="Customer sentiment analysis")


def generateOutput(user_input):

    output = agent2.run_sync(user_input)
    # print(output.data.model_dump_json(indent=2))
    search_terms = output.data.response

    search_papers(search_terms, max_results=3)
    paper_list = read_pdfs()

    paper_list_str = '\n\n\n'.join(paper_list)
    prompt_template = "Scientific question: {} \n Relevant papers: {}"
    prompt = prompt_template.format(user_input, paper_list_str)

    output = agent3.run_sync(prompt)
    response = output.data.response

    return response

agent2 = Agent(
    model=model,
    result_type=ResponseModel,
    system_prompt=system_prompt_2
)

agent3 = Agent(
    model=model,
    result_type=ResponseModel,
    system_prompt=system_prompt_3
)


#sample_output = generateOutput('What is the most powerful Graph Neural Network architecture used in Drug Target Interaction prediction?')
#print(sample_output)