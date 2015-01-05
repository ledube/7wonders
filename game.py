#!/usr/bin/python
#
# Copyright 2015 - Jonathan Gordon
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This software is distributed on an "AS IS" basis, WITHOUT WARRANTY OF ANY
# KIND, either express or implied.

import random

from common import *
from cards import helpers
from players import *

def init_games():
	global __all_cards
	global __all_wonders

	__all_cards = helpers.read_cards_file("card-descriptions.txt")
	__all_wonders = Wonders.read_wonders_file("wonders.txt")

class GameState:
	def __init__(self, player_count):
		self.player_count = player_count
		self.players = []
		self.ages = []
		self.decks = [[]] * player_count
		self.discard_pile = []
		for i in range(player_count):
			self.players.append(Players.Player("player %d" % (i + 1)))
		
	def setup_age_cards(self, cards):
		age_1 = [c for c in cards if c.age == 1 and c.players <= self.player_count]
		age_2 = [c for c in cards if c.age == 2 and c.players <= self.player_count]
		age_3 = [c for c in cards if c.age == 3 and c.get_colour() != CARDS_PURPLE and c.players <= self.player_count]
		purple = [c for c in cards if c.age == 3 and c.get_colour() == CARDS_PURPLE and c.players <= self.player_count]

		random.shuffle(age_1)
		random.shuffle(age_2)
		random.shuffle(purple)
		age_3 += purple[0 : self.player_count + 2]
		random.shuffle(age_3)
		
		self.ages = [age_1, age_2, age_3]
	
	def deal_age_cards(self, age):
		cards = self.ages[age][0:]
		p = 0
		for i in range(self.player_count):
			self.decks[i] = []
		while len(cards):
			self.decks[p].append(cards[0])
			p += 1
			p %= self.player_count
			cards = cards[1:]
	
	def _get_west_player(self, playerid):
		return self.players[(playerid + self.player_count - 1) % self.player_count]

	def _get_east_player(self, playerid):
		return self.players[(playerid + 11) % self.player_count]
	
	def play_turn(self, offset):
		for i in range(self.player_count):
			player = self.players[i]
			west_player = self._get_west_player(i)
			east_player = self._get_east_player(i)
			deckid = (i + offset) % self.player_count
			player.print_tableau()
			# This loop is actually wrong.
			# Everyone should choose the card they will play, server
			# validates the move is legal, then each player plays the card
			# Then each player adds the new card to their tableau
			while True:
				action, card = player.play_hand(self.decks[deckid], west_player, east_player)
				if action == ACTION_PLAYCARD:
					can_buy = False
					# see if the player can buy the card
					if player.can_build_with_chain(card):
						can_buy = True
					else:
						can_buy = True # fixme
						#buy_options = player.buy_card(card, west_player, east_player)
						#if buy_options == None:
						#	continue
						#player.money -= buy_options[0].total_cost
						#cost = 0
						#for c in buy_options[0].east_trades:
						#	cost += player.east_trade_prices[c.get_info()[0]]
						#east_player.money += cost
						#cost = 0
						#for c in buy_options[0].east_trades:
						#	cost += player.west_trade_prices[c.get_info()[0]]
						#west_player.money += cost
					if can_buy:
						card.play(player, west_player, east_player)
						player.get_cards().append(card)
						break
				elif action == ACTION_DISCARD:
					self.discard_pile.append(card)
					player.money += 3
					break
				elif action == ACTION_STAGEWONDER:
					# make sure we can do that
					break
			self.decks[deckid].remove(card)
			
	
	def game_loop(self):
		for age in range(3):
			self.deal_age_cards(age)
			offset = 0
			while len(self.decks[0]) > 1:
				self.play_turn(offset)
				offset = (offset + 1) % self.player_count
			# everyone discards the last card
			for p in range(self.player_count):
				self.discard_pile.append(self.decks[p][0])
			
			# score military
			for p in range(self.player_count):
				west = self._get_west_player(p)
				east = self._get_east_player(p)
				player = self.players[p]
				self.players[p].military.append(helpers.score_military(west, player, age))
				self.players[p].military.append(helpers.score_military(east, player, age))
		for i in range(self.player_count):
			player = self.players[i]
			score = 0
			score += helpers.score_blue(player)
			(_,_,_,), greenscore = helpers.score_science(player)
			score += greenscore
			for military in player.military:
				score += military
			# TODO: score yellow, purple
			print "Final score: ", score
			

init_games()
game = GameState(3)
game.setup_age_cards(__all_cards)
game.game_loop()
