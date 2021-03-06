from __future__ import print_function
from collections import defaultdict, deque

import chess
import random
import numpy as np
import time

from Reinforcement_Learning.Monte_Carlo_Search_Tree.self_play import start
from Reinforcement_Learning.Monte_Carlo_Search_Tree.MCTS_main import agent_MCTS
from Reinforcement_Learning.Monte_Carlo_Search_Tree.deep_structure import Neural_Network

class Train_Network():

    def __init__(self):
        self.board = chess.Board()
        self.play = start(self.board)

        # Hyperparameters
        self.learning_rate = 2e-3
        self.multiplier = 1.0
        self.temperature = 1.0
        self.playout = 400
        self.Cpuct_value = 5

        self.batch_size = 256
        self.batch_number = 1500
        self.play_batch_size = 1
        self.buffer = deque(maxlen=10000)

        self.epochs = 5
        self.goal = 0.02
        self.check = 2
        self.win = 0.0
        self.mcts_play = 1000

        ''' Change to FALSE if you want to start training from scratch '''
        if True:
            self.Neural_Net = Neural_Network()
            self.Neural_Net.load_network("current_policy.model")
        else:
            # start training from a new policy-value net
            self.Neural_Net = Neural_Network()

        self.agent = agent_MCTS(self.Neural_Net.state_score, training=1)

    def data_storing(self):
        '''
        The goal of this function is to loop, and collect the data
        from the matches of self-play
        '''
        
        for i in range(self.batch_size):
            
            winner, data = self.play.start_self_play(self.agent, temperature=self.temperature)
            data = list(data)
            self.episode_len = len(data)
            self.buffer.extend(data)
            #print(f"Game {i} completed in {time.time()-time_start}")
            #print(f"Data buffer length:{len(self.buffer)}")

    def update(self):
        '''
        The job of this function is to update the Neural Network, in order for it to
        learn and get better over time
        '''
        small_batch = random.sample(self.buffer, self.batch_size-1)
        states = [data[0] for data in small_batch]
        probabilities = [data[1] for data in small_batch]
        winner_batch = [data[2] for data in small_batch]
        old_probabilities, old_values = self.Neural_Net.move_probabilities(states)

        for i in range(self.epochs):
            loss, entropy = self.Neural_Net.train_network(states, probabilities, winner_batch, self.learning_rate*self.multiplier)
            new_probabilities, new_values = self.Neural_Net.move_probabilities(states)
            l = np.mean(np.sum(old_probabilities * ( np.log(old_probabilities + 1e-10) - np.log(new_probabilities + 1e-10)), axis=1) )

            if l > self.goal * 4:
                break

        if l > self.goal * 2 and self.multiplier > 0.1:
            self.multiplier /= 1.5

        elif l < self.goal / 2 and self.multiplier < 10:
            self.multiplier *= 1.5
        self.buffer.clear()
        return loss, entropy

    def policy_evaluate(self):
        '''
        The job of this function is to Evaluate the current Neural Network, and
        test to see if it is 55% better than the current best Neural Network.

        This is done in AlphaZero.
        '''
        current_network = Neural_Network()
        current_network.load_network("current_policy.model")
        best_current = Neural_Network()
        best_current.load_network("best_policy.model")

        current_agent = agent_MCTS(current_network.state_score)
        best_agent = agent_MCTS(best_current.state_score)

        dic_win = defaultdict(int)
        n_runs = 10
        for i in range(n_runs):
            winner, data= self.play.start_play(current_agent, best_agent, start_player=i % 2) 
            dic_win[winner] += 1
        print(dic_win)
        return ((dic_win["p1"] )/n_runs)


    def run(self):
        '''
        The job of this function is to bring everything together and be the 'meeting grounds'
        for all of the other functions and run them simultaneously, training the model
        '''
        print("IN GAME STATE > RUN")
        for i in range(self.batch_number):
            time_start = time.time()
            print(f"Batch Number: {i}")

            self.data_storing() #run 512 self games 

            loss, entropy = self.update()

            self.Neural_Net.save_network('Reinforcement_Learning/current_policy.model')

            print("Saved model, line 116")

            if (i+1) % self.check == 0:
                win_ratio = self.policy_evaluate()
                print(f"The Win ratio is : {win_ratio}")
                if(win_ratio>= 0.55):
                    self.Neural_Net.save_network('Reinforcement_Learning/best_policy.model')
                    print("Saved model, line 124")
                    print("IMPROVEMENT!!!!!!!!!!!!")
                else:
                    print("YOU SUCK BALLSSSSSSSSSSSSSSSSSSSSS")

                # if win_ratio > self.win:
                #     self.win = win_ratio

                #     if (self.win == 1.0 and self.mcts_play < 5000):
                #         self.mcts_play += 1000
            
                #         self.win = 0.0
            print(f"Batch {i} completed in {time.time()-time_start}")

if __name__ == '__main__':
    training_pipeline = Train_Network()
    training_pipeline.run()
