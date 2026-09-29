import numpy as np
import random
import sys

# Attempt to import Gymnasium and Stable Baselines3 (industry standards for RL)
try:
    import gymnasium as gym
    from gymnasium import spaces
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_checker import check_env
    HAS_SB3 = True
except ImportError:
    # Fallback if libraries are still installing
    HAS_SB3 = False

if HAS_SB3:
    class MicrogridEnv(gym.Env):
        """
        Custom Environment that follows the OpenAI Gym interface.
        The RL agent learns to balance the microgrid load to strictly avoid diesel usage
        and prevent catastrophic battery depletion.
        """
        metadata = {"render_modes": ["console"]}

        def __init__(self):
            super(MicrogridEnv, self).__init__()
            
            # The Action Space: 3 discrete decisions the AI can make every hour
            # 0: Maintain all operations (Do nothing, keep science/comfort running)
            # 1: Shed Non-Essential Load (e.g., turn off heating in empty modules)
            # 2: Start Diesel Generator (Emergency power)
            self.action_space = spaces.Discrete(3)
            
            # The Observation Space: What the AI "sees" before making a decision
            # [Battery SOC (0-1), Battery Temp (-40 to 40C), Current Load (kW), Predicted Gen (kW)]
            self.observation_space = spaces.Box(
                low=np.array([0.0, -40.0, 0.0, 0.0]), 
                high=np.array([1.0, 40.0, 100.0, 300.0]), 
                dtype=np.float32
            )

        def reset(self, seed=None, options=None):
            super().reset(seed=seed)
            # Start the episode with a semi-healthy battery but high load
            self.soc = 0.8
            self.temp = -5.0
            self.load = 50.0
            self.predicted_gen = random.uniform(0.0, 100.0)
            
            self.current_step = 0
            self.max_steps = 24 # 24 hour episode
            
            observation = np.array([self.soc, self.temp, self.load, self.predicted_gen], dtype=np.float32)
            return observation, {}

        def step(self, action):
            self.current_step += 1
            
            reward = 0.0
            terminated = False
            truncated = False
            
            # Calculate Deficit/Surplus (simplified physics for the RL training environment)
            net_power = self.predicted_gen - self.load
            
            # --- REWARD SHAPING (The heart of Reinforcement Learning) ---
            if action == 0:
                # Maintained all loads
                reward += 10.0 # Positive reinforcement for keeping all science online
            elif action == 1:
                # Shed load
                net_power += (self.load * 0.20) # Save 20% power by cutting non-essentials
                reward -= 5.0  # Mild penalty for disrupting station comfort/science
                print(f"   [RL Agent] Action Taken: Shedding Non-Essential Load.")
            elif action == 2:
                # Started Diesel
                net_power += 100.0 # Diesel gives 100kW
                reward -= 50.0 # Massive penalty for burning polluting fossil fuels!
                print(f"   [RL Agent] Action Taken: Starting Diesel Generator!")
                
            # Update Battery State
            # Very crude approximation: 100kW net power adds roughly 10% SOC to a 1000kWh battery
            self.soc += (net_power * 0.001) 
            self.soc = np.clip(self.soc, 0.0, 1.0)
            
            # Check critical failure (The PLC daemon in failsafe_fallback.py would trigger here in real life)
            if self.soc < 0.20:
                reward -= 200.0 # Catastrophic failure penalty
                terminated = True
                
            if self.current_step >= self.max_steps:
                truncated = True
                
            # Randomize next hour's weather for the simulation
            self.predicted_gen = random.uniform(0.0, 100.0)
            if self.predicted_gen < 20.0 and self.temp > -20.0:
                self.temp -= 2.0 # Battery gets colder if no sun/wind is available
                
            observation = np.array([self.soc, self.temp, self.load, self.predicted_gen], dtype=np.float32)
            info = {}
            
            return observation, reward, terminated, truncated, info

if __name__ == "__main__":
    print("--- Initializing RL Load-Balancing Agent ---")
    
    if HAS_SB3:
        env = MicrogridEnv()
        # Verify the custom environment follows the strict Gym API
        check_env(env, warn=True)
        
        print("Training Proximal Policy Optimization (PPO) Agent for 1000 timesteps...")
        # In a real hackathon, you'd train for 100k+ timesteps to let it learn optimal behavior
        model = PPO("MlpPolicy", env, verbose=0)
        model.learn(total_timesteps=1000)
        
        print("\n--- Running Trained Agent Test Episode ---")
        vec_env = model.get_env()
        obs = vec_env.reset()
        
        for i in range(5):
            # The model predicts the absolute best action based on the observation
            action, _states = model.predict(obs, deterministic=True)
            obs, rewards, dones, info = vec_env.step(action)
            soc = obs[0][0]
            pred_gen = obs[0][3]
            print(f"[Hour {i+1}] SOC: {soc*100:5.1f}% | Predicted Gen: {pred_gen:5.1f}kW | AI Action: {action[0]} | Reward: {rewards[0]}")
            
    else:
        print("Waiting for stable-baselines3 and gymnasium to finish installing in the background...")
        print("You can run this script again once the installation completes to see the AI train!")
