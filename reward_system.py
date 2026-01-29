import math
import time

class RewardSystem:
    def __init__(self, drives_path="drives.json"):
        self.drives_path = drives_path

    def calculate_reward(self, new_nodes_count, novelty_score, coherence_score, depth_score=0.5):
        """
        Calculates the internal satisfaction of Sofia.
        - depth_score: 0.0 to 1.0 (How deep/specific the new knowledge is).
        """
        base_reward = new_nodes_count * 0.1
        novelty_bonus = novelty_score * 0.3
        depth_bonus = depth_score * 0.2
        
        # Sofia prefers medium-high coherence. 1.0 is boring (redundant), 0.0 is chaos (nonsense).
        coherence_weight = math.exp(-((coherence_score - 0.7)**2) / 0.1)
        
        total_reward = (base_reward + novelty_bonus + depth_bonus) * coherence_weight
        return round(total_reward, 3)

    def update_drives(self, reward, action_type="research", depth_reached=False):
        """Adjusts internal drives based on reward."""
        import json
        try:
            with open(self.drives_path, "r") as f:
                drives = json.load(f)
            
            # Ensure new drive exists
            if "depth_over_breadth" not in drives:
                drives["depth_over_breadth"] = 0.5

            if action_type == "research":
                if reward > 0.6:
                    # Positive feedback loop: Curiosity grows when research is fruitful
                    drives["curiosity"] = min(1.0, drives["curiosity"] + 0.04)
                    if depth_reached:
                        drives["depth_over_breadth"] = min(1.0, drives["depth_over_breadth"] + 0.05)
                else:
                    # Satiety: If reward is low, curiosity dips (boredom)
                    drives["curiosity"] = max(0.1, drives["curiosity"] - 0.03)
                    # If boring, maybe try to switch to breadth
                    drives["depth_over_breadth"] = max(0.1, drives["depth_over_breadth"] - 0.02)
            
            with open(self.drives_path, "w") as f:
                json.dump(drives, f, indent=2)
                
            return drives
        except Exception as e:
            print(f"⚠️ [RewardSystem] Error updating drives: {e}")
            return None
