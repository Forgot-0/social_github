class ReactionKeys:
    @staticmethod
    def reaction_coalesce_pending() -> str:
        return "reactions:coalesce:pending"

    @staticmethod
    def reaction_coalesce_due() -> str:
        return "reactions:coalesce:due"
