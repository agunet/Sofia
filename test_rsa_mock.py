import unittest
from unittest.mock import MagicMock
from agents import AgentReasoning
import sys

# Mock OpenAI Client
class MockClient:
    def __init__(self):
        self.chat = MagicMock()
        self.chat.completions = MagicMock()
        self.chat.completions.create = MagicMock(side_effect=self.mock_create)
        self.call_count = 0

    def mock_create(self, **kwargs):
        self.call_count += 1
        messages = kwargs.get('messages', [])
        prompt = messages[-1]['content']
        
        # Simulate Expert Phase
        if "Eres un matemático" in str(messages[0]['content']):
            return self._response("Expert Output: Logical Calculation")
        if "Eres un experto en pensamiento lateral" in str(messages[0]['content']):
            return self._response("Expert Output: Creative Leap")
        
        # Simulate RSA Phase
        if "Ciclo 1/2" in prompt:
             return self._response("[RSA Round 1 Result] Merged logic and creativity.")
        if "Ciclo 2/2" in prompt:
             return self._response("[RSA Round 2 Result] Final polished answer.")

        return self._response("Generic Output")

    def _response(self, content):
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = content
        return mock_resp

class TestRSA(unittest.TestCase):
    def test_rsa_flow(self):
        print("\n--- Testing RSA Flow ---")
        client = MockClient()
        agent = AgentReasoning()
        
        result = agent.solve_with_voting(
            problem="Test Problem",
            client=client,
            model_name="test-model",
            n_attempts=2 # Only 2 experts to keep it simple
        )
        
        print(f"Final Result: {result}")
        
        # We expect:
        # 2 calls for Experts (n_attempts=2)
        # 2 calls for RSA (rsa_rounds=2)
        # Total = 4 calls or more depending on retry logic (but here it's clean)
        self.assertTrue(client.call_count >= 4)
        self.assertIn("RSA Round 2", result)
        print("✅ RSA Logic Verified.")

if __name__ == "__main__":
    unittest.main()
