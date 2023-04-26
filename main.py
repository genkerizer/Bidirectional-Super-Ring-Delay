# Author: Nguyen Y Hop
import os
import sys
import yaml
import math
import time
import numpy as np
import matplotlib.pyplot as plt

class BidirectionalSuperRing:

    def __init__(self, config):
        if isinstance(config, str):
            config = yaml.load(open(config))
        self.config = config

        self.params_config = config['Params']
        self.global_config = config['Global']

        self.n = self.params_config['num_node']
        self.init = self.params_config['init_values']

        self.time_step = self.params_config['time_step']

        assert len(self.init) == self.n

        self.b_forward = self.params_config['b_forward']
        self.b_backward = self.params_config['b_backward']

        assert len(self.b_forward) == self.n
        assert len(self.b_backward) == self.n

        self.r_signal = self.params_config['r_signal']

        self.T1_delay = self.params_config['T1_delay']
        self.T2_delay = self.params_config['T2_delay']

        self.delayed = True

        if self.T1_delay is None or self.T2_delay is None:
            self.delayed = False

        if self.delayed:
            assert len(self.T1_delay) == self.n
            assert len(self.T2_delay) ==  self.n
            # Normalize to integer to easly process delay time
            self.T1_delay = np.array(self.params_config['T1_delay']) // self.time_step
            self.T2_delay = np.array(self.params_config['T2_delay']) // self.time_step
            self.T1_delay = self.T1_delay.astype(np.int32)
            self.T2_delay = self.T2_delay.astype(np.int32)
            
            

        self.save_visual_dir = self.global_config['output_dir']
        os.makedirs(self.save_visual_dir, exist_ok=True)
        


    def forward_no_delays(self, delta_t, init_value):
        
        for i in range(self.n):
            self_value = -self.r_signal * self.init[i]
            
            if i == 0:
                neighbor_value = self.b_backward[-1] * math.tanh(init_value[i+1]) + \
                               self.b_forward[-1] * math.tanh(init_value[-1])
            elif i < self.n - 1:
                neighbor_value = self.b_backward[self.n-i-1] * math.tanh(init_value[i+1]) + \
                               self.b_forward[i-1] * math.tanh(init_value[i-1])
            else:

                neighbor_value = self.b_backward[0] * math.tanh(init_value[0]) + \
                               self.b_forward[-2] * math.tanh(init_value[-2])

            self.init[i] += delta_t  * (self_value + neighbor_value)


    def forward_with_delays(self, delta_t, save_matrix, t):
        
        for i in range(self.n):
            self_value = -self.r_signal * self.init[i]
            
            if i == 0:
                neighbor_value = self.b_backward[-1] * math.tanh(save_matrix[max(t-self.T1_delay[-1], 0)][i+1]) + \
                               self.b_forward[-1] * math.tanh(save_matrix[max(t-self.T2_delay[-1], 0)][-1])
            elif i < self.n - 1:
                neighbor_value = self.b_backward[self.n-i-1] * math.tanh(save_matrix[max(t-self.T1_delay[-i], 0)][i+1]) + \
                               self.b_forward[i-1] * math.tanh(save_matrix[max(t-self.T2_delay[-i], 0)][i-1])
            else:

                neighbor_value = self.b_backward[0] * math.tanh(save_matrix[max(t-self.T1_delay[0], 0)][0]) + \
                               self.b_forward[-2] * math.tanh(save_matrix[max(t-self.T2_delay[0], 0)][-2])

            self.init[i] += delta_t  * (self_value + neighbor_value)

    
    def visualize(self, matrix_result, timestep):
        for i in range(0, self.n):
            if i not in [0, 1, 2, 6]:
                continue
            value = matrix_result[i]
            plt.plot(timestep.tolist(), value.tolist(), label=f"$x{i+1}$")
        plt.legend()
        plt.xlabel("t")
        plt.ylabel("$x_{i}$")
        plt.savefig(os.path.join(self.save_visual_dir, f"{time.time()}.jpg"))


    def cal_time(self, t=100):
        timestep_list = np.arange(0, t, self.time_step)

        save_matrix = np.zeros((timestep_list.shape[0], self.n))
        save_matrix[0, :] = self.init

        if self.delayed:
            for i, t in enumerate(np.diff(timestep_list)):
                init_value = self.init.copy()
                self.forward_with_delays(t, save_matrix, i)
                save_matrix[i, :] = self.init.copy()
        else:
            for i, t in enumerate(np.diff(timestep_list)):
                init_value = self.init.copy()
                self.forward_no_delays(t, init_value)
                save_matrix[i, :] = self.init.copy()

        
        
        save_matrix = np.transpose(save_matrix)

        
        self.visualize(save_matrix, timestep_list)
        

        return None


if __name__ == '__main__':
    config_path = sys.argv[1]
    assert os.path.exists(config_path), "config path does not exist"
    net = BidirectionalSuperRing(config_path)
    net.cal_time(200.0)