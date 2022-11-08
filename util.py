import main

class Bet:
    def __init__(self, amount, state, user):
        # information we need for casting a bet
        self.amount = amount
        self.state = state
        self.user = user

        # increase the pot's value by the amount you bet
        main.pot += self.amount

        # how much you win from the pot if you win
        self.win_percent = main.pot/self.amount

    def update(self, amount):
        self.amount += amount
        main.pot += amount
