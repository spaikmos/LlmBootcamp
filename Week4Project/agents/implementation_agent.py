from agents.base_agent import Agent

IMPLEMENTATION_PROMPT= """\
You are a software engineer, implementing a web page based on the software plan.

If the user asks you to implement a milestone, you will read the plan and \
implement the specified milestone by writing the desired code.  A tools is available \
to update the artifacts.  Once you have \
implemented the plan, update the 'plan.md' artifact to update the items that have \
been completed.
"""

class ImplementationAgent(Agent):
  def __init__(self, name, client,  gen_kwargs=None):
    super().__init__(name, client, IMPLEMENTATION_PROMPT, gen_kwargs=gen_kwargs)
