# Import Bot base class from player.
from player import Bot

import random
import operator


class TeamSelection:
    def __init__(self, turn, trie, leader, team):
        self.turn = turn
        self.trie = trie
        self.leader = leader
        self.team = team


class Votes:
    def __init__(self, leader, team, votes):
        self.leader = leader
        self.team = team
        self.votes = votes


class Mission:
    def __init__(self, leader, team, sabotaged):
        self.leader = leader
        self.team = team
        self.sabotaged = sabotaged


class TestBot(Bot):
    ######################################
    # Game methods                       #
    ######################################
    def select(self, players, count):
        # never select self in early rounds only when need is to ensure win or loss.
        # if resistance select players that are least likely to be spies
        # if spy check if turn requires spy, select those least suspicious.
        team = []
        if self.game.wins > 1 or self.game.losses > 1:
            team = [self]

        sorted_suspicion_list = sorted(self.suspicion.items(), key=operator.itemgetter(1))

        def mapindex(x): return x[0]

        mapped = list(map(mapindex, sorted_suspicion_list))

        team += [player for player in players if player.index in mapped]

        team = team[:count-len(team)]

        # take into consideration previous selected teams

        return team

    def vote(self, team):
        # if resistance check team corresponding to suspicion
        # if spy check there are enough turns left in order to win, if not ensure at least 1 spy is in the team
        # if self is in team

        vote = True

        if self.game.tries < 5 and (self.game.turn > 1 or self.game.turn < 5):
            if len(team) == 3 and self not in team:
                vote = False
            else:
                team_suspicion = 0
                other_team_members = [player for player in team if player.index != self.index]
                for player in other_team_members:
                    team_suspicion += self.suspicion[player.index]

                vote = team_suspicion/(self.average_suspicion*len(other_team_members)) <= 1

        # try to get self into team

        #self.log.debug("%s:%s => voting %s", self.game.turn, self.game.tries, vote)

        return (self.spy and self.game.tries == 5) or vote

    def sabotage(self):
        sabotage = False

        # prevent loss or make sure to win the game
        if self.game.wins > 1 or self.game.losses > 1:
            sabotage = True

        # avoid suspicion when 2 plays in a team when win is not crucial
        if len(self.game.team) == 2 and self.game.wins == 0:
            sabotage = False

        # check for other spies in team
        # see if they acted suspiciously and avoid suspicious
        # keep statics of rounds where multiple spies were and see how the other spy voted historically in past plays

        self.sabotaged = sabotage

        return sabotage

    ######################################
    # Base game event listeners          #
    ######################################
    def onGameRevealed(self, players, spies):
        #self.log.debug("---- starting game ----")

        self.other_players = [player for player in players if player.index != self.index]
        self.sabotaged = False

        # remember the selected teams
        self.teamSelection = []
        self.votes = []
        self.missions = []

        self.average_suspicion = 2 / len(self.other_players)
        self.suspicion = dict([])

        for player in self.other_players:
            self.suspicion[player.index] = 0 # self.average_suspicion

        super().onGameRevealed(players, spies)

    def onMissionAttempt(self, mission, tries, leader):
        #self.log.debug("----- attempting mission -----")
        super().onMissionAttempt(mission, tries, leader)

    def onTeamSelected(self, leader, team):
        #self.log.debug("## Team Selected: %s", team)
        # log which leader selected which team member
        self.teamSelection.append(TeamSelection(self.game.turn, self.game.tries, leader, team))

    def onVoteComplete(self, votes):
        #self.log.debug("## Votes: %s" % votes)
        # log how each bot voted
        self.votes.append(Votes(self.game.leader, self.game.team, votes))

    def onMissionFailed(self, leader, team):
        #self.log.debug("## Mission Failed: %s, %s", leader, team)
        super().onMissionFailed(leader, team)

    def onMissionComplete(self, sabotaged):
        #self.log.debug("## Mission complete: %s spy", sabotaged)
        if self.sabotaged:
            sabotaged -= 1

        # check how many sabotaged and assign spy probability to each team member
        if sabotaged > 0:
            other_team_members = [player for player in self.game.team if player.index != self.index]
            suspicion = sabotaged / len(other_team_members)
            for player in other_team_members:
                if suspicion > self.suspicion[player.index]:
                    self.suspicion[player.index] = suspicion
                # self.log.debug(
                #     "Suspicion level raised for player %(player)s to %(suspicion)s" %
                #    dict(player=player.name, suspicion=self.suspicion[player.index])
                #)

            self.average_suspicion = 0
            for value in self.suspicion.values():
                self.average_suspicion += value
            self.average_suspicion /= len(self.game.players)

        # log mission status
        self.missions.append(Mission(self.game.leader, self.game.team, sabotaged))

    def onGameComplete(self, win, spies):

        self.log.debug("## Game complete: %s, %s, %s", win, spies, self.suspicion)
        # check if spies made teams with themselves or voted only for teams as such

        # catalog spies for multi spy behaviour situations

        # compare suspicion levels to benchmark algorithm

        super().onGameComplete(win, spies)

    ######################################
    # Communication event listeners      #
    ######################################
    def onAnnouncement(self, source, announcement):
        super().onAnnouncement(source, announcement)

    def onMessage(self, source, message):
        super().onMessage(source, message)
