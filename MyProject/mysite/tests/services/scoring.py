class ScoreCalculator:
    def calculate(self, options):
        return sum(option.score for option in options)