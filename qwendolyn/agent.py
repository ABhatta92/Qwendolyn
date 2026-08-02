class Agent:

    def __init__(
        self,
        llm,
        registry,
    ):

        self.llm = llm
        self.registry = registry

    def run(self, prompt):

        ...